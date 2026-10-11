import json

import pytest
from conftest import needs_sandbox

from app import config, providers
from app.ai import reference
from app.ai.reference.synth import AIReferenceBuilder
from app.ai.reference.validate import validate
from app.contracts.models import Example, LCProblem

# slug -> (starter, [(input_text, output_text)])
DEMO = {
    "two-sum": ("class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass",
                [("nums = [2,7,11,15], target = 9", "[0,1]"), ("nums = [3,2,4], target = 6", "[1,2]")]),
    "binary-search": ("class Solution:\n    def search(self, nums: List[int], target: int) -> int:\n        pass",
                      [("nums = [-1,0,3,5,9,12], target = 9", "4"), ("nums = [-1,0,3,5,9,12], target = 2", "-1")]),
    "maximum-subarray": ("class Solution:\n    def maxSubArray(self, nums: List[int]) -> int:\n        pass",
                         [("nums = [-2,1,-3,4,-1,2,1,-5,4]", "6"), ("nums = [1]", "1")]),
    "contains-duplicate": ("class Solution:\n    def containsDuplicate(self, nums: List[int]) -> bool:\n        pass",
                           [("nums = [1,2,3,1]", "true"), ("nums = [1,2,3,4]", "false")]),
    "valid-anagram": ("class Solution:\n    def isAnagram(self, s: str, t: str) -> bool:\n        pass",
                      [('s = "anagram", t = "nagaram"', "true"), ('s = "rat", t = "car"', "false")]),
    "best-time-to-buy-and-sell-stock": (
        "class Solution:\n    def maxProfit(self, prices: List[int]) -> int:\n        pass",
        [("prices = [7,1,5,3,6,4]", "5"), ("prices = [7,6,4,3,1]", "0")]),
    "climbing-stairs": ("class Solution:\n    def climbStairs(self, n: int) -> int:\n        pass",
                        [("n = 2", "2"), ("n = 3", "3")]),
    "missing-number": ("class Solution:\n    def missingNumber(self, nums: List[int]) -> int:\n        pass",
                       [("nums = [3,0,1]", "2"), ("nums = [0,1]", "2"), ("nums = [9,6,4,2,3,5,7,0,1]", "8")]),
}


def make_problem(slug: str, starter: str | None = None, examples=None) -> LCProblem:
    s, ex = DEMO.get(slug, (starter, examples))
    return LCProblem(slug=slug, title=slug, difficulty="Easy", tags=[], statement_text="stmt",
                     examples=[Example(input_text=i, output_text=o) for i, o in (examples or ex)],
                     constraints_text="", starter_python=starter or s, lang_selected="en", content_hash="h-" + slug)


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "", raising=False)
    old = providers._llm
    yield
    providers._llm = old


@needs_sandbox
@pytest.mark.parametrize("slug", list(DEMO))
def test_curated_bundles_verify_in_sandbox(slug):
    b = AIReferenceBuilder().build(make_problem(slug))
    assert b.verified and b.oracle_code and b.reference_code
    ok, note = validate(make_problem(slug), b)
    assert ok, note


def test_no_llm_unknown_slug_is_unverified_and_never_raises():
    providers._llm = None
    b = AIReferenceBuilder().build(make_problem("some-unknown-problem", "class Solution:\n    def f(self, n): pass",
                                                [("n = 1", "1")]))
    assert b.verified is False and b.notes and b.oracle_code == ""


_GOOD = {
    "oracle_code": "class Solution:\n    def doubleIt(self, n):\n        return sum(n for _ in range(2))\n",
    "reference_code": "class Solution:\n    def doubleIt(self, n):\n        return n * 2\n",
    "gen_inputs_code": "def gen_inputs(rng):\n    return [rng.randint(-50, 50)]\n",
    "comparator": "exact", "constraints": {"n": "-50..50"},
}
_PROBLEM = ("class Solution:\n    def doubleIt(self, n: int) -> int:\n        pass", [("n = 4", "8"), ("n = -1", "-2")])


@needs_sandbox
def test_llm_path_verified():
    providers.register_llm(lambda prompt: json.dumps(_GOOD))
    b = AIReferenceBuilder().build(make_problem("double-it", *_PROBLEM))
    assert b.verified is True and "LLM-synthesised" in b.notes


@needs_sandbox
def test_llm_path_bad_reference_is_unverified():
    bad = {**_GOOD, "reference_code": "class Solution:\n    def doubleIt(self, n):\n        return n + 3\n"}
    providers.register_llm(lambda prompt: json.dumps(bad))
    b = AIReferenceBuilder().build(make_problem("double-it", *_PROBLEM))
    assert b.verified is False and "NOT verified" in b.notes


def test_llm_garbage_reply_is_unverified():
    providers.register_llm(lambda prompt: "not json at all")
    b = AIReferenceBuilder().build(make_problem("double-it", *_PROBLEM))
    assert b.verified is False


def test_register_installs_builder():
    old = providers._reference_builder
    try:
        reference.register()
        assert isinstance(providers.reference_builder(), AIReferenceBuilder)
    finally:
        providers._reference_builder = old
        providers._bundle_cache.clear()
