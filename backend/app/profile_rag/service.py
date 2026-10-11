"""Orchestration for the LeetCode profile RAG: sync (fetch + index + snapshot), ask, status, delete."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlmodel import Session

from .. import config
from ..contracts.enums import ErrorCode
from ..db.models_core import LeetCodeProfileSnapshot, User
from ..errors import ApiError
from . import answerer, client, store
from .documents import summarize


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _store():
    try:
        return store.get_store()
    except store.RagUnavailable as e:
        raise ApiError(ErrorCode.UPSTREAM_FAILED, f"profile RAG unavailable: {e}")


def snapshot_summary(snap: LeetCodeProfileSnapshot) -> dict:
    return summarize(json.loads(snap.payload_json))


def sync(session: Session, user_id: str, username: str, force: bool = False) -> dict:
    username = username.strip()
    if not client.valid_username(username):
        raise ApiError(ErrorCode.VALIDATION_ERROR, "invalid LeetCode username")
    snap = session.get(LeetCodeProfileSnapshot, user_id)
    if snap and not force and snap.username.lower() == username.lower():
        age = (datetime.now(timezone.utc) - _aware(snap.fetched_at)).total_seconds()
        if age < config.PROFILE_SYNC_MIN_INTERVAL_S:
            return {"status": "cached", "username": snap.username, "documents": snap.docs_indexed,
                    "age_s": int(age), "summary": snapshot_summary(snap)}
    st = _store()
    try:
        profile = client.fetch_profile(username)
    except client.ProfileNotFound as e:
        raise ApiError(ErrorCode.VALIDATION_ERROR, str(e))
    except Exception as e:  # noqa: BLE001  (network / LeetCode API failure)
        raise ApiError(ErrorCode.UPSTREAM_FAILED, f"LeetCode fetch failed: {type(e).__name__}")
    count = st.upsert_profile(user_id, profile)
    if session.get(User, user_id) is None:
        session.add(User(user_id=user_id))
    if snap is None:
        snap = LeetCodeProfileSnapshot(user_id=user_id, username=profile["username"], payload_json="{}")
    snap.username, snap.payload_json = profile["username"], json.dumps(profile, ensure_ascii=False, default=str)
    snap.docs_indexed, snap.fetched_at = count, datetime.now(timezone.utc)
    session.add(snap)
    session.commit()
    return {"status": "synced", "username": snap.username, "documents": count,
            "section_status": profile.get("section_status", {}), "warnings": profile.get("fetch_warnings", []),
            "summary": summarize(profile)}


def ask(session: Session, user_id: str, question: str, k: int = 16) -> dict:
    snap = session.get(LeetCodeProfileSnapshot, user_id)
    if snap is None:
        raise ApiError(ErrorCode.VALIDATION_ERROR, "no LeetCode profile synced yet; call /profile/sync first")
    hits = _store().search(user_id, question, k=k)
    return {**answerer.answer_question(snap.username, question, hits), "username": snap.username}


def status(session: Session, user_id: str) -> dict:
    snap = session.get(LeetCodeProfileSnapshot, user_id)
    if snap is None:
        return {"synced": False}
    return {"synced": True, "username": snap.username, "documents": snap.docs_indexed,
            "fetched_at": _aware(snap.fetched_at).isoformat(), "summary": snapshot_summary(snap)}


def delete_index(user_id: str) -> int:
    """Chroma part of delete-all. Never raises (a missing store means there is nothing to delete)."""
    try:
        return store.get_store().delete_user(user_id)
    except store.RagUnavailable:
        return 0


def delete(session: Session, user_id: str) -> dict:
    removed = delete_index(user_id)
    snap = session.get(LeetCodeProfileSnapshot, user_id)
    if snap:
        session.delete(snap)
        session.commit()
    return {"deleted_documents": removed, "deleted_snapshot": snap is not None}
