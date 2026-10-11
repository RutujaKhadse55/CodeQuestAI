"""Per-learner identity. The API token proves the CLIENT; the user token proves WHICH learner (plan §5.4, spec §7).

`POST /users` returns a `user_token`. When a request carries `X-User-Token`, the learner id is DERIVED from it
server-side and a conflicting user_id in the body/query is rejected (FORBIDDEN). With REQUIRE_USER_TOKEN=1 the
header is mandatory. Never take a user id from model/tool arguments.
"""
import hashlib
import secrets

from fastapi import Header
from sqlmodel import Session

from . import config
from .contracts.enums import ErrorCode
from .db.models_core import ApiToken
from .errors import ApiError


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_user_token(session: Session, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    session.add(ApiToken(token_hash=_hash(token), user_id=user_id))
    session.commit()
    return token


def user_from_token(session: Session, token: str) -> str | None:
    if not token:
        return None
    row = session.get(ApiToken, _hash(token))
    return row.user_id if row else None


def resolve_user(session: Session, claimed: str | None, x_user_token: str = "") -> str:
    """The authenticated learner id for this request."""
    uid = user_from_token(session, x_user_token)
    if x_user_token and uid is None:
        raise ApiError(ErrorCode.UNAUTHORIZED, "invalid X-User-Token")
    if config.REQUIRE_USER_TOKEN and uid is None:
        raise ApiError(ErrorCode.UNAUTHORIZED, "X-User-Token required")
    if uid is not None:
        if claimed and claimed != uid:
            raise ApiError(ErrorCode.FORBIDDEN, "user_id does not match the authenticated learner")
        return uid
    if not claimed:
        raise ApiError(ErrorCode.VALIDATION_ERROR, "user_id is required")
    return claimed


def user_token_header(x_user_token: str = Header(default="")) -> str:
    return x_user_token
