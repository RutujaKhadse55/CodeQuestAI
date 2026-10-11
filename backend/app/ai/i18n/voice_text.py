"""Voice-friendly rewrite for TTS: symbols to words per language (<=, O(n), brackets), markdown/code marks removed.
Pure function, no LLM. HI/MR wording pending reviewer pass [NEEDS VERIFICATION]."""
from __future__ import annotations

import re

_SYM = {
    "en": {"<=": "less than or equal to", ">=": "greater than or equal to", "==": "equals", "!=": "is not equal to",
           "<": "less than", ">": "greater than", "->": "gives", "=>": "gives", "+": "plus", "*": "times", "/": "divided by",
           "%": "modulo", "=": "is set to", "[": "open bracket", "]": "close bracket", "(": "open parenthesis",
           ")": "close parenthesis", "{": "open brace", "}": "close brace", "&&": "and", "||": "or", "-": "minus",
           "big_o": "big O of", "squared": "squared", "cubed": "cubed", "power": "to the power", "code": "code omitted"},
    "hi": {"<=": "से छोटा या बराबर", ">=": "से बड़ा या बराबर", "==": "बराबर है", "!=": "बराबर नहीं है",
           "<": "से छोटा", ">": "से बड़ा", "->": "देता है", "=>": "देता है", "+": "प्लस", "*": "गुणा", "/": "भाग",
           "%": "मॉड्यूलो", "=": "सेट है", "[": "ब्रैकेट खुला", "]": "ब्रैकेट बंद", "(": "कोष्ठक खुला",
           ")": "कोष्ठक बंद", "{": "ब्रेस खुला", "}": "ब्रेस बंद", "&&": "और", "||": "या", "-": "माइनस",
           "big_o": "बिग ओ ऑफ़", "squared": "का वर्ग", "cubed": "का घन", "power": "घात", "code": "कोड छोड़ा गया"},
    "mr": {"<=": "पेक्षा लहान किंवा बरोबर", ">=": "पेक्षा मोठे किंवा बरोबर", "==": "बरोबर आहे", "!=": "बरोबर नाही",
           "<": "पेक्षा लहान", ">": "पेक्षा मोठे", "->": "देतो", "=>": "देतो", "+": "प्लस", "*": "गुणिले", "/": "भागिले",
           "%": "मॉड्युलो", "=": "सेट आहे", "[": "ब्रॅकेट उघडा", "]": "ब्रॅकेट बंद", "(": "कंस उघडा",
           ")": "कंस बंद", "{": "ब्रेस उघडा", "}": "ब्रेस बंद", "&&": "आणि", "||": "किंवा", "-": "वजा",
           "big_o": "बिग ओ ऑफ", "squared": "वर्ग", "cubed": "घन", "power": "घात", "code": "कोड वगळला"},
}
_FENCED = re.compile(r"```.*?```", re.S)
_BIG_O = re.compile(r"\bO\(\s*([^()]*(?:\([^()]*\)[^()]*)*)\)")
_ORDER = ["<=", ">=", "==", "!=", "->", "=>", "&&", "||", "<", ">", "+", "*", "/", "%", "=", "[", "]", "{", "}"]


def _expr(e: str, t: dict) -> str:
    e = re.sub(r"(\w)\s*\^\s*2\b", lambda m: f"{m.group(1)} {t['squared']}", e)
    e = re.sub(r"(\w)\s*\^\s*3\b", lambda m: f"{m.group(1)} {t['cubed']}", e)
    e = re.sub(r"(\w)\s*\^\s*(\w+)", lambda m: f"{m.group(1)} {t['power']} {m.group(2)}", e)
    return re.sub(r"\s+", " ", e.replace("*", f" {t['*']} ")).strip()


def voice_text(text: str, lang: str | None = "en") -> str:
    t = _SYM.get(lang or "en", _SYM["en"])
    s = _FENCED.sub(f" {t['code']} ", text or "")
    s = _BIG_O.sub(lambda m: f" {t['big_o']} {_expr(m.group(1), t)} ", s)
    s = s.replace("`", "")
    s = re.sub(r"\*\*|__|^#+\s*|^\s*[-*]\s+", "", s, flags=re.M)  # markdown bold/headings/bullets
    s = re.sub(r"(?<![\w])-(?=\d)", f" {t['-']} ", s)  # negative numbers
    s = re.sub(r"(?<=\s)-(?=\s)", t["-"], s)  # spaced minus
    for sym in _ORDER:
        s = s.replace(sym, f" {t[sym]} ")
    s = re.sub(r"\(", f" {t['(']} ", s)
    s = re.sub(r"\)", f" {t[')']} ", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    return re.sub(r"[ \t]+", " ", s).strip()
