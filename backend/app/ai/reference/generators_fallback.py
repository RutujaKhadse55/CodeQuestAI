"""Hand-written, hand-verified reference bundles for the demo problems.

Convention (same as contracts/fakes/backend_fakes.py): oracle_code / reference_code define `class Solution` with the
LeetCode method name and parameter names; gen_inputs_code defines `def gen_inputs(rng)` returning the list of call
arguments, using only the passed `rng`. Only sandbox-allowed imports (none are needed here).
The first three demo problems are reused from the Backend fake module (not edited).
"""
from __future__ import annotations

from ...contracts.fakes.backend_fakes import _BINARY_SEARCH, _MAX_SUBARRAY, _TWO_SUM

_CONTAINS_DUPLICATE = dict(
    oracle_code="""
class Solution:
    def containsDuplicate(self, nums):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] == nums[j]:
                    return True
        return False
""",
    reference_code="""
class Solution:
    def containsDuplicate(self, nums):
        seen = set()
        for n in nums:
            if n in seen:
                return True
            seen.add(n)
        return False
""",
    gen_inputs_code="""
def gen_inputs(rng):
    n = rng.randint(1, 10)
    if rng.random() < 0.5:
        return [rng.sample(range(-20, 21), n)]
    return [[rng.randint(-5, 5) for _ in range(n)]]
""",
    comparator="exact",
    constraints={"nums.length": "1..10 (fuzz)"},
)

_VALID_ANAGRAM = dict(
    oracle_code="""
class Solution:
    def isAnagram(self, s, t):
        if len(s) != len(t):
            return False
        rest = list(t)
        for ch in s:
            if ch in rest:
                rest.remove(ch)
            else:
                return False
        return not rest
""",
    reference_code="""
class Solution:
    def isAnagram(self, s, t):
        if len(s) != len(t):
            return False
        counts = {}
        for ch in s:
            counts[ch] = counts.get(ch, 0) + 1
        for ch in t:
            if counts.get(ch, 0) == 0:
                return False
            counts[ch] -= 1
        return True
""",
    gen_inputs_code="""
def gen_inputs(rng):
    letters = "abcd"
    n = rng.randint(1, 8)
    s = "".join(rng.choice(letters) for _ in range(n))
    r = rng.random()
    if r < 0.45:
        chars = list(s)
        rng.shuffle(chars)
        t = "".join(chars)
    elif r < 0.7:
        t = "".join(rng.choice(letters) for _ in range(n))
    elif r < 0.85:
        t = "".join(rng.choice(letters) for _ in range(rng.randint(1, 8)))
    else:
        chars = list(s)
        rng.shuffle(chars)
        chars[rng.randrange(n)] = rng.choice(letters)
        t = "".join(chars)
    return [s, t]
""",
    comparator="exact",
    constraints={"s.length": "1..8 (fuzz)", "charset": "a-d (fuzz)"},
)

_BEST_TIME_STOCK = dict(
    oracle_code="""
class Solution:
    def maxProfit(self, prices):
        best = 0
        for i in range(len(prices)):
            for j in range(i + 1, len(prices)):
                if prices[j] - prices[i] > best:
                    best = prices[j] - prices[i]
        return best
""",
    reference_code="""
class Solution:
    def maxProfit(self, prices):
        low = prices[0]
        best = 0
        for p in prices[1:]:
            if p < low:
                low = p
            elif p - low > best:
                best = p - low
        return best
""",
    gen_inputs_code="""
def gen_inputs(rng):
    n = rng.randint(1, 10)
    r = rng.random()
    if r < 0.2:
        return [sorted((rng.randint(0, 30) for _ in range(n)), reverse=True)]
    if r < 0.35:
        return [sorted(rng.randint(0, 30) for _ in range(n))]
    return [[rng.randint(0, 30) for _ in range(n)]]
""",
    comparator="exact",
    constraints={"prices.length": "1..10 (fuzz)", "prices[i]": "0..30 (fuzz)"},
)

_CLIMBING_STAIRS = dict(
    oracle_code="""
class Solution:
    def climbStairs(self, n):
        if n <= 1:
            return 1
        return self.climbStairs(n - 1) + self.climbStairs(n - 2)
""",
    reference_code="""
class Solution:
    def climbStairs(self, n):
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b
""",
    gen_inputs_code="""
def gen_inputs(rng):
    return [rng.randint(1, 18)]
""",
    comparator="exact",
    constraints={"n": "1..18 (fuzz; the oracle is exponential)"},
)

_MISSING_NUMBER = dict(
    oracle_code="""
class Solution:
    def missingNumber(self, nums):
        for k in range(len(nums) + 1):
            if k not in nums:
                return k
        return -1
""",
    reference_code="""
class Solution:
    def missingNumber(self, nums):
        n = len(nums)
        return n * (n + 1) // 2 - sum(nums)
""",
    gen_inputs_code="""
def gen_inputs(rng):
    n = rng.randint(1, 10)
    nums = list(range(n + 1))
    nums.remove(rng.randint(0, n))
    rng.shuffle(nums)
    return [nums]
""",
    comparator="exact",
    constraints={"nums": "distinct values in 0..n, exactly one missing", "nums.length": "1..10 (fuzz)"},
)

CURATED: dict[str, dict] = {
    "two-sum": _TWO_SUM,
    "binary-search": _BINARY_SEARCH,
    "maximum-subarray": _MAX_SUBARRAY,
    "contains-duplicate": _CONTAINS_DUPLICATE,
    "valid-anagram": _VALID_ANAGRAM,
    "best-time-to-buy-and-sell-stock": _BEST_TIME_STOCK,
    "climbing-stairs": _CLIMBING_STAIRS,
    "missing-number": _MISSING_NUMBER,
}
