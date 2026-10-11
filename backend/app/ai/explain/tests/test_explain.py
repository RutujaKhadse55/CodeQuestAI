import pytest

from app import providers
from app.ai.explain.neutral import from_summary
from app.ai.explain.render import ExplainerImpl, render, template_render

SUMMARY = {"available": True, "passed_all": False, "tests": [],
           "diagnosis": {"mistake_class": "missing_empty_case", "failure_class": "empty",
                         "divergence": {"variable": "lo", "iteration": 2, "line": 4, "expected": "SECRET", "actual": "9"}}}


@pytest.fixture(autouse=True)
def _reset():
    yield
    providers._llm = None


def test_neutral_has_no_hidden_values():
    m = from_summary(SUMMARY)
    assert m.mistake_class == "missing_empty_case" and m.divergence.variable == "lo"
    assert m.divergence.expected is None and m.divergence.actual is None
    assert from_summary({"available": True, "passed_all": True}).concept == "passed"
    assert from_summary(None).concept == "no_data"
    assert from_summary({"available": False}).concept == "no_data"


@pytest.mark.parametrize("lang", ["en", "hi", "mr", "xx"])
def test_templates_render_all_languages(lang):
    t = render(from_summary(SUMMARY), lang)
    assert t and "```" not in t and "SECRET" not in t
    assert ("`lo`" in t) and (lang in ("en", "xx")) == t.replace("`lo`", "").isascii() or lang in ("hi", "mr")


def test_profile_verbosity_changes_wording_only():
    m = from_summary(SUMMARY)
    short = template_render(m, "en", {"style": {"verbosity": "short"}})
    full = template_render(m, "en", None)
    assert short != full and full.startswith(short)


def test_llm_wording_used_and_guard_falls_back():
    m = from_summary(SUMMARY)
    providers.register_llm(lambda p: '{"text": "Your code forgets the empty list."}')
    assert render(m, "en") == "Your code forgets the empty list."
    providers.register_llm(lambda p: '{"text": "```python\\ndef f(x):\\n    return x\\n```"}')
    assert render(m, "en") == template_render(m, "en")

    def boom(p):
        raise RuntimeError("x")
    providers.register_llm(boom)
    assert render(m, "en") == template_render(m, "en")


def test_explainer_protocol():
    assert ExplainerImpl().render(from_summary(SUMMARY), "hi", None)
