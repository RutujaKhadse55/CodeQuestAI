"""POST /tts -> {audio_base64, mime, cached, fallback?, credits}. 200 with fallback="browser" when no audio."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from ..agents.voice import voice_agent
from ..auth import resolve_user, user_token_header
from ..contracts.enums import ErrorCode
from ..deps import get_session
from ..errors import ApiError

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    lang: str = "en"
    user_id: str | None = None


@router.post("/tts")
def tts(req: TTSRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    if not req.text.strip():
        raise ApiError(ErrorCode.VALIDATION_ERROR, "text is required")
    if len(req.text) > voice_agent.MAX_CHARS:
        raise ApiError(ErrorCode.VALIDATION_ERROR, f"text longer than {voice_agent.MAX_CHARS} characters")
    uid = resolve_user(session, req.user_id, token)
    return voice_agent.tts(req.text, req.lang, uid)


@router.post("/stt")
def stt():
    raise ApiError(ErrorCode.UPSTREAM_FAILED, "speech-to-text is not configured; use browser recognition")
