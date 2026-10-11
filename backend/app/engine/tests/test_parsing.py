import pytest

from app.engine import ast_policy
from app.engine.examples_parser import ParseError, args_for, parse_inputs, parse_value
from app.engine.signature import parse_signature, unsupported_reason

# ---- examples parser: 10 LeetCode formats (plan §9) ----
CASES = [
    ("nums = [2,7,11,15], target = 9", {"nums": [2, 7, 11, 15], "target": 9}),
    ("nums = [3,3], target = 6", {"nums": [3, 3], "target": 6}),
    ("nums = [2,7,11,15]\ntarget = 9", {"nums": [2, 7, 11, 15], "target": 9}),
    ('s = "anagram", t = "nagaram"', {"s": "anagram", "t": "nagaram"}),
    ('s = "a, b = c", t = "x"', {"s": "a, b = c", "t": "x"}),
    ("n = 3", {"n": 3}),
    ("prices = [7,1,5,3,6,4]", {"prices": [7, 1, 5, 3, 6, 4]}),
    ("nums = [-1,0,3,5,9,12], target = 9", {"nums": [-1, 0, 3, 5, 9, 12], "target": 9}),
    ("nums = [[1,2],[3]], flag = true", {"nums": [[1, 2], [3]], "flag": True}),
    ("Input: nums = [], k = null", {"nums": [], "k": None}),
    ("x = 2.50000, n = -2", {"x": 2.5, "n": -2}),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_parse_inputs(text, expected):
    assert parse_inputs(text) == expected


@pytest.mark.parametrize("text,expected", [("[0,1]", [0, 1]), ("true", True), ("null", None), ('"abc"', "abc"),
                                           ("Output: 21", 21), ("[[1,2],[3]]", [[1, 2], [3]])])
def test_parse_value(text, expected):
    assert parse_value(text) == expected


def test_parse_errors_and_no_code_execution():
    with pytest.raises(ParseError):
        parse_inputs("just words")
    with pytest.raises(ParseError):
        parse_value("__import__('os').system('x')")  # literal_eval only


def test_args_for_orders_by_params_and_positional_fallback():
    assert args_for(["target", "nums"], {"nums": [1], "target": 2}) == [2, [1]]
    assert args_for(["a", "b"], {"x": 1, "y": 2}) == [1, 2]
    with pytest.raises(ParseError):
        args_for(["a"], {"x": 1, "y": 2})


# ---- signature ----
STARTER = "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        "


def test_signature_from_starter_with_empty_body():
    s = parse_signature(STARTER)
    assert s.entry == "twoSum" and s.params == ["nums", "target"] and s.annotations["return"] == "List[int]"


def test_signature_plain_function():
    assert parse_signature("def f(a, b):\n    return a").entry == "f"
    assert parse_signature(None).entry is None


def test_unsupported_types():
    assert unsupported_reason(parse_signature(STARTER)) is None
    ll = "class Solution:\n    def f(self, head: Optional[ListNode]) -> Optional[ListNode]:\n        "
    assert "ListNode" in unsupported_reason(parse_signature(ll))
    inplace = "class Solution:\n    def f(self, nums: List[int]) -> None:\n        "
    assert unsupported_reason(parse_signature(inplace))


# ---- AST policy ----
GOOD = "from typing import List\nimport math\nclass Solution:\n    def f(self, nums: List[int]) -> int:\n        return math.floor(sum(nums))\n"


def test_policy_allows_normal_code_and_init():
    assert ast_policy.check(GOOD) == []
    assert ast_policy.check("class A:\n    def __init__(self):\n        super().__init__()\n") == []


@pytest.mark.parametrize("code,rule", [
    ("open('x')", "banned_builtin"),
    ("import os", "import_not_allowed"),
    ("from os import path", "import_not_allowed"),
    ("import collections.abc, sys", "import_not_allowed"),
    ("eval('1')", "banned_builtin"),
    ("f = exec", "banned_builtin"),
    ("x = ().__class__", "dunder_access"),
    ("getattr(x, 'a')", "banned_builtin"),
    ("'{0.__class__}'.format(1)", "format_attribute_traversal"),
    ("from . import x", "import_not_allowed"),
])
def test_policy_rejects(code, rule):
    assert rule in {v.rule for v in ast_policy.check(code)}


def test_policy_size_and_syntax():
    assert ast_policy.check("x=1\n" * 10000)[0].rule == "too_long"
    assert ast_policy.check("def (") == []  # harness reports syntax errors
