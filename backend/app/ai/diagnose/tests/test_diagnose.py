import random
import sys
from types import SimpleNamespace

import pytest
from conftest import needs_sandbox

from app import providers
from app.ai.diagnose import AIDiagnoser, register, remember_bundle
from app.ai.diagnose.hardcode import detect
from app.ai.diagnose.mutants.fingerprint import Fingerprint, FingerprintStore
from app.ai.diagnose.mutants.matcher import hamming_similarity, match
from app.ai.diagnose.mutants.operators import generate_mutants
from app.contracts.fakes.backend_fakes import FakeReferenceBuilder
from app.contracts.models import LCProblem
from app.engine.service import FINGERPRINT_N, FINGERPRINT_SEED, SandboxEngine

N = FINGERPRINT_N


def bundle(slug):
    return FakeReferenceBuilder().build(LCProblem.model_construct(slug=slug))


class _Budget(Exception):
    pass


def _limited(fn, *args, steps=20000):
    """Call fn with a line budget so mutants with infinite loops fail instead of hanging."""
    left = [steps]

    def tracer(frame, event, arg):
        left[0] -= 1
        if left[0] < 0:
            raise _Budget
        return tracer

    sys.settrace(tracer)
    try:
        return fn(*args)
    finally:
        sys.settrace(None)


class LocalEngine:
    """In-process stand-in for SandboxEngine.fuzz (tests only; the code under test is our own fixtures)."""

    @staticmethod
    def _solution(code, name_hint=None):
        ns: dict = {}
        exec(code, {"List": list}, ns)  # noqa: S102
        return ns["Solution"]()

    def fuzz(self, code, b, seed, n=200):
        gen_ns: dict = {}
        exec(b.gen_inputs_code, {}, gen_ns)  # noqa: S102
        oracle = self._solution(b.oracle_code)
        try:
            cand = self._solution(code)
        except Exception:  # noqa: BLE001
            return SimpleNamespace(vector="1" * N)
        rng = random.Random(seed)
        bits = []
        for _ in range(N):
            args = gen_ns["gen_inputs"](rng)
            m = [x for x in dir(oracle) if not x.startswith("_")][0]
            exp = getattr(oracle, m)(*[list(a) if isinstance(a, list) else a for a in args])
            try:
                got = _limited(getattr(cand, m), *[list(a) if isinstance(a, list) else a for a in args])
                ok = sorted(got) == sorted(exp) if b.comparator == "unordered" else got == exp
            except Exception:  # noqa: BLE001
                ok = False
            bits.append("0" if ok else "1")
        return SimpleNamespace(vector="".join(bits))


@pytest.fixture()
def store():
    return FingerprintStore(engine=LocalEngine())


# ---------------------------------------------------------------- operators
def test_operators_produce_valid_distinct_classes():
    ms = generate_mutants(bundle("binary-search").reference_code)
    classes = {c for c, _ in ms}
    assert {"off_by_one_bound", "wrong_comparison", "wrong_operator"} <= classes
    assert len({s for _, s in ms}) == len(ms)
    for _, src in ms:
        compile(src, "<m>", "exec")
        assert src != generate_mutants.__doc__
    assert generate_mutants("def (") == []


def test_max_subarray_has_wrong_init_mutant():
    ms = generate_mutants(bundle("maximum-subarray").reference_code)
    assert any(c == "wrong_init" and "best = 0" in s.replace("cur = best = 0", "best = 0") for c, s in ms)


# ---------------------------------------------------------------- matcher
def test_matcher_thresholds():
    fps = [Fingerprint("wrong_init", "0011" * 16, ""), Fingerprint("off_by_one_bound", "1100" * 16, "")]
    assert hamming_similarity("0011", "0010") == 0.75
    m = match("0011" * 16, fps)
    assert (m.mistake_class, m.confidence) == ("wrong_init", 1.0)
    near = "0011" * 15 + "0001"  # 63/64 similar
    assert match(near, fps).mistake_class == "wrong_init"
    far = "1111" * 16
    m = match(far, fps)
    assert m.mistake_class is None and m.confidence < 0.5
    assert match("0" * 64, fps).mistake_class is None and match("", fps).mistake_class is None


# ---------------------------------------------------------------- fingerprint + diagnoser (in-process engine)
MAX_SUB_BUGGY = """
class Solution:
    def maxSubArray(self, nums):
        cur = best = 0
        for n in nums[1:]:
            cur = max(n, cur + n)
            best = max(best, cur)
        return best
"""
BINARY_OFF_BY_ONE = """
class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            if nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return -1
"""
def test_fingerprints_cached_and_nonempty(store):
    b = bundle("binary-search")
    fps = store.get("binary-search", b)
    assert fps and all("1" in f.vector and len(f.vector) == N for f in fps)
    assert store.get("binary-search", b) is fps  # cached per (slug, hash)


