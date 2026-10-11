"""Render a NeutralMessage to plain language in en/hi/mr (templates first, optional LLM wording, Guard re-run).

HI/MR wording is pending the bilingual reviewer pass [NEEDS VERIFICATION]. Profile style only changes wording
(verbosity, analogy domain), never the facts or outcomes.
"""
from __future__ import annotations

import logging

from pydantic import BaseModel

from ...contracts.models import NeutralMessage
from ..hints.guard import hint_violation
from ..hints.tiers import LANGS, norm_lang, template_hint
from .neutral import NO_DATA, PASSED

log = logging.getLogger(__name__)

_MISTAKE = {
    "off_by_one_bound": ("A loop boundary is off by one, so one position is skipped or visited an extra time.",
                         "लूप (loop) की सीमा एक से चूक रही है, इसलिए एक position छूट रही है या एक बार ज़्यादा आ रही है।",
                         "लूप (loop) ची सीमा एकाने चुकत आहे, त्यामुळे एक position सुटते किंवा एकदा जास्त येते."),
    "missing_empty_case": ("The empty input is not handled before the main logic runs.",
                           "मुख्य logic चलने से पहले खाली input को नहीं संभाला गया है।",
                           "मुख्य logic चालण्यापूर्वी रिकामा input हाताळलेला नाही."),
    "wrong_init": ("A variable starts with a value that is wrong for some inputs.",
                   "एक variable ऐसे मान से शुरू होता है जो कुछ input के लिए गलत है।",
                   "एक variable काही input साठी चुकीच्या मूल्याने सुरू होतो."),
    "wrong_comparison": ("A comparison treats equal or repeated values the wrong way.",
                         "एक तुलना बराबर या दोहराए गए मानों को गलत तरीके से संभालती है।",
                         "एक तुलना समान किंवा पुनरावृत्त मूल्ये चुकीच्या पद्धतीने हाताळते."),
    "accumulator_reset": ("A running total or counter is reset at the wrong moment.",
                          "कोई कुल योग या counter गलत समय पर reset हो रहा है।",
                          "एखादा एकूण किंवा counter चुकीच्या वेळी reset होत आहे."),
    "wrong_operator": ("An operator does not match the rule you intended.",
                       "एक operator आपके इरादे वाले नियम से मेल नहीं खाता।",
                       "एक operator तुमच्या हेतूच्या नियमाशी जुळत नाही."),
    "missing_edge_single": ("The code assumes at least two items and breaks with a single item.",
                            "कोड मानकर चलता है कि कम से कम दो items हैं और एक item पर टूट जाता है।",
                            "कोड गृहीत धरतो की किमान दोन items आहेत आणि एका item वर चुकतो."),
    "hardcoded_output": ("The answer looks tied to the sample cases instead of being computed from the input.",
                         "उत्तर input से निकालने के बजाय नमूना मामलों से बँधा दिखता है।",
                         "उत्तर input वरून काढण्याऐवजी नमुना प्रकरणांशी बांधलेले दिसते."),
}
_FAILURE = {
    "empty": ("It breaks on an empty input.", "यह खाली input पर टूटता है।", "हे रिकाम्या input वर चुकते."),
    "single_element": ("It breaks on an input with a single element.", "यह एक element वाले input पर टूटता है।",
                       "हे एका element च्या input वर चुकते."),
    "duplicates": ("It breaks on inputs with repeated values.", "यह दोहराए गए मानों वाले input पर टूटता है।",
                   "हे पुनरावृत्त मूल्यांच्या input वर चुकते."),
    "negatives": ("It breaks on inputs with negative numbers.", "यह negative संख्याओं वाले input पर टूटता है।",
                  "हे negative संख्यांच्या input वर चुकते."),
    "large": ("It breaks, or is too slow, on large inputs.", "यह बड़े input पर टूटता है या बहुत धीमा है।",
              "हे मोठ्या input वर चुकते किंवा खूप हळू आहे."),
    "boundary": ("It breaks at the first or last position.", "यह पहली या आखिरी position पर टूटता है।",
                 "हे पहिल्या किंवा शेवटच्या position वर चुकते."),
}
_GENERIC = ("Some checks failed, but I cannot narrow down where yet.", "कुछ जाँचें fail हुईं, पर अभी जगह तय नहीं हो पाई।",
            "काही तपासण्या fail झाल्या, पण अजून जागा निश्चित करता आली नाही.")
