"""Restricted tool registry for the problem chat (spec §6, §7).

Exactly four tools. Properties enforced here, not by the model:
  - allowlist: a tool name outside TOOLS is rejected, nothing is looked up dynamically;
  - typed, bounded arguments (pydantic, extra="forbid"): a model-supplied `user_id` / path / URL is a validation error;
  - the learner id comes ONLY from ToolContext (derived from authentication), never from arguments;
  - every query is scoped to that learner; outputs are small JSON, later wrapped as untrusted <data>.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlmodel import Session, desc, select

from .. import providers
from ..contracts.models import LCProblem
from ..db.models_core import (Attempt, ChatMessage, ChatThread, DiagnosisRow, LCProblemRow, ProfileConsent,
                              TestResultRow)
from ..engine.hint_state import HintStateService, requirements_text
from ..profile_rag import answerer, service as profile_service

TOOL_NAMES = ("get_history", "run_analysis", "get_hint", "explain_concept")
MAX_FIELD = 300


@dataclass
class ToolContext:
    session: Session
    user_id: str          # authenticated learner (server-derived) - tools never read a user id from arguments
    thread: ChatThread
    problem_row: LCProblemRow
    problem: LCProblem
    language: str = "en"


class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetHistoryArgs(_Args):
    limit: int = Field(default=6, ge=1, le=20)


class RunAnalysisArgs(_Args):
    analysis: Literal["latest_attempt", "profile_strengths"]
    question: str | None = Field(default=None, max_length=300)


class GetHintArgs(_Args):
    level: int | None = Field(default=None, ge=1, le=4)


class ExplainConceptArgs(_Args):
    concept: str = Field(min_length=2, max_length=60, pattern=r"^[\w \-+#/()]+$")  # no punctuation tricks


def _clip(v: Any, n: int = MAX_FIELD) -> str:
    return str(v)[:n]


# ----------------------------------------------------------------------------------------------- tool: get_history
def get_history(ctx: ToolContext, a: GetHistoryArgs) -> dict:
    msgs = ctx.session.exec(select(ChatMessage).where(ChatMessage.thread_id == ctx.thread.id)
                            .order_by(desc(ChatMessage.id)).limit(a.limit)).all()
    attempts = ctx.session.exec(select(Attempt).where(
        Attempt.user_id == ctx.user_id, Attempt.problem_slug == ctx.thread.problem_slug)
        .order_by(desc(Attempt.id)).limit(5)).all()
    return {"messages": [{"role": m.role, "content": _clip(m.content)} for m in reversed(msgs)],
            "attempts": [{"attempt_id": x.id, "passed_all": x.passed_all, "verified": x.verified,
                          "copy_flagged": x.copy_flagged, "at": x.created_at.isoformat()} for x in attempts]}


# --------------------------------------------------------------------------------------------- tool: run_analysis
def attempt_summary(session: Session, a: Attempt) -> dict:
    """Plain facts about one attempt: outcomes, classes and a short divergence. No code, no hidden inputs."""
    rows = session.exec(select(TestResultRow).where(TestResultRow.attempt_id == a.id)).all()
    d = session.exec(select(DiagnosisRow).where(DiagnosisRow.attempt_id == a.id)).first()
    out: dict = {"available": True, "attempt_id": a.id, "passed_all": a.passed_all, "verified": a.verified,
                 "tests": [{"kind": r.kind, "outcome": r.outcome, "error": _clip(r.error, 120) if r.error else None,
                            "failure_class": r.failure_class} for r in rows if r.kind != "fuzz"],
                 "fuzz": [{"outcome": r.outcome, "failure_class": r.failure_class} for r in rows if r.kind == "fuzz"]}
    if d:
        div = json.loads(d.divergence_json) if d.divergence_json else None
        out["diagnosis"] = {"mistake_class": d.mistake_class, "failure_class": d.failure_class,
                            "confidence": d.confidence,
                            "divergence": ({"variable": div.get("variable"), "iteration": div.get("iteration"),
                                            "line": div.get("line"), "expected": _clip(div.get("expected"), 40),
                                            "actual": _clip(div.get("actual"), 40)} if div else None)}
    return out  # no hidden/fuzz inputs exist in the DB; only classes and a short divergence


def _latest_attempt(ctx: ToolContext) -> dict:
    a = ctx.session.exec(select(Attempt).where(Attempt.user_id == ctx.user_id,
                                               Attempt.problem_slug == ctx.thread.problem_slug)
                         .order_by(desc(Attempt.id))).first()
    if a is None:
        return {"available": False, "note": "no attempts on this problem yet"}
    return attempt_summary(ctx.session, a)


def run_analysis(ctx: ToolContext, a: RunAnalysisArgs) -> dict:
    if a.analysis == "latest_attempt":
        return _latest_attempt(ctx)
    consent = ctx.session.get(ProfileConsent, ctx.user_id)
    if not (consent and consent.granted):
        return {"available": False, "note": "the learner has not allowed access to their LeetCode profile"}
    docs = profile_service.retrieve_evidence(ctx.session, ctx.user_id,
                                             a.question or "strengths weaknesses topics languages activity", k=8)
    if not docs:
        return {"available": False, "note": "no LeetCode profile has been synced"}
    return {"available": True, "evidence": [{"section": d["metadata"].get("section"),
                                              "title": d["metadata"].get("title"), "text": _clip(d["text"], 500)}
                                             for d in docs[:6]]}


# ------------------------------------------------------------------------------------------------- tool: get_hint
def get_hint(ctx: ToolContext, a: GetHintArgs) -> dict:
    svc = HintStateService(ctx.session)
    slug = ctx.thread.problem_slug
    allowed = svc.allowed_level(ctx.user_id, slug)
    level = a.level or min(allowed, svc.max_level_given(ctx.user_id, slug) + 1, 4)
    out: dict = {"allowed_level": allowed, "requested_level": level, "next_requirement": requirements_text(allowed + 1)}
    if level > allowed:
        return {**out, "locked": True, "text": None, "requirement": requirements_text(level)}
    provider = providers.hint_service()
    text = provider(ctx.user_id, slug, level, {"language": ctx.language}) if provider else None
    if text:
        svc.record_hint(ctx.user_id, slug, level)
    return {**out, "locked": False, "text": text}


# ------------------------------------------------------------------------------------------ tool: explain_concept
def explain_concept(ctx: ToolContext, a: ExplainConceptArgs) -> dict:
    provider = providers.concept_service()
    text = provider(a.concept, ctx.language) if provider else None
    if text is None:
        prompt = (f"Explain the programming concept '{a.concept}' to a beginner in under 120 words, in "
                  f"{ctx.language}. Do not write code that solves any specific problem.")
        try:
            text = answerer.llm_complete(prompt)
        except Exception:  # noqa: BLE001
            text = None
    return {"concept": a.concept, "explanation": text, "available": bool(text)}


TOOLS: dict[str, tuple[type[_Args], Callable[[ToolContext, Any], dict]]] = {
    "get_history": (GetHistoryArgs, get_history),
    "run_analysis": (RunAnalysisArgs, run_analysis),
    "get_hint": (GetHintArgs, get_hint),
    "explain_concept": (ExplainConceptArgs, explain_concept),
}


def call_tool(name: str, raw_args: dict | None, ctx: ToolContext) -> dict:
    """Validate and run one tool. Returns {"tool", "ok": bool, "data"|"error"}; never raises."""
    if name not in TOOLS:
        return {"tool": name, "ok": False, "error": "unknown tool"}
    model, fn = TOOLS[name]
    try:
        args = model(**(raw_args or {}))
    except ValidationError as e:
        return {"tool": name, "ok": False, "error": "invalid arguments: " + "; ".join(
            f"{'.'.join(map(str, x['loc']))}: {x['type']}" for x in e.errors()[:3])}
    try:
        return {"tool": name, "ok": True, "data": fn(ctx, args)}
    except Exception as e:  # noqa: BLE001  (a failing tool must not break the chat)
        return {"tool": name, "ok": False, "error": type(e).__name__}