def _diagnose(store, slug, code):
    b = bundle(slug)
    remember_bundle(slug, b)
    vec = LocalEngine().fuzz(code, b, FINGERPRINT_SEED, N).vector
    return AIDiagnoser(store).diagnose(vec, slug, None)


def test_binary_search_off_by_one_matched(store):
    d = _diagnose(store, "binary-search", BINARY_OFF_BY_ONE)
    assert d.mistake_class == "off_by_one_bound" and d.confidence >= 0.8


def test_max_subarray_wrong_init_matched(store):
    d = _diagnose(store, "maximum-subarray", MAX_SUB_BUGGY.replace("nums[1:]", "nums"))
    assert d.mistake_class == "wrong_init" and d.confidence >= 0.8


def test_unknown_bug_is_no_known_pattern(store):
    b = bundle("maximum-subarray")
    remember_bundle("maximum-subarray", b)
    d = AIDiagnoser(store).diagnose("01" * (N // 2), "maximum-subarray", None)  # fails on no mutant's pattern
    assert d.mistake_class is None and d.confidence < 0.8


def test_passing_or_missing_bundle_degrades_gracefully(store):
    assert AIDiagnoser(store).diagnose("0" * N, "binary-search", None).mistake_class is None
    assert AIDiagnoser(store).diagnose("1" * N, "no-such-slug", None).mistake_class is None


def test_register_wires_providers(monkeypatch):
    monkeypatch.setattr(providers, "_diagnoser", None)
    monkeypatch.setattr(providers, "_hardcode", None)
    d = register()
    assert providers.diagnoser() is d and providers.hardcode_detector() is detect


# ---------------------------------------------------------------- sandbox-backed
@needs_sandbox
def test_real_sandbox_binary_search_matches_off_by_one():
    b = bundle("binary-search")
    st = FingerprintStore(engine=SandboxEngine())
    remember_bundle("binary-search", b)
    eng = SandboxEngine()
    vec = eng.fuzz(BINARY_OFF_BY_ONE, b, 1, 10).vector
    d = AIDiagnoser(st).diagnose(vec, "binary-search", None)
    assert d.mistake_class == "off_by_one_bound"


# ---------------------------------------------------------------- hardcode
TWO = [("nums = [2,7,11,15], target = 9", "[0,1]"), ("nums = [3,2,4], target = 6", "[1,2]"),
       ("nums = [3,3], target = 6", "[0,1]")]
HEAD = "class Solution:\n    def twoSum(self, nums, target):\n"


def body(s):
    return HEAD + "".join("        " + ln + "\n" for ln in s.strip("\n").splitlines())


@pytest.mark.parametrize("src,reason", [
    ("if target == 9:\n    return [0, 1]\nif target == 6:\n    return [1, 2]\nreturn []", "example_if_chain"),
    ('t = {"[2,7,11,15]": [0, 1], "[3,2,4]": [1, 2]}\nreturn t.get(str(nums), [])', "example_lookup_table"),
    ("t = {(2, 7, 11, 15, 9): 1, (3, 2, 4, 6): 2}\nreturn t[(*nums, target)]", None),
    ("if sum(nums) == 35:\n    return [0, 1]\nreturn [0, 0]", "len_sum_check"),
    ("if len(nums) == 4:\n    return [0, 1]\nif len(nums) == 3:\n    return [1, 2]\nreturn [0, 1]", "len_sum_check"),
    ("if nums == [3, 3] and target == 6:\n    return [0, 1]\nreturn [0, 0]", "example_branch"),
    ("return [0, 1]", "constant_return"),
])
def test_hardcode_flagged(src, reason):
    reasons = detect(body(src), TWO)
    assert isinstance(reasons, list) and all(isinstance(r, str) for r in reasons)
    if reason:
        assert reason in reasons


def test_hardcode_clean_code_not_flagged():
    good = "seen = {}\nfor i, n in enumerate(nums):\n    if target - n in seen:\n        return [seen[target - n], i]\n    seen[n] = i\nreturn []"
    assert detect(body(good), TWO) == []
    fib = "class Solution:\n    def fib(self, n):\n        if n == 0:\n            return 0\n        if n == 1:\n            return 1\n        return self.fib(n - 1) + self.fib(n - 2)\n"
    assert detect(fib, [("n = 1", "1"), ("n = 0", "0")]) == []
    assert detect("def (", TWO) == []
