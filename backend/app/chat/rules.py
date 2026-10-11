"""Deterministic (LLM-free) replies: refusals, consent notices and the evidence-based fallback (spec §7:
'use an evidence-based deterministic fallback where possible'). Only facts from the problem, the learner's own
attempt data and their consented profile summary are used; nothing is invented."""
from __future__ import annotations

import re

from ..contracts.models import LCProblem

REFUSAL = {
    "en": "I can't give the full solution, but I can help you get there. Ask for a hint, or tell me what you've tried and where it fails.",
    "hi": "मैं पूरा समाधान नहीं दे सकता, लेकिन आपको वहाँ तक पहुँचने में मदद कर सकता हूँ। संकेत माँगिए, या बताइए कि आपने क्या कोशिश की और कहाँ अटक रहे हैं।",
    "mr": "मी पूर्ण उत्तर देऊ शकत नाही, पण तिथपर्यंत पोहोचायला मदत करू शकतो. संकेत मागा, किंवा तुम्ही काय प्रयत्न केला आणि कुठे अडकलात ते सांगा.",
}
HINT_AVAILABLE = {
    "en": "Hint level {n} is available for this problem.",
    "hi": "इस समस्या के लिए संकेत स्तर {n} उपलब्ध है।",
    "mr": "या समस्येसाठी संकेत पातळी {n} उपलब्ध आहे.",
}
NOT_PERSONALISED = {
    "en": "Personalised answers are off. Allow access to your public LeetCode profile in the chat settings to enable them.",
    "hi": "व्यक्तिगत उत्तर बंद हैं। इन्हें चालू करने के लिए चैट सेटिंग में अपनी सार्वजनिक LeetCode प्रोफ़ाइल की अनुमति दें।",
    "mr": "वैयक्तिक उत्तरे बंद आहेत. ती सुरू करण्यासाठी चॅट सेटिंगमध्ये तुमच्या सार्वजनिक LeetCode प्रोफाइलची परवानगी द्या.",
}
GUARD_FALLBACK = {
    "en": "I can't share that because it would give away the solution. Here is what I can say instead:",
    "hi": "मैं यह साझा नहीं कर सकता क्योंकि इससे समाधान सामने आ जाएगा। इसके बजाय मैं यह कह सकता हूँ:",
    "mr": "मी हे सांगू शकत नाही कारण त्यामुळे उत्तर उघड होईल. त्याऐवजी मी हे सांगू शकतो:",
}
# Socratic nudges per failure class: questions about behaviour, never code (HI/MR: reviewer pass pending)
NUDGE = {
    "empty": "What should your code return when the input is empty? Does it reach that case without an error?",
    "single_element": "Trace your code by hand on an input with exactly one element. Does every step still make sense?",
    "duplicates": "What happens in your code when the same value appears twice? Is each position used at most once?",
    "negatives": "Try a negative number by hand. Does any starting value or comparison assume numbers are positive?",
    "large": "Think about how your running time grows as the input gets large. Is any step repeated unnecessarily?",
    "boundary": "Check the first and last positions: do your loop bounds include them exactly once?",
    "general": "Pick the smallest input where the output looks wrong and trace each variable line by line.",
}
FAILURE_TEXT = {
    "empty": "an empty input", "single_element": "an input with a single element", "duplicates": "inputs with repeated values",
    "negatives": "inputs with negative numbers", "large": "large inputs", "boundary": "boundary positions (first/last)",
    "general": "some general inputs",
}


def _sentences(text: str, n: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join(parts[:n])[:400]


def explain_problem(p: LCProblem) -> str:
    ex = p.examples[0] if p.examples else None
    lines = [f"**{p.title}** ({p.difficulty}). {_sentences(p.statement_text)}"]
    if ex:
        lines.append(f"Example: input `{ex.input_text}` -> output `{ex.output_text}`.")
    if p.constraints_text:
        lines.append(f"Constraints: {p.constraints_text[:200]}")
    lines.append("Tell me which part is unclear, or what you have tried so far, and I will guide you step by step.")
    return "\n".join(lines)


def why_failing(analysis: dict | None) -> str:
    if not analysis or not analysis.get("data", {}).get("available"):
        return "I don't see an analysed attempt for this problem yet. Run Debug on your code first, then ask me again."
    d = analysis["data"]
    if d.get("passed_all"):
        return "Your latest attempt passed all checks. If something still feels off, tell me what you want to double-check."
    diag = d.get("diagnosis") or {}
    fc = diag.get("failure_class")
    parts = []
    errs = [t["error"] for t in d.get("tests", []) if t.get("error")]
    if errs:
        parts.append(f"Your code raised an error on a visible example: {errs[0]}.")
    if fc:
        parts.append(f"It breaks on {FAILURE_TEXT.get(fc, 'some inputs')}.")
    div = diag.get("divergence")
    if div and div.get("variable"):
        where = f" around iteration {div['iteration']}" if div.get("iteration") else ""
        line = f" (your line {div['line']})" if div.get("line") else ""
        parts.append(f"The variable `{div['variable']}`{where} stops matching the expected behaviour{line}.")
    if not parts:
        parts.append("Some checks failed, but I could not narrow down where.")
    parts.append(NUDGE.get(fc or "general", NUDGE["general"]))
    return " ".join(parts)


def hint_reply(hint: dict | None, lang: str, analysis: dict | None) -> str:
    if not hint or not hint.get("ok"):
        return REFUSAL.get(lang, REFUSAL["en"])
    d = hint["data"]
    if d.get("locked"):
        return (f"That hint level is still locked. {d.get('requirement') or ''} "
                f"You can use level {d['allowed_level']} now.").strip()
    if d.get("text"):
        return d["text"]
    fc = ((analysis or {}).get("data", {}).get("diagnosis") or {}).get("failure_class")
    msg = HINT_AVAILABLE.get(lang, HINT_AVAILABLE["en"]).format(n=d["allowed_level"])
    return f"{msg} {NUDGE.get(fc or 'general', NUDGE['general'])}"


def profile_reply(analysis: dict | None, summary: dict | None) -> str:
    if summary:
        s = summary
        solved = s.get("solved") or {}
        langs = ", ".join(f"{x['language']} ({x['solved']})" for x in s.get("top_languages", [])) or "not available"
        bits = [f"From your public LeetCode profile ({s.get('username')}): solved {solved.get('All', '?')} problems "
                f"(Easy {solved.get('Easy', '?')}, Medium {solved.get('Medium', '?')}, Hard {solved.get('Hard', '?')}); "
                f"top languages: {langs}."]
        if s.get("streak") is not None:
            bits.append(f"Current streak: {s['streak']} days.")
        if s.get("contest_rating") is None:
            bits.append("Contest data was not returned (that does not mean you have never taken part).")
        return " ".join(bits)
    return NOT_PERSONALISED["en"]


def concept_reply(concept: dict | None) -> str:
    if concept and concept.get("ok") and concept["data"].get("explanation"):
        return concept["data"]["explanation"]
    return ("I can't explain that concept right now because no language model is available. "
            "Ask about this problem's statement, your attempt, or request a hint.")
