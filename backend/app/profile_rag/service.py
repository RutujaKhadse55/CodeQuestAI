"""Orchestration for the LeetCode profile RAG: sync (fetch + index + snapshot), ask, status, delete."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

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


def _snapshot_file(username: str) -> Path:
    return Path(config.PROFILE_SNAPSHOT_DIR) / f"profile_{username}.json"


def _write_snapshot(profile: dict) -> str | None:
    """Spec §11: a JSON snapshot is written (git-ignored under backend/data). Failure to write is not fatal."""
    try:
        path = _snapshot_file(profile["username"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(profile, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return str(path)
    except OSError:
        return None


def _remove_snapshot_file(session: Session, snap: LeetCodeProfileSnapshot) -> None:
    from sqlmodel import select
    others = session.exec(select(LeetCodeProfileSnapshot).where(
        LeetCodeProfileSnapshot.username == snap.username, LeetCodeProfileSnapshot.user_id != snap.user_id)).first()
    if others is None:  # another learner may have synced the same public username
        try:
            os.remove(_snapshot_file(snap.username))
        except OSError:
            pass


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
            "snapshot_path": _write_snapshot(profile),
            "section_status": profile.get("section_status", {}), "warnings": profile.get("fetch_warnings", []),
            "summary": summarize(profile)}


def ask(session: Session, user_id: str, question: str, k: int = 16) -> dict:
    snap = session.get(LeetCodeProfileSnapshot, user_id)
    if snap is None:
        raise ApiError(ErrorCode.VALIDATION_ERROR, "no LeetCode profile synced yet; call /profile/sync first")
    hits = _store().search(user_id, question, k=k)
    return {**answerer.answer_question(snap.username, question, hits), "username": snap.username}


def retrieve_evidence(session: Session, user_id: str, question: str, k: int = 8) -> list[dict]:
    """Evidence documents for ONE authenticated learner (never by LeetCode username alone). [] if not synced."""
    if session.get(LeetCodeProfileSnapshot, user_id) is None:
        return []
    return _store().search(user_id, question, k=k)


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
        _remove_snapshot_file(session, snap)
    return {"deleted_documents": removed, "deleted_snapshot": snap is not None}
