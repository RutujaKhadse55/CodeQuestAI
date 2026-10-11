"""Phase 4 bug bash: sandbox / fuzz edge cases. Needs Docker (conftest.needs_sandbox)."""
import subprocess
import time

import pytest

from conftest import H, needs_sandbox
from app.contracts.models import ReferenceBundle
from app.engine.service import SandboxEngine
from app.tests.test_analyze import GOOD_TWO_SUM, _analyze, _fixture

pytestmark = needs_sandbox
E = SandboxEngine()


def run(body: str, args=None, expected="0", n=1, timeout_s=2.0, kind="example"):
    code = "class Solution:\n    def f(self, nums):\n" + "\n".join("        " + ln for ln in body.splitlines()) + "\n"
    tests = [{"args": args if args is not None else [[1, 2, 3]], "kind": kind, "input_text": "nums = [1,2,3]",
              "expected_text": expected} for _ in range(n)]
    return E.sandbox_run(code, "f", tests, timeout_s=timeout_s)


def test_huge_output_is_reported_not_crashed():
    r = run("return list(range(100000))")[0]
    assert r.outcome == "runtime_error" and "OutputTooLarge" in r.error


def test_infinite_recursion_is_a_runtime_error():
    r = run("def g(n):\n    return g(n + 1)\nreturn g(0)")[0]
    assert r.outcome == "runtime_error" and "RecursionError" in r.error


def test_deep_but_legal_recursion_works():
    r = run("def g(n):\n    return 0 if n == 0 else 1 + g(n - 1)\nreturn g(400)", expected="400")[0]
    assert r.outcome == "passed"


def test_non_json_return_values_do_not_crash():
    assert run("return {1, 2, 3}")[0].outcome == "wrong_output"          # set -> repr string
    assert run("return float('nan')")[0].outcome == "wrong_output"
    assert run("return float('inf')")[0].outcome == "wrong_output"
    assert run("return None", expected="null")[0].outcome == "passed"
    assert run("return (1, 2)", expected="[1,2]")[0].outcome == "passed"   # tuple == list after canonicalisation


def test_huge_int_exceeds_conversion_limit_gracefully():
    r = run("return 10 ** 5000")[0]
    assert r.outcome in ("runtime_error", "wrong_output") and r.outcome != "passed"


def test_print_flood_then_correct_answer_still_passes():
    assert run("print('x' * 5_000_000)\nreturn 0")[0].outcome == "passed"


def test_unicode_in_inputs_and_outputs():
    code = "class Solution:\n    def f(self, s):\n        return s[::-1]\n"
    t = [{"args": ["héllo 世界 \U0001F600"], "kind": "example", "input_text": "s", "expected_text": '"\U0001F600 界世 olléh"'}]
    assert E.sandbox_run(code, "f", t)[0].outcome == "passed"


def test_many_small_tests_and_a_few_large_inputs():
    t0 = time.time()
    assert all(r.outcome == "passed" for r in run("return len(nums)", args=[[1, 2, 3]], expected="3", n=60))
    big = run("return len(nums)", args=[list(range(100_000))], expected="100000", n=4)  # LeetCode-sized inputs
    assert all(r.outcome == "passed" for r in big) and time.time() - t0 < 30


def test_each_test_gets_its_own_input_copy():
    code = "class Solution:\n    def f(self, nums):\n        nums.append(9)\n        return len(nums)\n"
    t = [{"args": [[1, 2]], "kind": "example", "input_text": "x", "expected_text": "3"}] * 3
    assert [r.outcome for r in E.sandbox_run(code, "f", t)] == ["passed"] * 3


def test_load_failures_are_per_test_errors_not_exceptions():
    cases = ["class Solution:\n    def other(self, nums):\n        return 0\n",      # entry point missing
             "class Solution:\n    def __init__(self, x):\n        pass\n    def f(self, nums):\n        return 0\n",
             "class Solution:\n    def f(self, nums):\n        return 0\n    x = undefined_name\n"]
    for code in cases:
        r = E.sandbox_run(code, "f", [{"args": [[1]], "kind": "example", "input_text": "x", "expected_text": "0"}])[0]
        assert r.outcome == "runtime_error" and r.error, code


def test_timeout_budget_many_slow_tests_stays_bounded():
    t0 = time.time()
    rs = run("while True: pass", n=4, timeout_s=0.5)
    assert [r.outcome for r in rs] == ["timeout"] * 4 and time.time() - t0 < 25


def test_slow_but_legal_code_passes_under_the_limit():
    assert run("return sum(range(3_000_000)) * 0")[0].outcome == "passed"


