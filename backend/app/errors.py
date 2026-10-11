from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .contracts.enums import ErrorCode
from .i18n_errors import localized, pick_lang

_STATUS = {
    ErrorCode.UNAUTHORIZED: 401, ErrorCode.FORBIDDEN: 403, ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.RATE_LIMITED: 429, ErrorCode.CODE_REJECTED: 400, ErrorCode.HINT_LOCKED: 423,
    ErrorCode.UNSUPPORTED_PROBLEM: 422, ErrorCode.UNSUPPORTED_LANGUAGE: 422,
    ErrorCode.CREDIT_CAP_REACHED: 429, ErrorCode.UPSTREAM_FAILED: 502,
}


class ApiError(Exception):
    """Raise anywhere; rendered as {code, message, message_key, localized, ...extra}."""

    def __init__(self, code: ErrorCode, message: str | None = None, **extra):
        self.code, self.message, self.extra = code, message, extra


def _body(request: Request, code: str, message: str | None, **extra) -> dict:
    lang = pick_lang(request.headers.get("x-lang"), request.headers.get("accept-language"))
    return {"code": code, "message": message, "message_key": f"errors.{code}",
            "localized": localized(code, lang), **extra}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(request: Request, e: ApiError):
        return JSONResponse(_body(request, e.code.value, e.message, **e.extra), status_code=_STATUS[e.code])

    @app.exception_handler(HTTPException)
    async def _http(request: Request, e: HTTPException):
        code = "UPSTREAM_FAILED" if e.status_code >= 500 else "VALIDATION_ERROR"
        return JSONResponse(_body(request, code, str(e.detail)), status_code=e.status_code)

    @app.exception_handler(RequestValidationError)
    async def _val(request: Request, e: RequestValidationError):
        errs = [{"loc": list(x["loc"]), "msg": x["msg"]} for x in e.errors()[:5]]
        return JSONResponse(_body(request, "VALIDATION_ERROR", "invalid request", errors=errs), status_code=422)
