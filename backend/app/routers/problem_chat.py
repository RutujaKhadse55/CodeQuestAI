"""Problem-understanding chat + profile consent (Backend-owned; behind FEATURE_CHAT).

Flow the extension follows when the learner opens the chat panel:
  1. GET  /chat/consent-info                    -> show the permission dialog
  2. POST /chat/consent {leetcode_username}     -> records consent, fetches + indexes the PUBLIC profile
     (declining = skip this step: chat still works, just not personalised)
  3. POST /chat/threads {problem_slug}          -> new thread about the problem on the page
  4. POST /chat/threads/{id}/messages {content} -> reply (JSON, or SSE with ?stream=true / Accept: text/event-stream)
Identity: with X-User-Token the learner id is derived server-side; a different user_id in the body is FORBIDDEN.
"""
import json

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import Session

from .. import config
from ..auth import resolve_user, user_token_header
from ..chat import service
from ..contracts.enums import ErrorCode
from ..deps import get_session
from ..errors import ApiError

router = APIRouter(prefix="/chat", tags=["problem-chat"])


def _enabled() -> None:
    if not config.FEATURE_CHAT:
        raise ApiError(ErrorCode.UPSTREAM_FAILED, "chat is disabled (set FEATURE_CHAT=1)")


class ConsentRequest(BaseModel):
    user_id: str | None = None
    leetcode_username: str = Field(min_length=1, max_length=40)
    refresh: bool = False


class ThreadRequest(BaseModel):
    user_id: str | None = None
    problem_slug: str = Field(min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=120)
    language: str | None = None


class MessageRequest(BaseModel):
    user_id: str | None = None
    content: str = Field(min_length=1, max_length=1000)
    language: str | None = None


@router.get("/consent-info", dependencies=[Depends(_enabled)])
def consent_info():
    return service.CONSENT_INFO


@router.get("/consent", dependencies=[Depends(_enabled)])
def get_consent(user_id: str | None = None, session: Session = Depends(get_session),
                token: str = Depends(user_token_header)):
    return service.consent_status(session, resolve_user(session, user_id, token))


@router.post("/consent", dependencies=[Depends(_enabled)])
def grant(req: ConsentRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    """The learner allows access to their PUBLIC LeetCode profile; it is fetched and indexed immediately."""
    return service.grant_consent(session, resolve_user(session, req.user_id, token), req.leetcode_username, req.refresh)


@router.delete("/consent", dependencies=[Depends(_enabled)])
def revoke(user_id: str | None = None, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    """Withdraw permission: the stored profile snapshot, its file and its vector index are deleted."""
    return service.revoke_consent(session, resolve_user(session, user_id, token))


@router.post("/threads", dependencies=[Depends(_enabled)])
def new_thread(req: ThreadRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    return service.create_thread(session, resolve_user(session, req.user_id, token), req.problem_slug, req.title,
                                 req.language)


@router.get("/threads", dependencies=[Depends(_enabled)])
def threads(user_id: str | None = None, session: Session = Depends(get_session),
            token: str = Depends(user_token_header)):
    return service.list_threads(session, resolve_user(session, user_id, token))


@router.get("/threads/{thread_id}", dependencies=[Depends(_enabled)])
def thread(thread_id: str, user_id: str | None = None, session: Session = Depends(get_session),
           token: str = Depends(user_token_header)):
    return service.get_thread(session, thread_id, resolve_user(session, user_id, token))


@router.delete("/threads/{thread_id}", dependencies=[Depends(_enabled)])
def remove_thread(thread_id: str, user_id: str | None = None, session: Session = Depends(get_session),
                  token: str = Depends(user_token_header)):
    return service.delete_thread(session, thread_id, resolve_user(session, user_id, token))


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _chunks(text: str, n: int = 6):
    words = text.split(" ")
    for i in range(0, len(words), n):
        yield " ".join(words[i:i + n]) + (" " if i + n < len(words) else "")


@router.post("/threads/{thread_id}/messages", dependencies=[Depends(_enabled)])
def post_message(thread_id: str, req: MessageRequest, request: Request, stream: bool = Query(default=False),
                 session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    uid = resolve_user(session, req.user_id, token)
    result = service.post_message(session, thread_id, uid, req.content, req.language)
    if not stream and "text/event-stream" not in request.headers.get("accept", ""):
        return result
    reply = result["reply"]

    def gen():  # the reply was fully Guard-checked BEFORE any byte is streamed
        yield _sse("meta", {"thread_id": result["thread_id"], "language": reply["language"], "mode": reply["mode"],
                            "tools_used": reply["tools_used"], "personalized": reply["personalized"]})
        for piece in _chunks(reply["content"]):
            yield _sse("token", {"text": piece})
        yield _sse("done", {"message_id": result["message_id"], "guard": reply["guard"], "sources": reply["sources"],
                            "allowed_hint_level": reply["allowed_hint_level"]})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
