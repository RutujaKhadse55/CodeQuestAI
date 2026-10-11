"""Phase 4: hardcode detector, AST escape payloads, remote sandbox client + server (no Docker needed)."""
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from app import config
from app.engine import ast_policy, hardcode
from app.engine.sandbox import runner, server

FIX = Path(__file__).resolve().parents[4] / "fixtures" / "lc" / "two-sum"
EXAMPLES = [("nums = [2,7,11,15], target = 9", "[0,1]"), ("nums = [3,2,4], target = 6", "[1,2]"),
            ("nums = [3,3], target = 6", "[0,1]")]
HEAD = "class Solution:\n    def twoSum(self, nums, target):\n"


def body(s: str) -> str:
    return HEAD + "".join("        " + ln + "\n" for ln in s.strip("\n").splitlines())


# ------------------------------------------------------------------ hardcode detector
@pytest.mark.parametrize("src,reason", [
    ("return [0, 1]", "constant_return"),
    ("return []", "constant_return"),
    ("if nums == [2, 7, 11, 15]:\n    return [0, 1]\nreturn [1, 2]", "example_branch"),
    ("if nums == [3, 3] and target == 6:\n    return [0, 1]\nreturn [0, 0]", "example_branch"),
    ("table = {9: [0, 1], 6: [1, 2]}\nreturn table.get(target, [0, 0])", None),  # keys are not input values
    ("if len(nums) == 4:\n    return [0, 1]\nreturn [1, 2]", None),  # literal 4 is not an example input value
])
def test_hardcode_detection(src, reason):
    reasons = hardcode.detect(body(src), EXAMPLES)
    if reason:
        assert reason in reasons
    else:
        assert reasons == [] or reasons == ["example_output_table"]


def test_dict_keyed_by_example_inputs_is_flagged():
    src = 'table = {"[2,7,11,15]": [0, 1], 3: [1, 2]}\nreturn [0, 0]'
    ex = [("nums = [2,7,11,15], target = 9", "[0,1]")]
    assert "constant_return" in hardcode.detect(body(src), ex)
    d = 'answers = {9: [0, 1], 6: [1, 2]}\nreturn answers[target]'
    assert "example_output_table" in hardcode.detect(body(d), [("nums = [1], target = 9", "[0,1]"),
                                                               ("nums = [1], target = 6", "[1,2]")])


def test_legitimate_solutions_are_not_flagged():
    good = """
seen = {}
for i, n in enumerate(nums):
    if target - n in seen:
        return [seen[target - n], i]
    seen[n] = i
return []
"""
    assert hardcode.detect(body(good), EXAMPLES) == []
    boolean = "class Solution:\n    def containsDuplicate(self, nums):\n        for i in range(len(nums)):\n            if nums[i] in nums[:i]:\n                return True\n        return False\n"
    assert hardcode.detect(boolean, [("nums = [1,2,3,1]", "true")]) == []
    assert hardcode.detect("def (", EXAMPLES) == []  # syntax errors never raise


def test_labelled_two_sum_bugs_only_the_hardcoded_one_is_flagged():
    labels = json.loads((FIX / "buggy" / "labels.json").read_text(encoding="utf-8"))
    flagged = {f for f in labels if hardcode.detect((FIX / "buggy" / f).read_text(encoding="utf-8"), EXAMPLES)}
    assert flagged == {"bug_hardcoded_output_1.py"}


# ------------------------------------------------------------------ AST escape payloads (all must be rejected)
ESCAPES = {
    "generator_frame_chain": "class Solution:\n    def f(self, nums):\n        def g():\n            fr = gen.gi_frame\n            while fr:\n                fr = fr.f_back\n            yield 1\n        gen = g()\n        return next(gen)\n",
    "frame_globals": "class Solution:\n    def f(self, nums):\n        g = (i for i in nums)\n        return g.gi_frame.f_globals\n",
    "traceback_frame": "class Solution:\n    def f(self, nums):\n        try:\n            1 / 0\n        except Exception as e:\n            return e.__traceback__.tb_frame\n",
    "tb_next": "class Solution:\n    def f(self, nums):\n        try:\n            1 / 0\n        except Exception as e:\n            t = e\n        return t.tb_next\n",
    "format_gi_frame": "class Solution:\n    def f(self, nums):\n        return '{0.gi_frame}'.format((i for i in nums))\n",
    "format_index": "class Solution:\n    def f(self, nums):\n        return '{0[0]}'.format(nums)\n",
    "mro_walk": "class Solution:\n    def f(self, nums):\n        return int.mro()\n",
    "class_bases": "class Solution:\n    def f(self, nums):\n        return ().__class__.__bases__\n",
    "builtins_name": "class Solution:\n    def f(self, nums):\n        return __builtins__\n",
    "builtins_import": "from builtins import open\n",
    "importlib": "import importlib\n",
    "ctypes": "import ctypes\n",
    "_thread": "import _thread\n",
    "threading": "import threading\n",
    "io_module": "import io\n",
    "fullwidth_eval": "class Solution:\n    def f(self, nums):\n        return \uff45\uff56\uff41\uff4c('1')\n",  # NFKC-normalised by the parser to `eval`
    "alias_exec": "class Solution:\n    def f(self, nums):\n        run = exec\n        return run\n",
    "getattr_str": "class Solution:\n    def f(self, nums):\n        return getattr(nums, 'append')\n",
    "class_body_open": "class A:\n    x = open('/etc/passwd')\n",
    "lambda_default_vars": "f = lambda a=vars(): a\n",
    "decorator_eval": "@eval\ndef f(): pass\n",
}


