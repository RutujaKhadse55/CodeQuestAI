from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .contracts.enums import ErrorCode

_STATUS = {
    ErrorCode.UNAUTHORIZED: 401, ErrorCode.FORBIDDEN: 403, ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.RATE_LIMITED: 429, ErrorCode.CODE_REJECTED: 400, ErrorCode.HINT_LOCKED: 423,
    ErrorCode.UNSUPPORTED_PROBLEM: 422, ErrorCode.UNSUPPORTED_LANGUAGE: 422,
    ErrorCode.CREDIT_CAP_REACHED: 429, ErrorCode.UPSTREAM_FAILED: 502,
}


class ApiError(Exception):
    """Raise anywhere; rendered as the common error body {code, message, ...extra}."""

    def __init__(self, code: ErrorCode, message: str | None = None, **extra):
        self.code, self.message, self.extra = code, message, extra


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(_: Request, e: ApiError):
        return JSONResponse({"code": e.code.value, "message": e.message, **e.extra},
                            status_code=_STATUS[e.code])

    @app.exception_handler(HTTPException)
    async def _http(_: Request, e: HTTPException):
        code = "UPSTREAM_FAILED" if e.status_code >= 500 else "VALIDATION_ERROR"
        return JSONResponse({"code": code, "message": str(e.detail)}, status_code=e.status_code)

    @app.exception_handler(RequestValidationError)
    async def _val(_: Request, e: RequestValidationError):
        errs = [{"loc": list(x["loc"]), "msg": x["msg"]} for x in e.errors()[:5]]
        return JSONResponse({"code": "VALIDATION_ERROR", "message": "invalid request", "errors": errs},
                            status_code=422)
