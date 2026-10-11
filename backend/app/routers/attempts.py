from fastapi import APIRouter, Depends
from sqlmodel import Session, desc, select

from ..db.models_core import Attempt
from ..deps import get_session
from ..engine.hint_state import HintStateService, requirements_text

router = APIRouter()


@router.get("/attempts/{user_id}")
def list_attempts(user_id: str, problem_slug: str | None = None, limit: int = 20,
                  session: Session = Depends(get_session)):
    q = select(Attempt).where(Attempt.user_id == user_id)
    if problem_slug:
        q = q.where(Attempt.problem_slug == problem_slug)
    rows = session.exec(q.order_by(desc(Attempt.id)).limit(min(limit, 100))).all()
    return [{"attempt_id": a.id, "problem_slug": a.problem_slug, "passed_all": a.passed_all,
             "verified": a.verified, "copy_flagged": a.copy_flagged, "created_at": a.created_at.isoformat()}
            for a in rows]  # code and fuzz seed are intentionally not exposed


@router.get("/hint-state/{user_id}/{problem_slug}")
def hint_state(user_id: str, problem_slug: str, session: Session = Depends(get_session)):
    """Used by AI's /hint router (and the UI) to learn which tier is unlocked and why the next is locked."""
    svc = HintStateService(session)
    attempts, secs = svc.stats(user_id, problem_slug)
    allowed = svc.allowed_level(user_id, problem_slug)
    return {"allowed_level": allowed, "max_level_given": svc.max_level_given(user_id, problem_slug),
            "attempts_counted": attempts, "elapsed_s": int(secs),
            "next_requirement": requirements_text(allowed + 1)}
