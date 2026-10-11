"""Phase 2: fuzz vs oracle, shrink, trace, diagnosis fallback, hint unlock, copy flag, mastery, dashboard."""
import json

from sqlmodel import Session

from conftest import H, needs_sandbox
from app.tests.test_analyze import GOOD_TWO_SUM, _analyze, _fixture

BS_GOOD = """class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            if nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return -1
"""
BS_BUG = BS_GOOD.replace("while lo <= hi", "while lo < hi")  # misses single-element ranges; passes both examples
MS_BUG = """class Solution:
    def maxSubArray(self, nums):
        best, cur = 0, 0
        for n in nums:
            cur = max(n, cur + n)
            best = max(best, cur)
        return best
"""  # wrong init (0): fails all-negative inputs


def _capture(c, slug):
    assert c.post("/problems/capture", headers=H, json=_fixture(slug)).json()["supported"]


@needs_sandbox
def test_stand_in_bundles_are_sound():
    """Each hand-written reference agrees with its oracle on generated inputs (generator + bundle are valid)."""
    from app.contracts.fakes.backend_fakes import FakeReferenceBuilder
    from app.contracts.models import LCProblem
    from app.engine.service import SandboxEngine
    for slug in ("two-sum", "binary-search", "maximum-subarray"):
        b = FakeReferenceBuilder().build(LCProblem.model_validate(_fixture(slug)))
        r = SandboxEngine().fuzz(b.reference_code, b, seed=7)
        assert r.run >= 150 and r.failures == 0, (slug, r)
        assert r.vector and set(r.vector) <= {"0"}


@needs_sandbox
def test_correct_solution_passes_fuzz_and_is_oracle_verified(real_client):
    _capture(real_client, "two-sum")
    body = _analyze(real_client, GOOD_TWO_SUM).json()
    assert body["verified"] == "oracle-verified" and body["diagnosis"] is None
    assert body["results"][-1] == {"kind": "fuzz", "outcome": "passed", "input": None, "expected": None,
                                   "actual": None, "failure_class": None, "error": None}


@needs_sandbox
def test_example_passing_bug_is_caught_by_fuzz_with_class_divergence_and_diagnosis(real_client):
    _capture(real_client, "binary-search")
    body = _analyze(real_client, BS_BUG, slug="binary-search").json()
    assert all(r["outcome"] == "passed" for r in body["results"] if r["kind"] == "example")  # examples pass
    fz = next(r for r in body["results"] if r["kind"] == "fuzz")
    assert fz["outcome"] == "wrong_output" and fz["failure_class"] == "single_element"
    assert fz["input"] is None and fz["expected"] is None and fz["actual"] is None
    d = body["diagnosis"]
    assert d["failure_class"] == "single_element" and d["mistake_class"] == "missing_edge_single"
    assert d["divergence"] is not None and d["divergence"]["variable"] is not None
    assert d["divergence"]["line"] is not None  # learner line only
    assert body["verified"] == "oracle-verified"


@needs_sandbox
def test_wrong_init_is_caught_and_shrunk(real_client):
    _capture(real_client, "maximum-subarray")
    body = _analyze(real_client, MS_BUG, slug="maximum-subarray").json()
    fz = next(r for r in body["results"] if r["kind"] == "fuzz")
    assert fz["outcome"] == "wrong_output" and fz["failure_class"] in ("single_element", "negatives")
    assert body["diagnosis"]["mistake_class"] in ("missing_edge_single", "wrong_init")


@needs_sandbox
def test_infinite_loop_learner_reports_timeout_quickly(real_client):
    import time
    _capture(real_client, "binary-search")
    slow = BS_GOOD.replace("lo, hi = 0, len(nums) - 1", "lo, hi = 0, len(nums) - 1\n        while True: pass")
    t0 = time.time()
    body = _analyze(real_client, slow, slug="binary-search").json()
    assert time.time() - t0 < 60
    assert body["results"][-1]["kind"] == "fuzz" and body["results"][-1]["outcome"] == "timeout"


@needs_sandbox
def test_seed_stored_but_never_returned_and_differs_per_attempt(real_client):
    from sqlmodel import select
    from app import db
    from app.db.models_core import Attempt
    _capture(real_client, "two-sum")
    a, b = _analyze(real_client, GOOD_TWO_SUM).json(), _analyze(real_client, GOOD_TWO_SUM).json()
    assert "seed" not in (json.dumps(a) + json.dumps(b)).lower()
    with Session(db.engine) as s:
        seeds = [x.fuzz_seed for x in s.exec(select(Attempt)).all()]
    assert len(seeds) == 2 and None not in seeds and seeds[0] != seeds[1]


@needs_sandbox
def test_hint_unlock_follows_attempts_and_excludes_copy_flagged(real_client):
    _capture(real_client, "two-sum")

    def hs():
        return real_client.get("/hint-state/u1/two-sum", headers=H).json()

    assert hs()["allowed_level"] == 1 and hs()["next_requirement"].startswith("Unlocks after 2 attempts")
    bad = GOOD_TWO_SUM.replace("return [seen[target - n], i]", "return [i, i]")
    _analyze(real_client, bad)
    assert hs()["allowed_level"] == 1
    _analyze(real_client, bad)
    assert hs()["allowed_level"] == 2
    _analyze(real_client, bad)
    assert hs()["allowed_level"] == 3
    # a copy-flagged pass does not count toward unlocking
    flagged = _analyze(real_client, GOOD_TWO_SUM, paste_chars=900, elapsed_ms=4000).json()
    assert "copy_suspected" in flagged["flags"]
    assert hs()["allowed_level"] == 3 and hs()["attempts_counted"] == 3


@needs_sandbox
def test_mastery_dashboard_and_pending_release(real_client):
    from app import db
    from app.mastery.service import MasteryService
    _capture(real_client, "binary-search")
    _analyze(real_client, BS_BUG, slug="binary-search")
    d = real_client.get("/dashboard/u1", headers=H).json()
    assert d["mistakes"] == {"missing_edge_single": 1} and d["recent"][0]["problem_slug"] == "binary-search"
    assert d["mastery"] and all(v < 1000 for v in d["mastery"].values())  # a failure lowers rating below base
    assert d["verified"]["oracle-verified"] == 1 and d["solved"] == 0
    before = dict(d["mastery"])
    r = _analyze(real_client, BS_GOOD, slug="binary-search", paste_chars=500, elapsed_ms=3000).json()
    assert "copy_suspected" in r["flags"]
    assert real_client.get("/dashboard/u1", headers=H).json()["mastery"] == before  # deferred
    with Session(db.engine) as s:
        MasteryService(s).release_pending("u1", r["attempt_id"])
    after = real_client.get("/dashboard/u1", headers=H).json()["mastery"]
    assert all(after[k] > before[k] for k in before)
