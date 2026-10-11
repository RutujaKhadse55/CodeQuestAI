"""Consent, threads and messages for the problem chat. Every function takes the AUTHENTICATED learner id."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlmodel import Session, desc, select

from ..contracts.enums import ErrorCode
from ..contracts.models import LCProblem
from ..db.models_core import (ChatMessage, ChatThread, LCProblemRow, LeetCodeProfileSnapshot, ProfileConsent, User)
from ..errors import ApiError
from ..profile_rag import client as lc_client, service as profile_service
from . import agent
from .lang import LANG_NAMES, detect_lang
from .tools import ToolContext

CONSENT_VERSION = "1"
CONSENT_SCOPE = "leetcode_public_profile"
CONSENT_INFO = {
    "version": CONSENT_VERSION,
    "scope": CONSENT_SCOPE,
    "title": "Allow CodeQuest AI to use your public LeetCode profile?",
    "text": ("To personalise explanations, CodeQuest AI will read the PUBLIC LeetCode profile of the username you "
             "enter: solved counts, languages, topics, activity and streak, recent accepted problems, badges and "
             "contest rating. It does not sign in to LeetCode and cannot see private data or your code there. "
             "The data is stored on this CodeQuest backend, used only to answer your chat questions, and you can "
             "withdraw permission at any time, which deletes it. You can also chat without allowing this."),
    "data_accessed": ["profile overview", "solved statistics", "languages", "topics", "activity/streak",
                      "recent accepted problems", "badges", "contest rating"],
    "not_accessed": ["private submissions", "your LeetCode password or session", "other people's data"],
    "retention": "until you withdraw permission or delete your data",
    "can_revoke": True,
}  # EN only; HI/MR wording is [NEEDS VERIFICATION] by a bilingual reviewer


def now() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------------------------------------------------------ consent
def consent_status(session: Session, user_id: str) -> dict:
    c = session.get(ProfileConsent, user_id)
    snap = session.get(LeetCodeProfileSnapshot, user_id)
    return {"granted": bool(c and c.granted), "scope": CONSENT_SCOPE, "version": CONSENT_VERSION,
            "leetcode_username": c.leetcode_username if c and c.granted else None,
            "granted_at": c.granted_at.isoformat() if c and c.granted_at else None,
            "revoked_at": c.revoked_at.isoformat() if c and c.revoked_at else None,
            "profile_synced": snap is not None,
            "summary": profile_service.snapshot_summary(snap) if (c and c.granted and snap) else None}


def grant_consent(session: Session, user_id: str, leetcode_username: str, force_sync: bool = False) -> dict:
    username = (leetcode_username or "").strip()
    if not lc_client.valid_username(username):
        raise ApiError(ErrorCode.VALIDATION_ERROR, "invalid LeetCode username")
    if session.get(User, user_id) is None:
        session.add(User(user_id=user_id))
    c = session.get(ProfileConsent, user_id) or ProfileConsent(user_id=user_id)
    c.granted, c.leetcode_username, c.granted_at, c.revoked_at = True, username, now(), None
    c.consent_version = CONSENT_VERSION
    session.add(c)
    session.commit()
    sync_error = None
    try:  # permission is recorded first; if LeetCode is down the learner can still chat (unpersonalised)
        profile_service.sync(session, user_id, username, force_sync)
    except ApiError as e:
        sync_error = {"code": e.code.value, "message": e.message}
    out = consent_status(session, user_id)
    out["sync_error"] = sync_error
    return out


def revoke_consent(session: Session, user_id: str) -> dict:
    c = session.get(ProfileConsent, user_id)
    if c:
        c.granted, c.revoked_at = False, now()
        session.add(c)
        session.commit()
    removed = profile_service.delete(session, user_id)  # snapshot row + file + Chroma documents
    return {**consent_status(session, user_id), "deleted": removed}


def is_personalised(session: Session, user_id: str) -> bool:
    c = session.get(ProfileConsent, user_id)
    return bool(c and c.granted and session.get(LeetCodeProfileSnapshot, user_id))


# ------------------------------------------------------------------------------------------------------ threads
def _thread(session: Session, thread_id: str, user_id: str) -> ChatThread:
    t = session.get(ChatThread, thread_id)
    if t is None or t.user_id != user_id:  # missing and foreign look identical: no probing of other learners' ids
        raise ApiError(ErrorCode.FORBIDDEN, "no access to this thread")
    return t


def create_thread(session: Session, user_id: str, problem_slug: str, title: str | None, language: str | None) -> dict:
    row = session.get(LCProblemRow, problem_slug)
    if row is None:
        raise ApiError(ErrorCode.UNSUPPORTED_PROBLEM, "problem not captured; call /problems/capture first")
    if session.get(User, user_id) is None:
        session.add(User(user_id=user_id))
    t = ChatThread(id=uuid.uuid4().hex, user_id=user_id, problem_slug=problem_slug,
                   title=(title or row.title)[:120], language=language if language in LANG_NAMES else "en")
    session.add(t)
    session.commit()
    return thread_view(session, t)


def thread_view(session: Session, t: ChatThread, with_messages: bool = False) -> dict:
    out = {"thread_id": t.id, "problem_slug": t.problem_slug, "title": t.title, "language": t.language,
           "personalized": is_personalised(session, t.user_id), "created_at": t.created_at.isoformat()}
    if with_messages:
        msgs = session.exec(select(ChatMessage).where(ChatMessage.thread_id == t.id).order_by(ChatMessage.id)).all()
        out["messages"] = [{"message_id": m.id, "role": m.role, "content": m.content, "at": m.created_at.isoformat(),
                            "meta": json.loads(m.meta_json) if m.meta_json else None} for m in msgs]
    return out


def list_threads(session: Session, user_id: str) -> list[dict]:
    rows = session.exec(select(ChatThread).where(ChatThread.user_id == user_id).order_by(desc(ChatThread.updated_at))).all()
    return [thread_view(session, t) for t in rows]


def get_thread(session: Session, thread_id: str, user_id: str) -> dict:
    return thread_view(session, _thread(session, thread_id, user_id), with_messages=True)


def delete_thread(session: Session, thread_id: str, user_id: str) -> dict:
    t = _thread(session, thread_id, user_id)
    n = session.exec(select(ChatMessage).where(ChatMessage.thread_id == t.id)).all()
    for m in n:
        session.delete(m)
    session.delete(t)
    session.commit()
    return {"deleted": True, "messages": len(n)}


# ---------------------------------------------------------------------------------------------------- messages
def post_message(session: Session, thread_id: str, user_id: str, content: str, language: str | None,
                 code: str | None = None, code_language: str | None = None) -> dict:
    t = _thread(session, thread_id, user_id)
    row = session.get(LCProblemRow, t.problem_slug)
    if row is None:
        raise ApiError(ErrorCode.UNSUPPORTED_PROBLEM, "problem no longer available")
    um = ChatMessage(thread_id=t.id, role="user", content=content)
    session.add(um)
    session.commit()
    ctx = ToolContext(session=session, user_id=user_id, thread=t, problem_row=row,
                      problem=LCProblem.model_validate_json(row.payload_json), language=t.language)
    reply = agent.respond(ctx, content, language, code=code, code_language=code_language)
    if language is None and reply["language"] != t.language and detect_lang(content, t.language) == reply["language"]:
        t.language = reply["language"]  # the thread follows the language the learner actually writes in
    am = ChatMessage(thread_id=t.id, role="assistant", content=reply["content"],
                     meta_json=json.dumps({k: reply[k] for k in ("mode", "intent", "guard", "tools_used", "sources",
                                                                  "personalized", "language")}))
    t.updated_at = now()
    session.add(am)
    session.add(t)
    session.commit()
    session.refresh(am)
    return {"thread_id": t.id, "user_message_id": um.id, "message_id": am.id, "reply": reply}
