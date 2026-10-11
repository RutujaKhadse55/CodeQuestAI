"""LLM hint wording on top of the tier templates. Never raises: any failure returns the guarded template."""
from __future__ import annotations

import logging

from pydantic import BaseModel

from ...contracts.models import GuardResult
from .guard import guarded_hint
from .tiers import norm_lang, template_hint

log = logging.getLogger(__name__)

LANG_NAMES = {"en": "English", "hi": "Hindi (Devanagari)", "mr": "Marathi (Devanagari)"}
TIER_RULES = {
    1: "one short Socratic question that points at the kind of case that fails (no variable names, no code)",
    2: "2-3 sentences pointing at the variable or step to inspect and how to check it by hand (no code)",
    3: "2-4 sentences naming the faulty idea and where to look, but not the fix (no code at all)",
    4: "numbered plain-language pseudocode with gaps (____) for the learner to fill; words only, no code, no function definition",
}
SYSTEM = ("You are a Socratic programming mentor. Never write code, never write a function, never give the final answer. "
          "Keep technical words (loop, index, array, variable) in English. Do not mention hidden test inputs.")


class _Out(BaseModel):
    text: str


def _facts(summary: dict | None) -> dict:
    diag = (summary or {}).get("diagnosis") or {}
    div = diag.get("divergence") or {}
    return {"mistake_class": diag.get("mistake_class"), "failure_class": diag.get("failure_class"),
            "divergence": {k: div.get(k) for k in ("variable", "iteration", "line") if div.get(k) is not None}}


def _llm_text(level: int, lang: str, facts: dict, base: str, strict: bool) -> str | None:
    from ...crew import llm  # lazy: crew is optional
    if not llm.available():
        return None
    prompt = (f"Write a level {level} hint in {LANG_NAMES[lang]}: {TIER_RULES[level]}.\n"
              f"Neutral facts (do not invent others): {facts}\n"
              f"Reference wording to rephrase, keep the same level of detail:\n{base}\n"
              + ("Your previous draft contained code. Use plain words only, no code blocks, no statements.\n" if strict else "")
              + 'Reply as JSON {"text": "..."}.')
    out = llm.complete_json(SYSTEM, prompt, _Out)
    return out.text if out else None


def generate_hint(level: int, summary: dict | None = None, lang: str | None = "en",
                  ctx: dict | None = None) -> tuple[str, GuardResult]:
    """Return (guarded hint text, GuardResult). `summary` is an attempt summary (chat.tools.attempt_summary)."""
    level = min(max(int(level or 1), 1), 4)
    lg = norm_lang(lang)
    facts = _facts(summary)
    gctx = {**(ctx or {}), "allowed_hint_level": level}

    def template() -> str:
        return template_hint(level, facts["mistake_class"], facts["failure_class"], lg, facts["divergence"])

    try:
        base = template()
        return guarded_hint(lambda attempt: _llm_text(level, lg, facts, base, attempt > 0), level, gctx, template)
    except Exception as exc:  # noqa: BLE001
        log.warning("hint generation failed: %s", type(exc).__name__)
        return template_hint(level, None, None, lg), GuardResult(passed=True, retries=0, source="template")


def hint_service(user_id: str, slug: str, level: int, ctx: dict) -> str | None:
    """providers.register_hint_service-compatible callable."""
    text, _ = generate_hint(level, (ctx or {}).get("summary"), (ctx or {}).get("language"), None)
    return text

