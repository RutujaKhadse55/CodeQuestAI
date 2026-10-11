import json
from collections import Counter

from fastapi import APIRouter, Depends
from sqlmodel import Session, desc, select

from .. import providers
from ..db.models_core import (Attempt, ConceptMastery, DiagnosisRow, LeetCodeProfileSnapshot,
                              UserMistakeCount)
from ..deps import get_session
from ..mastery.profile import basic_profile
from ..profile_rag.service import snapshot_summary

router = APIRouter()


@router.get("/dashboard/{user_id}")
def dashboard(user_id: str, session: Session = Depends(get_session)):
    """v2: mastery per concept, mistakes + heatmap, recent diagnoses, verified breakdown, learner profile, credits."""
    mastery = {m.concept: m.rating for m in session.exec(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)).all()}
    mistakes = {m.mistake_class: m.count for m in session.exec(
        select(UserMistakeCount).where(UserMistakeCount.user_id == user_id)).all()}
    attempts = session.exec(select(Attempt).where(Attempt.user_id == user_id).order_by(desc(Attempt.id))).all()
    by_attempt = {a.id: a for a in attempts}
    recent, heat = [], Counter()
    if by_attempt:
        diags = session.exec(select(DiagnosisRow).where(DiagnosisRow.attempt_id.in_(list(by_attempt)))
                             .order_by(desc(DiagnosisRow.id))).all()
        for d in diags:
            a = by_attempt[d.attempt_id]
            if d.mistake_class:
                heat[(a.problem_slug, d.mistake_class)] += 1
            if len(recent) < 10:
                recent.append({"attempt_id": a.id, "problem_slug": a.problem_slug,
                               "mistake_class": d.mistake_class, "failure_class": d.failure_class,
                               "confidence": d.confidence, "created_at": a.created_at.isoformat(),
                               "divergence": json.loads(d.divergence_json) if d.divergence_json else None})
    verified = {"oracle-verified": 0, "unverified": 0}
    for a in attempts:
        verified[a.verified] = verified.get(a.verified, 0) + 1
    snap = session.get(LeetCodeProfileSnapshot, user_id)
    model = providers.learner_model()
    profile = model.summary(user_id) if model else basic_profile(session, user_id)
    return {"user_id": user_id, "mastery": mastery, "mistakes": mistakes,
            "heatmap": [{"problem_slug": p, "mistake_class": m, "count": c} for (p, m), c in sorted(heat.items())],
            "recent": recent, "verified": verified, "attempts": len(attempts),
            "solved": len({a.problem_slug for a in attempts if a.passed_all}),
            "profile": profile, "credits": providers.credits(user_id),
            "leetcode": snapshot_summary(snap) if snap else None}
