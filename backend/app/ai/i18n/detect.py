"""Language detection: en / hi / mr / hinglish (Latin-script Hindi). Script + stop-word based, no LLM.

`detect(text)` returns {lang, confidence, code_mixed}; `detect_lang(text)` just the code.
Devanagari handling reuses chat/lang.py (Hindi vs Marathi markers).
"""
from __future__ import annotations

import re

from ...chat.lang import detect_lang as _deva_lang

_DEVA = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")
_ROMAN_HI = {"hai", "hain", "nahi", "nahin", "kya", "mujhe", "mera", "meri", "karo", "kar", "batao", "bata", "samjhao",
             "kaise", "kyun", "kyon", "ye", "yeh", "wo", "woh", "aur", "ka", "ki", "ke", "se", "mein", "main", "tum",
             "aap", "ho", "tha", "hota", "chahiye", "dikhao", "likho", "galat", "sahi", "dena", "do", "bhai", "yaar"}
_ROMAN_MR = {"aahe", "ahe", "aahet", "mala", "tumhi", "kasa", "kase", "saang", "sang", "samjav", "nahi", "kay", "ani",
             "pahije", "dya", "kara", "majha", "maza", "mazha", "chuk", "barobar"}
_EN_STOP = {"the", "is", "are", "what", "why", "how", "my", "this", "that", "and", "to", "of", "in", "it", "for", "with",
            "does", "not", "can", "you", "me", "give", "hint", "code", "please", "explain", "why"}
_WORD = re.compile(r"[A-Za-z]+")


def detect(text: str, default: str = "en") -> dict:
    t = text or ""
    deva, latin = len(_DEVA.findall(t)), len(_LATIN.findall(t))
    if not deva and not latin:
        return {"lang": default if default in ("en", "hi", "mr") else "en", "confidence": 0.3, "code_mixed": False}
    if deva:
        lang = _deva_lang(t)
        words = set(re.findall(r"[ऀ-ॿ]+", t))
        hits = len(words & _hits_for(lang))
        share = deva / max(deva + latin, 1)
        return {"lang": lang, "confidence": round(min(0.95, 0.55 + 0.1 * hits) * (0.6 + 0.4 * share), 2),
                "code_mixed": latin > 0.3 * deva and bool(latin)}
    words = [w.lower() for w in _WORD.findall(t)]
    hi = sum(w in _ROMAN_HI for w in words)
    mr = sum(w in _ROMAN_MR for w in words)
    en = sum(w in _EN_STOP for w in words)
    if mr > hi and mr >= 2:
        return {"lang": "mr", "confidence": round(min(0.8, 0.4 + 0.1 * mr), 2), "code_mixed": en > 0}
    if hi >= 2 or (hi >= 1 and hi >= en and len(words) <= 4 and hi > mr):
        return {"lang": "hinglish", "confidence": round(min(0.9, 0.45 + 0.1 * hi), 2), "code_mixed": en > 0}
    return {"lang": "en", "confidence": round(min(0.95, 0.6 + 0.05 * en), 2), "code_mixed": False}


def _hits_for(lang: str) -> set[str]:
    from ...chat import lang as cl
    return cl._MR_MARKERS if lang == "mr" else cl._HI_MARKERS


def detect_lang(text: str, default: str = "en") -> str:
    return detect(text, default)["lang"]


def reply_lang(text: str, default: str = "en") -> str:
    """Language to answer in: hinglish is answered in English (en) with simple wording unless Hindi was selected."""
    lang = detect_lang(text, default)
    return "en" if lang == "hinglish" else lang
