from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..deps import get_session
from ..mastery.recommender import recommend

router = APIRouter()


@router.get("/recommend/{user_id}")
def recommend_next(user_id: str, session: Session = Depends(get_session)):
    """Next curated LeetCode problem for the learner's weakest concept (deterministic)."""
    return recommend(session, user_id)