@pytest.mark.parametrize("name", sorted(ESCAPES))
def test_escape_payload_rejected_by_policy(name):
    assert ast_policy.check(ESCAPES[name]), f"{name} was NOT rejected"


def test_benign_look_alikes_are_still_allowed():
    ok = "class Solution:\n    def f(self, nums):\n        s = 'items: {}, {:.2f}, {0}'.format(1, 2.5)\n        return [x * 2 for x in nums if x > 0], {'a': [1]}\n"
    assert ast_policy.check(ok) == []
    assert ast_policy.check("class A:\n    def __init__(self):\n        super().__init__()\n") == []
    assert ast_policy.check("x = '{\"a\": [1, 2]}'\n") == []  # JSON text is not a format traversal


# ------------------------------------------------------------------ remote sandbox: client + server
@pytest.fixture()
def sandbox_service(monkeypatch):
    """A real sandbox server on localhost whose native execution is stubbed (Windows has no rlimits)."""
    seen = {}

    def fake_native(payload, total):
        seen["payload"], seen["total"] = payload, total
        return json.dumps({"i": 0, "status": "ok", "value": 42}) + "\n"

    monkeypatch.setattr(runner, "_native", fake_native)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    monkeypatch.setattr(config, "SANDBOX_MODE", "remote")
    monkeypatch.setattr(config, "SANDBOX_URL", f"http://127.0.0.1:{httpd.server_address[1]}")
    monkeypatch.setattr(config, "SANDBOX_TOKEN", server.TOKEN)
    yield seen
    httpd.shutdown()


def test_remote_mode_round_trip(sandbox_service):
    lines = runner.run({"mode": "run", "code": "x", "tests": []}, 3.0)
    assert lines == [{"i": 0, "status": "ok", "value": 42}]
    assert sandbox_service["payload"]["mode"] == "run" and sandbox_service["total"] == 3.0


def test_remote_mode_rejects_bad_token_and_reports_unreachable(sandbox_service, monkeypatch):
    monkeypatch.setattr(config, "SANDBOX_TOKEN", "wrong")
    with pytest.raises(runner.SandboxUnavailable, match="401"):
        runner.run({"mode": "run"}, 1.0)
    monkeypatch.setattr(config, "SANDBOX_URL", "http://127.0.0.1:9")  # nothing listens
    with pytest.raises(runner.SandboxUnavailable, match="unreachable"):
        runner.run({"mode": "run"}, 1.0)


def test_server_validates_requests(sandbox_service, monkeypatch):
    import urllib.error
    import urllib.request

    def post(path, data, token=server.TOKEN):
        req = urllib.request.Request(config.SANDBOX_URL + path, data=data, method="POST",
                                     headers={"X-Sandbox-Token": token, "Content-Type": "application/json"})
        try:
            return urllib.request.urlopen(req, timeout=5).status
        except urllib.error.HTTPError as e:
            return e.code

    assert post("/run", b"not json") == 400
    assert post("/run", json.dumps({"payload": {}}).encode()) == 400  # missing total
    assert post("/run", b"", ) == 413  # empty body
    assert post("/nope", b"{}") == 404
    assert post("/run", json.dumps({"payload": {}, "total": 1}).encode(), token="x") == 401
    assert post("/run", json.dumps({"payload": {}, "total": 1}).encode()) == 200
    assert urllib.request.urlopen(config.SANDBOX_URL + "/health", timeout=5).status == 200


def test_server_caps_total_time(sandbox_service):
    import urllib.request
    req = urllib.request.Request(config.SANDBOX_URL + "/run", method="POST",
                                 data=json.dumps({"payload": {}, "total": 99999}).encode(),
                                 headers={"X-Sandbox-Token": server.TOKEN, "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5).read()
    assert sandbox_service["total"] == server.MAX_TOTAL_S