_PASSED = ("Your latest attempt passed all checks. If something still feels off, tell me what you want to double-check.",
           "आपका ताज़ा प्रयास सभी जाँचों में पास हुआ। अगर फिर भी कुछ ठीक नहीं लगता, तो बताइए कि क्या दोबारा जाँचना है।",
           "तुमचा ताजा प्रयत्न सर्व तपासण्यांत पास झाला. तरीही काही खटकत असेल तर काय पुन्हा तपासायचे ते सांगा.")
_NODATA = ("I do not see an analysed attempt yet. Run Debug on your code first, then ask again.",
           "मुझे अभी कोई जाँचा हुआ प्रयास नहीं दिखता। पहले अपने कोड पर Debug चलाइए, फिर दोबारा पूछिए।",
           "मला अजून तपासलेला प्रयत्न दिसत नाही. आधी तुमच्या कोडवर Debug चालवा, मग पुन्हा विचारा.")
_DIV = {"en": "The variable `{v}`{w} stops matching the expected behaviour{l}.",
        "hi": "variable `{v}`{w} अपेक्षित व्यवहार से अलग होने लगता है{l}।",
        "mr": "variable `{v}`{w} अपेक्षित वर्तनापासून वेगळा होऊ लागतो{l}."}
_W = {"en": " around iteration {i}", "hi": " (iteration {i} के आसपास)", "mr": " (iteration {i} च्या आसपास)"}
_L = {"en": " (your line {n})", "hi": " (आपकी line {n})", "mr": " (तुमची line {n})"}


def template_render(msg: NeutralMessage, lang: str | None = "en", profile: dict | None = None) -> str:
    lg = norm_lang(lang)
    i = LANGS.index(lg)
    if msg.concept == NO_DATA:
        return _NODATA[i]
    if msg.concept == PASSED:
        return _PASSED[i]
    parts = []
    mc = msg.mistake_class if msg.mistake_class in _MISTAKE else None
    if mc:
        parts.append(_MISTAKE[mc][i])
    if msg.failure_class in _FAILURE:
        parts.append(_FAILURE[msg.failure_class][i])
    d = msg.divergence
    if d and d.variable:
        parts.append(_DIV[lg].format(v=d.variable, w=_W[lg].format(i=d.iteration) if d.iteration else "",
                                     l=_L[lg].format(n=d.line) if d.line else ""))
    if not parts:
        parts.append(_GENERIC[i])
    style = (profile or {}).get("style") or (profile or {})
    if str(style.get("verbosity", "")).lower() in ("short", "brief", "low"):
        return parts[0]
    parts.append(template_hint(1, msg.mistake_class, msg.failure_class, lg))
    return " ".join(parts)


class _Out(BaseModel):
    text: str


_SYSTEM = ("You explain why a learner's code fails, in plain language, as a patient mentor. Never write code, never "
           "give the corrected solution, never mention hidden test inputs. Keep technical words (loop, index, array, "
           "variable) in English. Use only the facts given.")
_NAMES = {"en": "English", "hi": "Hindi (Devanagari)", "mr": "Marathi (Devanagari)"}


def _llm_render(msg: NeutralMessage, lg: str, profile: dict | None, base: str) -> str | None:
    from ...crew import llm  # lazy: crew is optional
    if not llm.available():
        return None
    style = (profile or {}).get("style") or (profile or {})
    prompt = (f"Write a 2-4 sentence explanation in {_NAMES[lg]}.\nNeutral facts: {msg.model_dump(exclude_none=True)}\n"
              f"Learner style hints (wording only, optional): {style or 'none'}\nReference wording:\n{base}\n"
              'Reply as JSON {"text": "..."}.')
    out = llm.complete_json(_SYSTEM, prompt, _Out)
    return out.text.strip() if out and out.text.strip() else None


def render(msg: NeutralMessage, lang: str | None = "en", profile: dict | None = None, use_llm: bool = True) -> str:
    """Never raises. LLM wording only for real diagnoses; the Guard is re-run on it, else the template is returned."""
    lg = norm_lang(lang)
    base = template_render(msg, lg, profile)
    if not use_llm or msg.concept in (NO_DATA, PASSED):
        return base
    try:
        text = _llm_render(msg, lg, profile, base)
        if text and hint_violation(text, 3, {}) is None:
            return text
    except Exception as exc:  # noqa: BLE001
        log.warning("explain render failed: %s", type(exc).__name__)
    return base


class ExplainerImpl:
    """Implements the Explainer Protocol."""

    def render(self, msg: NeutralMessage, lang: str, profile: dict | None = None) -> str:
        return render(msg, lang, profile)

