from fastapi import Header, HTTPException

from . import config


def require_token(x_api_token: str = Header(default="")) -> None:
    if x_api_token != config.API_TOKEN:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED"})

# TODO [BE]: rate limiter
