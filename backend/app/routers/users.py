import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session, delete, select

from .. import providers
from ..db.models_core import (ApiToken, Attempt, ConceptMastery, DiagnosisRow, HabitEvent, HintState,
                              ChatMessage, ChatThread, LeetCodeProfileSnapshot, ProfileConsent, TestResultRow, User,
                              UserMistakeCount, UserSettings)
from ..auth import issue_user_token
from ..deps import get_session
from ..profile_rag import service as profile_rag

router = APIRouter()


@router.post("/users")
def create_user(session: Session = Depends(get_session)):
    user = User(user_id=uuid.uuid4().hex)
    session.add(user)
    session.commit()
    # user_token authenticates THIS learner on chat/profile endpoints (X-User-Token); shown once, store it client-side
    return {"user_id": user.user_id, "user_token": issue_user_token(session, user.user_id)}


@router.delete("/users/{user_id}/data")
def delete_user_data(user_id: str, session: Session = Depends(get_session)):
    """Delete-all: every SQL row for the learner, then Agents'/AI's registered hooks (Chroma memory, TTS cache,
    profiles). Idempotent. The API uses one shared token, so any token holder can delete any user_id."""
    attempt_ids = list(session.exec(select(Attempt.id).where(Attempt.user_id == user_id)).all())
    deleted: dict[str, int] = {}

    def wipe(name, model, where):
        deleted[name] = session.exec(delete(model).where(where)).rowcount or 0

    if attempt_ids:
        wipe("test_results", TestResultRow, TestResultRow.attempt_id.in_(attempt_ids))
        wipe("diagnoses", DiagnosisRow, DiagnosisRow.attempt_id.in_(attempt_ids))
    wipe("attempts", Attempt, Attempt.user_id == user_id)
    wipe("hint_state", HintState, HintState.user_id == user_id)
    wipe("habit_events", HabitEvent, HabitEvent.user_id == user_id)
    wipe("concept_mastery", ConceptMastery, ConceptMastery.user_id == user_id)
    wipe("user_mistake_counts", UserMistakeCount, UserMistakeCount.user_id == user_id)
    wipe("user_settings", UserSettings, UserSettings.user_id == user_id)
    thread_ids = list(session.exec(select(ChatThread.id).where(ChatThread.user_id == user_id)).all())
    if thread_ids:
        wipe("chat_messages", ChatMessage, ChatMessage.thread_id.in_(thread_ids))
    wipe("chat_threads", ChatThread, ChatThread.user_id == user_id)
    wipe("profile_consents", ProfileConsent, ProfileConsent.user_id == user_id)
    wipe("leetcode_profile_snapshots", LeetCodeProfileSnapshot, LeetCodeProfileSnapshot.user_id == user_id)
    wipe("api_tokens", ApiToken, ApiToken.user_id == user_id)
    wipe("users", User, User.user_id == user_id)
    session.commit()
    hooks = providers.run_deletion_hooks(user_id)
    try:  # LeetCode profile RAG index (Chroma); built-in, not dependent on hook registration
        hooks["profile_rag"] = f"ok ({profile_rag.delete_index(user_id)} documents)"
    except Exception as e:  # noqa: BLE001
        hooks["profile_rag"] = f"error: {type(e).__name__}"
    return {"user_id": user_id, "deleted": deleted, "hooks": hooks}
