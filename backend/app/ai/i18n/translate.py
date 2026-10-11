"""LLM translation (en -> hi/mr) with the glossary, protected code/identifiers, guard re-run and an untranslated
fallback. Implements the Translator Protocol: translate(text, lang) -> str (never raises)."""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from ...contracts.models import GuardResult
from ..hints.guard import hint_violation

log = logging.getLogger(__name__)
_GLOSSARY = Path(__file__).with_name("glossary.json")
_NAMES = {"hi": "Hindi (Devanagari)", "mr": "Marathi (Devanagari)"}
_PROTECT = re.compile(r"```.*?```|`[^`\n]+`", re.S)
_TOKEN = "⟦{}⟧"


class _Out(BaseModel):
    text: str


@lru_cache(maxsize=1)
def glossary() -> dict:
    try:
        return json.loads(_GLOSSARY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _protect(text: str) -> tuple[str, list[str]]:
    saved: list[str] = []

    def sub(m: re.Match) -> str:
        saved.append(m.group(0))
        return _TOKEN.format(len(saved) - 1)

    return _PROTECT.sub(sub, text), saved


def _restore(text: str, saved: list[str]) -> str | None:
    for i, original in enumerate(saved):
        tok = _TOKEN.format(i)
        if tok not in text:
            return None  # the model dropped protected code: unsafe
        text = text.replace(tok, original)
    return text


def translate_detailed(text: str, lang: str | None) -> tuple[str, bool, GuardResult]:
    """(text, translated, guard). Falls back to the untranslated text on any failure or guard violation."""
    passthrough = (text, False, GuardResult(passed=True, retries=0, source="template"))
    if lang not in _NAMES or not (text or "").strip():
        return passthrough
    try:
        from ...crew import llm  # lazy: crew is optional
        if not llm.available():
            return passthrough
        masked, saved = _protect(text)
        already_unsafe = hint_violation(text, 4, {}) is not None  # input itself has code: only compare, don't block
        g = glossary()
        prompt = (f"Translate the text into {_NAMES[lang]}. Rules: keep these English words as they are or use the "
                  f"glossary form: keep={g.get('keep', [])}; glossary={g.get('terms', {}).get(lang, {})}. "
                  f"Tokens like {_TOKEN.format(0)} are code and must be copied exactly, in place. Do not add, remove or "
                  f"solve anything; do not write code.\n\nText:\n{masked}\n\nReply as JSON "
                  '{"text": "..."}.')
        for retries in range(2):
            out = llm.complete_json("You are a precise technical translator for programming education.", prompt, _Out)
            if out is None:
                break
            restored = _restore(out.text, saved)
            if restored and (already_unsafe or hint_violation(restored, 4, {}) is None):
                return restored, True, GuardResult(passed=True, retries=retries, source="llm")
    except Exception as exc:  # noqa: BLE001
        log.warning("translate failed: %s", type(exc).__name__)
    return passthrough


class TranslatorImpl:
    """Implements the Translator Protocol."""

    def translate(self, text: str, lang: str) -> str:
        return translate_detailed(text, lang)[0]