def test_no_stray_sandbox_containers_left():
    out = subprocess.run(["docker", "ps", "-aq", "--filter", "name=cq-sbx-"], capture_output=True, text=True).stdout
    assert out.strip() == ""


# ---------------------------------------------------------------- fuzz edge cases
def _bundle(gen: str, oracle="class Solution:\n    def f(self, nums):\n        return len(nums)\n", **kw):
    return ReferenceBundle(oracle_code=oracle, reference_code=oracle, gen_inputs_code=gen,
                           comparator="exact", constraints={}, verified=True, **kw)


LEARNER = "class Solution:\n    def f(self, nums):\n        return len(nums)\n"


def test_fuzz_with_broken_generator_is_not_reported_as_a_pass():
    r = E.fuzz(LEARNER, _bundle("def gen_inputs(rng):\n    return 5\n"), seed=1)  # not a list of args
    assert r.run == 0 and not r.passed and "generator_produced_no_valid_inputs" in r.flags
    r = E.fuzz(LEARNER, _bundle("def gen_inputs(rng):\n    raise ValueError('x')\n"), seed=1)
    assert r.run == 0 and not r.passed


def test_fuzz_with_oracle_that_always_raises_is_unverifiable():
    bad = "class Solution:\n    def f(self, nums):\n        raise RuntimeError('oracle bug')\n"
    r = E.fuzz(LEARNER, _bundle("def gen_inputs(rng):\n    return [[1, 2]]\n", oracle=bad), seed=1)
    assert r.run == 0 and not r.passed


def test_fuzz_learner_crash_is_a_runtime_error_failure():
    crash = "class Solution:\n    def f(self, nums):\n        return nums[len(nums)]\n"
    r = E.fuzz(crash, _bundle("def gen_inputs(rng):\n    return [[1, 2, 3]]\n"), seed=1)
    assert r.failures > 0 and r.first_kind == "runtime_error"


def test_fuzz_result_carries_no_input_data():
    """Hidden-test secrecy: the fuzz summary has counts, a class, a 0/1 vector and a divergence - never inputs."""
    r = E.fuzz("class Solution:\n    def f(self, nums):\n        return 1\n",
               _bundle("def gen_inputs(rng):\n    return [[rng.randint(1, 9) for _ in range(3)]]\n"), seed=3)
    assert r.failures > 0
    assert set(vars(r)) == {"seed", "run", "failures", "first_kind", "failure_class", "divergence", "vector", "flags"}
    assert set(r.vector) <= {"0", "1"}


def test_fuzz_learner_that_mutates_its_input_does_not_corrupt_the_oracle():
    mutating = "class Solution:\n    def f(self, nums):\n        n = len(nums)\n        nums.clear()\n        return n\n"
    r = E.fuzz(mutating, _bundle("def gen_inputs(rng):\n    return [[1, 2, 3]]\n"), seed=1)
    assert r.passed


# ---------------------------------------------------------------- API level
def test_syntax_error_is_a_normal_result_with_the_message(real_client):
    real_client.post("/problems/capture", headers=H, json=_fixture("two-sum"))
    body = _analyze(real_client, "class Solution:\n    def twoSum(self, nums, target)\n        return [0, 1]\n").json()
    assert body["flags"].count("syntax_error") == 1
    assert body["results"][0]["outcome"] == "runtime_error" and "SyntaxError" in body["results"][0]["error"]
    assert body["diagnosis"] is not None


def test_hardcoded_solution_is_flagged_and_diagnosed(real_client):
    real_client.post("/problems/capture", headers=H, json=_fixture("two-sum"))
    code = "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]\n"
    body = _analyze(real_client, code).json()
    assert "hardcode_suspected" in body["flags"]
    assert body["diagnosis"]["mistake_class"] == "hardcoded_output" and body["diagnosis"]["confidence"] >= 0.9
    assert "hardcode_suspected" not in _analyze(real_client, GOOD_TWO_SUM).json()["flags"]


def test_hardcode_hook_can_be_replaced_and_a_broken_detector_never_fails_analysis(real_client):
    from app import providers
    real_client.post("/problems/capture", headers=H, json=_fixture("two-sum"))
    try:
        providers.register_hardcode(lambda code, ex: 1 / 0)
        assert _analyze(real_client, GOOD_TWO_SUM).status_code == 200
        providers.register_hardcode(lambda code, ex: ["ai_detector_says_so"])
        assert "hardcode_suspected" in _analyze(real_client, GOOD_TWO_SUM).json()["flags"]
    finally:
        providers._hardcode = None
