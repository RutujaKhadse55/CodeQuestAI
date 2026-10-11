import json
from pathlib import Path

from conftest import H, needs_sandbox

FIX = Path(__file__).resolve().parents[3] / "fixtures" / "lc"


def _fixture(slug):
    return json.loads((FIX / slug / "problem.json").read_text(encoding="utf-8"))


GOOD_TWO_SUM = """class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
"""
BAD_TWO_SUM = GOOD_TWO_SUM.replace("return [seen[target - n], i]", "return [i, i]")


def _analyze(c, code, slug="two-sum", **extra):
    return c.post("/analyze", headers=H, json={"user_id": "u1", "problem_slug": slug, "code": code, **extra})


def test_capture_is_idempotent_and_flags_unsupported(real_client):
    p = _fixture("two-sum")
    a = real_client.post("/problems/capture", headers=H, json=p).json()
    assert a == {"problem_id": "two-sum", "slug": "two-sum", "supported": True, "reason": None}
    assert real_client.post("/problems/capture", headers=H, json=p).json() == a
    java = real_client.post("/problems/capture", headers=H, json={**p, "lang_selected": "java"}).json()
    assert java["supported"] is False and java["reason"] == "UNSUPPORTED_LANGUAGE"
    ll = {**p, "slug": "reverse-list", "starter_python": "class Solution:\n    def f(self, head: Optional[ListNode]) -> Optional[ListNode]:\n        "}
    assert real_client.post("/problems/capture", headers=H, json=ll).json()["supported"] is False


def test_capture_truncates_statement(real_client):
    from sqlmodel import Session
    from app import db
    from app.db.models_core import LCProblemRow
    p = {**_fixture("two-sum"), "statement_text": "x" * 9000}
    real_client.post("/problems/capture", headers=H, json=p)
    with Session(db.engine) as s:
        assert len(json.loads(s.get(LCProblemRow, "two-sum").payload_json)["statement_text"]) == 8000


def test_analyze_error_paths(real_client):
    r = _analyze(real_client, GOOD_TWO_SUM)
    assert r.status_code == 422 and r.json()["code"] == "UNSUPPORTED_PROBLEM"  # not captured
    real_client.post("/problems/capture", headers=H, json=_fixture("two-sum"))
    r = _analyze(real_client, GOOD_TWO_SUM, language="java")
    assert r.json()["code"] == "UNSUPPORTED_LANGUAGE"
    r = _analyze(real_client, "import os\nclass Solution:\n    def twoSum(self, nums, target):\n        return os.listdir('.')")
    assert r.status_code == 400 and r.json()["code"] == "CODE_REJECTED"
    assert r.json()["violations"][0]["rule"] == "import_not_allowed"
    assert _analyze(real_client, "x = 1").json()["code"] == "VALIDATION_ERROR"


@needs_sandbox
def test_analyze_good_and_bad_solution(real_client):
    real_client.post("/problems/capture", headers=H, json=_fixture("two-sum"))
    ok = _analyze(real_client, GOOD_TWO_SUM).json()
    assert [r["outcome"] for r in ok["results"]] == ["passed"] * 4 and ok["verified"] == "oracle-verified"
    assert ok["results"][-1]["kind"] == "fuzz" and ok["results"][-1]["input"] is None
    bad = _analyze(real_client, BAD_TWO_SUM, run_capture={"verdict": "Wrong Answer", "input": "nums = [1,5,9]\ntarget = 14",
                                                           "expected": "[1,2]", "output": "[0,0]"}).json()
    outcomes = {r["kind"]: r["outcome"] for r in bad["results"]}
    assert outcomes["run_capture"] == "wrong_output" and "wrong_output" in [r["outcome"] for r in bad["results"]]
    # hidden-test secrecy: nothing fuzz-shaped can appear in v0 responses
    assert all(r["input"] is None and r["expected"] is None and r["actual"] is None
               for r in bad["results"] if r["kind"] == "fuzz")


@needs_sandbox
def test_analyze_runtime_error_timeout_and_unordered(real_client):
    real_client.post("/problems/capture", headers=H, json=_fixture("two-sum"))
    err = _analyze(real_client, GOOD_TWO_SUM.replace("seen = {}", "seen = {}\n        1 / 0")).json()
    assert err["results"][0]["outcome"] == "runtime_error" and "ZeroDivisionError" in err["results"][0]["error"]
    slow = _analyze(real_client, GOOD_TWO_SUM.replace("seen = {}", "seen = {}\n        while True: pass")).json()
    assert slow["results"][0]["outcome"] == "timeout"
    swapped = GOOD_TWO_SUM.replace("[seen[target - n], i]", "[i, seen[target - n]]")
    assert all(r["outcome"] == "passed" for r in _analyze(real_client, swapped).json()["results"])  # "any order"


@needs_sandbox
def test_attacks_endpoint_all_blocked(real_client):
    body = real_client.get("/admin/attacks", headers=H).json()
    assert body["blocked"] == body["total"] >= 7, body


@needs_sandbox
def test_no_hidden_or_fuzz_data_in_any_response(real_client):
    """Exit criterion: responses carry only example/run_capture rows, never fuzz-kind data."""
    real_client.post("/problems/capture", headers=H, json=_fixture("two-sum"))
    for code in (GOOD_TWO_SUM, BAD_TWO_SUM):
        body = _analyze(real_client, code).json()
        for r in body["results"]:
            if r["kind"] == "fuzz":
                assert r["input"] is None and r["expected"] is None and r["actual"] is None
        assert "seed" not in json.dumps(body).lower()
    from sqlmodel import Session, select
    from app import db
    from app.db.models_core import TestResultRow
    with Session(db.engine) as s:
        for row in s.exec(select(TestResultRow).where(TestResultRow.kind == "fuzz")).all():
            assert row.input is None and row.expected is None and row.actual is None
