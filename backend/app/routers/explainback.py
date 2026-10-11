"""POST /explainback {attempt_id, transcript, lang, user_id?} -> {score, feedback, passed}.

The rubric is built from the attempt's stored mistake class. On pass, Mastery.release_pending applies the deferred
mastery update of a copy-flagged attempt (MasteryService, ownership re-checked there).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from ..ai.rubric.explainback_score import RubricScorerImpl, default_rubric, pass_score
from ..auth import user_token_header
from ..db.models_core import DiagnosisRow
from ..deps import get_session
from ..mastery.service import MasteryService
from .explain import owned_attempt

router = APIRouter()


class ExplainBackRequest(BaseModel):
    attempt_id: int
    transcript: str = Field(max_length=6000)
    lang: str | None = "en"
    user_id: str | None = None


@router.post("/explainback")
def explainback(req: ExplainBackRequest, session: Session = Depends(get_session),
                token: str = Depends(user_token_header)):
    uid, a = owned_attempt(session, req.attempt_id, req.user_id, token)
    d = session.exec(select(DiagnosisRow).where(DiagnosisRow.attempt_id == a.id)).first()
    rubric = default_rubric(d.mistake_class if d else None)
    score, feedback = RubricScorerImpl().score(req.transcript, rubric, req.lang or "en")
    passed = score >= pass_score(rubric)
    if passed:
        MasteryService(session).release_pending(uid, a.id)
    return {"score": score, "feedback": feedback, "passed": passed}
