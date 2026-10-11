"""[BE] Stand-ins so the Backend pipeline runs before AI's real implementations are merged.

FakeReferenceBuilder: hand-written, hand-verified bundles for the 3 demo fixtures (two-sum, binary-search,
maximum-subarray). Convention for every bundle (AI's real builder must follow it):
  - oracle_code / reference_code define `class Solution` with the SAME method name and parameter names as the
    LeetCode starter (or a plain function of that name);
  - gen_inputs_code defines `def gen_inputs(rng)` returning the LIST OF CALL ARGUMENTS, using only the passed
    `rng` (a random.Random) — no imports needed.
FakeDiagnoser: returns only the divergence (AI's Diagnoser adds fingerprint matching).
"""
from ..models import Diagnosis, Divergence, LCProblem, ReferenceBundle

_TWO_SUM = dict(
    oracle_code="""
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []
""",
    reference_code="""
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            need = target - n
            if need in seen:
                return [seen[need], i]
            seen[n] = i
        return []
""",
    gen_inputs_code="""
def gen_inputs(rng):
    for _ in range(50):
        n = rng.randint(2, 8)
        nums = [rng.randint(-20, 20) for _ in range(n)]
        i, j = rng.sample(range(n), 2)
        target = nums[i] + nums[j]
        pairs = sum(1 for a in range(n) for b in range(a + 1, n) if nums[a] + nums[b] == target)
        if pairs == 1:
            return [nums, target]
    return [[3, 3], 6]
""",
    comparator="unordered",
    constraints={"nums.length": "2..8 (fuzz)", "exactly_one_solution": True},
)

_BINARY_SEARCH = dict(
    oracle_code="""
class Solution:
    def search(self, nums, target):
        for i in range(len(nums)):
            if nums[i] == target:
                return i
        return -1
""",
    reference_code="""
class Solution:
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
""",
    gen_inputs_code="""
def gen_inputs(rng):
    n = rng.randint(1, 12)
    nums = sorted(rng.sample(range(-20, 21), n))
    target = rng.choice(nums) if rng.random() < 0.5 else rng.randint(-25, 25)
    return [nums, target]
""",
    comparator="exact",
    constraints={"sorted": True, "unique": True},
)

_MAX_SUBARRAY = dict(
    oracle_code="""
class Solution:
    def maxSubArray(self, nums):
        best = nums[0]
        for i in range(len(nums)):
            total = 0
            for j in range(i, len(nums)):
                total += nums[j]
                if total > best:
                    best = total
        return best
""",
    reference_code="""
class Solution:
    def maxSubArray(self, nums):
        cur = best = nums[0]
        for n in nums[1:]:
            cur = max(n, cur + n)
            best = max(best, cur)
        return best
""",
    gen_inputs_code="""
def gen_inputs(rng):
    n = rng.randint(1, 10)
    if rng.random() < 0.2:
        return [[rng.randint(-10, -1) for _ in range(n)]]
    return [[rng.randint(-10, 10) for _ in range(n)]]
""",
    comparator="exact",
    constraints={"nums.length": "1..10 (fuzz)"},
)

_BUNDLES = {"two-sum": _TWO_SUM, "binary-search": _BINARY_SEARCH, "maximum-subarray": _MAX_SUBARRAY}


class FakeReferenceBuilder:
    def build(self, problem: LCProblem) -> ReferenceBundle:
        spec = _BUNDLES.get(problem.slug)
        if spec is None:  # unknown problem: nothing to fuzz against => explanation-only
            return ReferenceBundle(oracle_code="", reference_code="", gen_inputs_code="", comparator="exact",
                                   constraints={}, verified=False, notes="no hand-written bundle for this problem")
        return ReferenceBundle(verified=True, notes="hand-written stand-in (FakeReferenceBuilder)", **spec)


class FakeDiagnoser:
    """No fingerprint matcher yet: report only the divergence. Backend's rule fallback fills mistake_class."""

    def diagnose(self, fuzz_vector: str, problem_slug: str, divergence: Divergence | None) -> Diagnosis:
        return Diagnosis(mistake_class=None, confidence=0.0, divergence=divergence)
