import pytest

from app import providers
from app.ai.i18n.detect import detect, detect_lang
from app.ai.i18n.translate import TranslatorImpl, glossary, translate_detailed
from app.ai.i18n.voice_text import voice_text


@pytest.fixture(autouse=True)
def _reset():
    yield
    providers._llm = None


@pytest.mark.parametrize("text,lang", [
    ("Why does my loop fail on empty input?", "en"),
    ("मुझे हिंट चाहिए, यह क्या है", "hi"),
    ("मला हिंट पाहिजे, हे काय आहे", "mr"),
    ("mujhe hint chahiye yaar, ye kya hai", "hinglish"),
])
def test_detect(text, lang):
    assert detect_lang(text) == lang
    assert 0 < detect(text)["confidence"] <= 1


def test_detect_empty_and_codemixed():
    assert detect("")["lang"] == "en"
    assert detect("मुझे loop समझाओ and the index")["code_mixed"] is True


def test_glossary_loaded_with_required_terms():
    g = glossary()
    assert {"loop", "index", "array", "variable"} <= set(g["keep"])


def test_translate_untranslated_without_llm():
    assert TranslatorImpl().translate("Check the loop.", "hi") == "Check the loop."
    assert translate_detailed("Hi", "en")[1] is False


def test_translate_with_llm_protects_code_and_uses_glossary():
    seen = []

    def llm(prompt):
        seen.append(prompt)
        return '{"text": "लूप (loop) में ⟦0⟧ देखिए।"}'
    providers.register_llm(llm)
    text, ok, g = translate_detailed("Check the loop at `lo`.", "hi")
    assert ok and text == "लूप (loop) में `lo` देखिए।" and g.source == "llm"
    assert "लूप (loop)" in seen[0] and "⟦0⟧" in seen[0] and "`lo`" not in seen[0].split("Text:")[1]


def test_translate_falls_back_when_code_dropped_or_guard_fails():
    providers.register_llm(lambda p: '{"text": "बिना कोड"}')
    assert translate_detailed("See `lo` now", "mr")[:2] == ("See `lo` now", False)
    providers.register_llm(lambda p: '{"text": "```python\\ndef f(x):\\n    return x\\n```"}')
    assert translate_detailed("Plain text", "hi")[:2] == ("Plain text", False)
    providers.register_llm(lambda p: "not json")
    assert translate_detailed("Plain text", "hi")[:2] == ("Plain text", False)


def test_voice_text_en():
    s = voice_text("Use `i <= n` and arr[i] with O(n log n) or O(n^2); x != -1.", "en")
    assert "less than or equal to" in s and "open bracket" in s and "big O of n log n" in s
    assert "n squared" in s and "is not equal to" in s and "minus 1" in s and "`" not in s


@pytest.mark.parametrize("lang,word", [("hi", "से छोटा या बराबर"), ("mr", "पेक्षा लहान किंवा बरोबर")])
def test_voice_text_other_languages(lang, word):
    assert word in voice_text("a <= b", lang) and "<" not in voice_text("O(1)", lang)


def test_voice_text_drops_code_blocks():
    assert "def" not in voice_text("Look:\n```python\ndef f(): pass\n```\nDone", "en")


def test_register_returns_translator():
    from app.ai import i18n
    assert i18n.register().translate("x", "en") == "x"
