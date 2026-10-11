"""Language detection (EN / HI / MR) and rule-based intent routing for the problem chat.

Intent routing is deterministic on purpose: the MODEL never chooses tools or functions (spec §7). The router
picks from a fixed allowlist, so a prompt like "call run_shell" cannot change what runs.
"""
from __future__ import annotations

import re

LANG_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_MR_MARKERS = {"आहे", "आहेत", "काय", "मला", "तुम्ही", "नाही", "करा", "द्या", "सांगा", "कसे", "कसं", "समजावून",
               "पाहिजे", "माझा", "माझे", "लिहा", "दाखवा", "आणि", "होते", "नको"}
_HI_MARKERS = {"है", "हैं", "क्या", "मुझे", "नहीं", "करो", "दो", "बताओ", "कैसे", "क्यों", "समझाओ", "चाहिए", "मेरा",
               "मेरी", "लिखो", "दिखाओ", "और", "था", "थी", "मत", "कृपया", "बताइए"}


def detect_lang(text: str, default: str = "en") -> str:
    if not _DEVANAGARI.search(text or ""):
        return default if default in LANG_NAMES and not text.strip() else "en"
    words = set(re.findall(r"[ऀ-ॿ]+", text))
    mr, hi = len(words & _MR_MARKERS), len(words & _HI_MARKERS)
    return "mr" if mr > hi else "hi"


# ---- solution requests (refused) -------------------------------------------------------------------------------
_NOUN = (r"(?:\b(?:solution|answer|code|soln)\b|समाधान|सॉल्यूशन|सोल्यूशन|उत्तर|कोड|जवाब)")
_VERB = (r"(?:\b(?:give|show|write|tell|send|provide|print|paste|need|want|share|reveal|do|dedo|batao|likh|likho|dya|"
         r"dakhva)\b|bata\s*do|de\s*do|दो|दे|दीजिए|बताओ|बता|लिखो|दिखाओ|चाहिए|द्या|सांगा|सांग|लिहा|पाहिजे|दाखवा)")
_NEG = re.compile(r"\b(?:don't|dont|do not|not|without|never)\b|नको|नहीं|मत|नका", re.I)
_OVERRIDE = re.compile(r"ignore\s+(?:all\s+|any\s+|the\s+)?(?:previous\s+|prior\s+|above\s+)?(?:rules|instructions|polic\w+)|"
                       r"disregard\s+(?:your|the)\s+(?:rules|instructions)|you\s+are\s+now\s+|developer\s+mode|"
                       r"system\s*prompt|jailbreak", re.I)


def is_solution_request(text: str) -> bool:
    t = (text or "").lower()
    if _OVERRIDE.search(t) and re.search(_NOUN, t):
        return True
    if _NEG.search(t):
        return False
    if re.search(r"\b(?:full|complete|whole|entire|final|working)\s+" + _NOUN, t):
        return True
    return bool(re.search(_NOUN + r"[^.?!\n]{0,25}" + _VERB, t) or re.search(_VERB + r"[^.?!\n]{0,25}" + _NOUN, t)
                ) and not re.search(r"\b(explain|why|understand|complexity|approach|mean)\b", t)


def is_policy_override(text: str) -> bool:
    return bool(_OVERRIDE.search((text or "").lower()))


# ---- intents ---------------------------------------------------------------------------------------------------
_HINT = re.compile(r"\bhint\b|\bstuck\b|\bclue\b|\bnudge\b|संकेत|हिंट|अटक|अडकलो|अडकले|मार्गदर्शन", re.I)
_WHY = re.compile(r"\b(fail|fails|failing|failed|wrong|error|bug|not working|doesn'?t work|why)\b|गलत|चूक|काम नहीं|"
                  r"चुकीचे|का नाही|काम करत नाही|फेल", re.I)
_PROFILE = re.compile(r"\bmy\s+(profile|leetcode|streak|languages?|progress|level|rating|weak\w*|strength\w*|topics?|"
                      r"stats?|history|badges?|contest\w*)|\brecommend|\bwhat should i (practice|solve|study)|\bhow many\b|"
                      r"मेरा प्रोफ़ाइल|मेरी प्रगति|माझी प्रगती|माझे प्रोफाइल|मेरे बारे", re.I)
_CONCEPT = re.compile(r"\b(?:what\s+is|what's|what\s+are|explain|define|meaning\s+of|teach\s+me(?:\s+about)?)\s+"
                      r"(?:an?\s+|the\s+)?([a-z][a-z0-9 \-+#/()]{2,40}?)\s*(?:\?|$|\.|,| in | for | with )", re.I)
_PROBLEM_WORDS = re.compile(r"\b(problem|question|statement|this|task|example|constraint|input|output)\b", re.I)


def classify_intent(text: str) -> str:
    """solution_request | hint | why_failing | profile | concept | explain_problem"""
    if is_solution_request(text):
        return "solution_request"
    if _HINT.search(text):
        return "hint"
    if _WHY.search(text):
        return "why_failing"
    if _PROFILE.search(text):
        return "profile"
    m = _CONCEPT.search(text)
    if m and not _PROBLEM_WORDS.search(m.group(1)):
        return "concept"
    return "explain_problem"


def extract_concept(text: str) -> str | None:
    m = _CONCEPT.search(text)
    return m.group(1).strip() if m else None
