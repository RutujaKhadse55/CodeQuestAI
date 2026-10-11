import pytest

from app import providers
from app.ai.hints import guard as hg
from app.ai.hints.generate import generate_hint
from app.ai.hints.tiers import LANGS, mistake_classes, template_hint

SUMMARY = {"available": True, "diagnosis": {"mistake_class": "off_by_one_bound", "failure_class": "boundary",
           "divergence": {"variable": "hi", "iteration": 3, "line": 7}}}
REF = ("class Solution:\n    def search(self, nums, target):\n        lo, hi = 0, len(nums) - 1\n"
       "        while lo <= hi:\n            mid = (lo + hi) // 2\n            if nums[mid] == target:\n"
       "                return mid\n            elif nums[mid] < target:\n                lo = mid + 1\n"
       "            else:\n                hi = mid - 1\n        return -1\n")


class FakeLLM:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0

    def __call__(self, prompt):
        self.calls += 1
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


@pytest.fixture()
def llm():
    def install(*replies):
        f = FakeLLM(*replies)
        providers.register_llm(f)
        return f
    yield install
    providers._llm = None


def test_every_template_is_guard_safe_and_has_text():
    for cls in mistake_classes() + ["unknown", None]:
        for lang in LANGS:
            for level in (1, 2, 3, 4):
                t = template_hint(level, cls, None, lang, {"variable": "lo", "iteration": 2, "line": 9})
                assert t and hg.hint_violation(t, level, {}) is None, (cls, lang, level, t)


def test_tier4_is_gapped_pseudocode():
    assert "____" in template_hint(4, "wrong_init", lang="en")
    assert "```" not in template_hint(4, "wrong_init", lang="hi")


def test_failure_class_maps_to_mistake_class_and_lang_differs():
    en = template_hint(1, None, "empty", "en")
    mr = template_hint(1, None, "empty", "mr")
    assert en != mr and "empty" in en


def test_guard_blocks_code_and_reference_copies():
    assert hg.hint_violation("```python\nfor i in range(3):\n    pass\n```", 4, {}) is not None
    assert hg.hint_violation(REF, 3, {"reference_code": REF})  # def + similar
    assert hg.hint_violation("for i in range(n):\n    total += i", 2, {}) == "code_at_low_tier"
    assert hg.hint_violation("Check the loop `lo` and what it assumes.", 3, {}) is None
    assert hg.HintGuard().check("def f(x):\n    return x", {"allowed_hint_level": 2}).passed is False


def test_generate_uses_llm_when_clean(llm):
    f = llm('{"text": "Look at hi near iteration 3 and compare by hand."}')
    text, g = generate_hint(2, SUMMARY, "en")
    assert text.startswith("Look at hi") and g.source == "llm" and g.retries == 0 and f.calls == 1


def test_generate_regenerates_twice_then_template(llm):
    f = llm('{"text": "```python\\nfor i in x:\\n    pass\\n```"}')
    text, g = generate_hint(2, SUMMARY, "en")
    assert g.source == "template" and g.retries == 3 and f.calls == 3 and "```" not in text and "`hi`" in text


def test_generate_recovers_on_second_try(llm):
    llm('{"text": "return mid + 1"}', '{"text": "Think about which end moves."}')
    text, g = generate_hint(1, SUMMARY, "en")
    assert text == "Think about which end moves." and g.retries == 1 and g.source == "llm"


def test_generate_never_raises_and_handles_garbage():
    def boom(p):
        raise RuntimeError("secret")
    providers.register_llm(boom)
    try:
        text, g = generate_hint(9, None, "xx")
        assert text and g.source == "template"
        text, g = generate_hint(3, {"weird": 1}, None)
        assert text
    finally:
        providers._llm = None


def test_register_does_not_override_existing(monkeypatch):
    from app.ai import hints
    monkeypatch.setattr(providers, "_guard", None)
    monkeypatch.setattr(providers, "_hint_service", lambda *a: "crew")
    hints.register()
    assert providers.hint_service()(1, 2, 3, {}) == "crew"
    assert isinstance(providers._guard, hg.HintGuard)
