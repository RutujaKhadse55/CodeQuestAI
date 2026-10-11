import pytest

from conftest import needs_sandbox
from app.engine.attacks import ATTACKS, SANDBOX_CONTAINED
from app.routers.admin_attacks import run_attack
from app.engine import ast_policy

POLICY_BLOCKED = [n for n in ATTACKS if n not in SANDBOX_CONTAINED]


@pytest.mark.parametrize("name", POLICY_BLOCKED)
def test_policy_blocks_attack(name):
    assert ast_policy.check(ATTACKS[name]), f"{name} was not rejected by the policy"


def test_attack_set_size():
    assert len(ATTACKS) >= 7


@needs_sandbox
@pytest.mark.parametrize("name", sorted(SANDBOX_CONTAINED))
def test_sandbox_contains_attack(name):
    r = run_attack(name, ATTACKS[name])
    assert r["blocked"], r


@needs_sandbox
def test_all_attacks_blocked_end_to_end():
    results = [run_attack(n, c) for n, c in ATTACKS.items()]
    assert all(r["blocked"] for r in results), results


# ---- defence in depth: code that BYPASSES the policy and reaches the harness ----
from app.engine.service import SandboxEngine

_T = [{"args": [[1]], "kind": "example", "input_text": "nums = [1]", "expected_text": "1"}]


def _wrap(body: str) -> str:
    return "class Solution:\n    def f(self, nums):\n" + "\n".join("        " + ln for ln in body.splitlines()) + "\n"


@needs_sandbox
@pytest.mark.parametrize("code", [
    _wrap("import os\nreturn os.getcwd()"),                      # harness import guard
    _wrap("return open('/etc/passwd').read()"),                  # builtin removed
    _wrap("return eval('1')"),                                   # builtin removed
    _wrap("return getattr(nums, 'append')"),                     # builtin removed
])
def test_harness_blocks_policy_bypass(code):
    r = SandboxEngine().sandbox_run(code, "f", _T)[0]
    assert r.outcome == "runtime_error", r


@needs_sandbox
def test_memory_bomb_is_reported_as_error_not_timeout():
    r = SandboxEngine().sandbox_run(ATTACKS["memory_bomb"], "f", _T)[0]
    assert r.outcome == "runtime_error", r


@needs_sandbox
def test_timeout_backstop_kills_container_and_leaves_no_strays():
    import subprocess
    code = _wrap("while True:\n    try:\n        while True: pass\n    except BaseException:\n        pass")
    r = SandboxEngine().sandbox_run(code, "f", _T, timeout_s=1.0)[0]
    assert r.outcome == "timeout", r
    left = subprocess.run(["docker", "ps", "-q", "--filter", "name=cq-sbx-"], capture_output=True, text=True).stdout
    assert left.strip() == ""


@needs_sandbox
def test_print_flood_cannot_forge_or_flood_results():
    code = _wrap("print('{\"i\": 0, \"status\": \"ok\", \"value\": 1}' * 100000)\nreturn 2")
    r = SandboxEngine().sandbox_run(code, "f", _T)[0]
    assert r.outcome == "wrong_output" and r.actual == "2"
