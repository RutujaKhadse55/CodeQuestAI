import time
from collections import defaultdict, deque

from fastapi import Header, Request

from . import config
from .contracts.enums import ErrorCode
from .errors import ApiError

_hits: dict[str, deque] = defaultdict(deque)


def reset_rate_limits() -> None:
    _hits.clear()


def require_token(x_api_token: str = Header(default="")) -> None:
    if x_api_token != config.API_TOKEN:
        raise ApiError(ErrorCode.UNAUTHORIZED, "missing or invalid X-API-Token")


def rate_limit(request: Request, x_api_token: str = Header(default="")) -> None:
    """Sliding 60 s window per token+client (in-memory, single process)."""
    key = f"{x_api_token}|{request.client.host if request.client else '-'}"
    now, q = time.monotonic(), _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= config.RATE_LIMIT_PER_MIN:
        raise ApiError(ErrorCode.RATE_LIMITED, "too many requests")
    q.append(now)
