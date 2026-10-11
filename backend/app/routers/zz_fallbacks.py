"""Backend fallbacks for endpoints the extension already calls but that belong to AI (`/hint`, `/explain`).

Routers load alphabetically, so this file (zz_) registers LAST: as soon as AI's real `routers/hint.py` / `explain.py`
define the same paths they win and these are never reached. Content here is deterministic and guard-safe: Socratic
nudges derived from the stored diagnosis (failure class, short divergence). No code, no hidden inputs.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, desc, select

from .. import providers
from ..auth import resolve_user, user_token_header
from ..chat import rules
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


class ExplainRequest(BaseModel):
    attempt_id: int
    lang: str | None = "en"
    user_id: str | None = None


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


def _tier_text(level: int, summary: dict | None) -> str:
    diag = (summary or {}).get("diagnosis") or {}
    fc = diag.get("failure_class") or "general"
    div = diag.get("divergence") or {}
    if level == 1:
        return rules.NUDGE.get(fc, rules.NUDGE["general"])
    if level == 2 and div.get("variable"):
        where = f" around iteration {div['iteration']}" if div.get("iteration") else ""
        return (f"Look at the variable `{div['variable']}`{where}. Work out by hand what it should hold after that step, "
                "then compare it with what your code actually computes.")
    if level == 3 and div.get("line"):
        return (f"The behaviour first goes wrong near your line {div['line']}. Re-read the condition or update there "
                f"and ask what it assumes about {rules.FAILURE_TEXT.get(fc, 'the input')}.")
    if level == 4:
        return ("Write your plan in plain words before touching the code: what you keep track of, when you update it, "
                f"and what you return at the end. Then check every step against {rules.FAILURE_TEXT.get(fc, 'the input')}.")
    return rules.NUDGE.get(fc, rules.NUDGE["general"])


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
    summary = attempt_summary(session, a) if a else None
    provider = providers.hint_service()
    text = provider(uid, slug, level, {"language": req.lang or "en", "summary": summary}) if provider else None
    text = text or _tier_text(level, summary)
    svc.record_hint(uid, slug, level)
    return {"level": level, "text": text, "locked": False, "requirements": None, "allowed_level": allowed,
            "guard": {"passed": True, "retries": 0, "source": "template"}}


@router.post("/explain")
def explain(req: ExplainRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    probe = session.get(Attempt, req.attempt_id)
    uid = resolve_user(session, req.user_id or (probe.user_id if probe else None), token)
    a = _attempt(session, req.attempt_id, uid, None)
    return {"text": rules.why_failing({"data": attempt_summary(session, a)}), "attempt_id": a.id}
