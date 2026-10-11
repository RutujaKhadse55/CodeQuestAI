"""LeetCode profile RAG endpoints (Backend-owned; behind FEATURE_PROFILE_RAG, default off)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from .. import config
from ..contracts.enums import ErrorCode
from ..deps import get_session
from ..errors import ApiError
from ..profile_rag import service

router = APIRouter(prefix="/profile", tags=["profile-rag"])


class SyncRequest(BaseModel):
    user_id: str
    username: str = Field(min_length=1, max_length=40)
    force: bool = False


class AskRequest(BaseModel):
    user_id: str
    question: str = Field(min_length=1, max_length=500)


def _enabled() -> None:
    if not config.FEATURE_PROFILE_RAG:
        raise ApiError(ErrorCode.UPSTREAM_FAILED, "profile RAG is disabled (set FEATURE_PROFILE_RAG=1)")


@router.post("/sync", dependencies=[Depends(_enabled)])
def sync_profile(req: SyncRequest, session: Session = Depends(get_session)):
    """Fetch the learner's PUBLIC LeetCode profile, index it in Chroma, keep a snapshot. User-triggered; a
    repeat sync for the same username within PROFILE_SYNC_MIN_INTERVAL_S returns the cached snapshot."""
    return service.sync(session, req.user_id, req.username, req.force)


@router.post("/ask", dependencies=[Depends(_enabled)])
def ask_profile(req: AskRequest, session: Session = Depends(get_session)):
    return service.ask(session, req.user_id, req.question)


@router.get("/{user_id}", dependencies=[Depends(_enabled)])
def profile_status(user_id: str, session: Session = Depends(get_session)):
    return service.status(session, user_id)


@router.delete("/{user_id}", dependencies=[Depends(_enabled)])
def delete_profile(user_id: str, session: Session = Depends(get_session)):
    return service.delete(session, user_id)
