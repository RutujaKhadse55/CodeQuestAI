"""GET /nudge/{user_id}?lang= -> {"nudge": {kind, text, lang, problem_slug} | null}. Learner id is derived like other routers."""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..agents.nudge.nudge_agent import nudge_for_user
from ..auth import resolve_user, user_token_header
from ..deps import get_session

router = APIRouter()


@router.get("/nudge/{user_id}")
def nudge(user_id: str, lang: str = "en", session: Session = Depends(get_session),
          token: str = Depends(user_token_header)):
    uid = resolve_user(session, user_id, token)
    return {"user_id": uid, "nudge": nudge_for_user(session, uid, lang)}
