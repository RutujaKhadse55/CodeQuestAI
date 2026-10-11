import json

from fastapi import APIRouter, Depends
from sqlmodel import Session, desc, select

from ..db.models_core import Attempt, ConceptMastery, DiagnosisRow, UserMistakeCount
from ..deps import get_session

router = APIRouter()


@router.get("/dashboard/{user_id}")
def dashboard(user_id: str, session: Session = Depends(get_session)):
    """v1: mastery per concept, mistake counts, recent diagnoses, verified breakdown. (v2 adds profile/credits.)"""
    mastery = {m.concept: m.rating for m in session.exec(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)).all()}
    mistakes = {m.mistake_class: m.count for m in session.exec(
        select(UserMistakeCount).where(UserMistakeCount.user_id == user_id)).all()}
    attempts = session.exec(select(Attempt).where(Attempt.user_id == user_id).order_by(desc(Attempt.id))).all()
    by_attempt = {a.id: a for a in attempts}
    recent = []
    if by_attempt:
        diags = session.exec(select(DiagnosisRow).where(DiagnosisRow.attempt_id.in_(list(by_attempt)))
                             .order_by(desc(DiagnosisRow.id)).limit(10)).all()
        for d in diags:
            a = by_attempt[d.attempt_id]
            recent.append({"attempt_id": a.id, "problem_slug": a.problem_slug, "mistake_class": d.mistake_class,
                           "failure_class": d.failure_class, "confidence": d.confidence,
                           "created_at": a.created_at.isoformat(),
                           "divergence": json.loads(d.divergence_json) if d.divergence_json else None})
    verified = {"oracle-verified": 0, "unverified": 0}
    for a in attempts:
        verified[a.verified] = verified.get(a.verified, 0) + 1
    return {"user_id": user_id, "mastery": mastery, "mistakes": mistakes, "recent": recent, "verified": verified,
            "attempts": len(attempts), "solved": len({a.problem_slug for a in attempts if a.passed_all})}
