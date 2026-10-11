"""POST /explain {attempt_id, lang, user_id?} -> {text, attempt_id}: plain-language explanation of an attempt.

Facts come from the stored attempt summary only (no code, no hidden inputs) via a NeutralMessage; wording is rendered
in en/hi/mr with the learner's style when a learner model is registered; the Guard is re-run on LLM wording.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from .. import providers
from ..ai.explain.neutral import from_summary
from ..ai.explain.render import render
from ..auth import resolve_user, user_token_header
from ..chat.tools import attempt_summary
from ..contracts.enums import ErrorCode
from ..db.models_core import Attempt
from ..deps import get_session
from ..errors import ApiError

router = APIRouter()


class ExplainRequest(BaseModel):
    attempt_id: int
    lang: str | None = "en"
    user_id: str | None = None


def owned_attempt(session: Session, attempt_id: int, user_id: str | None, token: str) -> tuple[str, Attempt]:
    probe = session.get(Attempt, attempt_id)
    uid = resolve_user(session, user_id or (probe.user_id if probe else None), token)
    if probe is None or probe.user_id != uid:
        raise ApiError(ErrorCode.FORBIDDEN, "no access to this attempt")
    return uid, probe


def _style(uid: str) -> dict | None:
    lm = providers.learner_model()
    try:
        return lm.style(uid) if lm else None
    except Exception:  # noqa: BLE001
        return None


@router.post("/explain")
def explain(req: ExplainRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    uid, a = owned_attempt(session, req.attempt_id, req.user_id, token)
    msg = from_summary(attempt_summary(session, a))
    return {"text": render(msg, req.lang or "en", _style(uid)), "attempt_id": a.id}
