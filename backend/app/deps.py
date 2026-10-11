import hmac
import time
from collections import defaultdict, deque

from fastapi import Header, Request

from sqlmodel import Session

from . import config, db
from .contracts.enums import ErrorCode
from .errors import ApiError

_hits: dict[str, deque] = defaultdict(deque)


def reset_rate_limits() -> None:
    _hits.clear()


def _token(x_api_token: str, authorization: str) -> str:
    """X-API-Token (curl/smoke) or `Authorization: Bearer` (the extension's API client)."""
    if x_api_token:
        return x_api_token
    return authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""


def require_token(x_api_token: str = Header(default=""), authorization: str = Header(default="")) -> None:
    if not hmac.compare_digest(_token(x_api_token, authorization).encode(), config.API_TOKEN.encode()):  # constant-time
        raise ApiError(ErrorCode.UNAUTHORIZED, "missing or invalid X-API-Token")


def rate_limit(request: Request, x_api_token: str = Header(default=""), authorization: str = Header(default="")) -> None:
    """Sliding 60 s window per token+client (in-memory, single process)."""
    key = f"{_token(x_api_token, authorization)}|{request.client.host if request.client else '-'}"
    now, q = time.monotonic(), _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= config.RATE_LIMIT_PER_MIN:
        raise ApiError(ErrorCode.RATE_LIMITED, "too many requests")
    q.append(now)


def get_session():
    with Session(db.engine) as session:
        yield session
