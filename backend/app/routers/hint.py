"""POST /hint: unlock-aware, guarded hint ladder (plan §6 P2). Same request model/response as the zz_ fallback.

Allowed level comes from Backend's HintStateService; a locked level answers 200 with locked=true (HINT_LOCKED
semantics) and the requirement text. Text comes from the crew hint service when one is registered, else from
ai/hints/generate.py (LLM wording + Hint Guard, template fallback). Every text is re-checked by the Hint Guard.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, desc, select

from .. import providers
from ..ai.hints.generate import generate_hint
from ..ai.hints.guard import hint_violation
from ..ai.hints.tiers import template_hint
from ..auth import resolve_user, user_token_header
from ..chat.tools import attempt_summary
from ..contracts.enums import ErrorCode
from ..db.models_core import Attempt
from ..deps import get_session
from ..engine.hint_state import HintStateService, requirements_text
from ..errors import ApiError

router = APIRouter()


class HintRequest(BaseModel):
    problem_slug: str | None = None
    attempt_id: int | None = None
    level: int | None = Field(default=None, ge=1, le=4)
    user_id: str | None = None
    lang: str | None = None


def _attempt(session: Session, attempt_id: int | None, uid: str, slug: str | None) -> Attempt | None:
    if attempt_id is not None:
        a = session.get(Attempt, attempt_id)
        if a is None or a.user_id != uid:
            raise ApiError(ErrorCode.FORBIDDEN, "no access to this attempt")
        return a
    if slug:
        return session.exec(select(Attempt).where(Attempt.user_id == uid, Attempt.problem_slug == slug)
                            .order_by(desc(Attempt.id))).first()
    return None


@router.post("/hint")
def hint(req: HintRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    probe = session.get(Attempt, req.attempt_id) if req.attempt_id is not None else None
    uid = resolve_user(session, req.user_id or (probe.user_id if probe else None), token)
    a = _attempt(session, req.attempt_id, uid, req.problem_slug)
    slug = req.problem_slug or (a.problem_slug if a else None)
    if not slug:
        raise ApiError(ErrorCode.VALIDATION_ERROR, "problem_slug or attempt_id is required")
    svc = HintStateService(session)
    allowed = svc.allowed_level(uid, slug)
    level = req.level or min(allowed, svc.max_level_given(uid, slug) + 1, 4)
    if level > allowed:
        return {"level": level, "text": "", "locked": True, "requirements": requirements_text(level),
                "allowed_level": allowed}
    lang = req.lang or "en"
    summary = attempt_summary(session, a) if a else None
    text, guard = None, None
    provider = providers.hint_service()
    if provider:
        try:
            text = provider(uid, slug, level, {"language": lang, "summary": summary})
        except Exception:  # noqa: BLE001
            text = None
        if text and hint_violation(text, level, {}) is not None:
            text = None
        if text:
            guard = {"passed": True, "retries": 0, "source": "llm"}
    if not text:
        text, g = generate_hint(level, summary, lang)
        guard = g.model_dump()
    if not text:  # defensive: generate_hint never returns empty
        text, guard = template_hint(level, lang=lang), {"passed": True, "retries": 0, "source": "template"}
    svc.record_hint(uid, slug, level)
    return {"level": level, "text": text, "locked": False, "requirements": None, "allowed_level": allowed,
            "guard": guard}
