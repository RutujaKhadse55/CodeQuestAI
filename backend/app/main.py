import importlib
import logging
import pkgutil
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config, db, errors, routers
from .deps import rate_limit, require_token


log = logging.getLogger("codequest")
MAX_BODY_BYTES = 2_000_000  # code is capped at 20k chars; this stops oversized bodies before they are parsed


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.create_all()  # no migrations (plan §3.1 rule 5)
    from .wiring import register_all
    register_all()
    if not config.MOCK and config.API_TOKEN in ("", "change-me"):
        log.warning("API_TOKEN is the default 'change-me': set a real token before exposing this backend")
    if config.SANDBOX_MODE == "remote" and config.SANDBOX_TOKEN == "sandbox-dev-token":
        log.warning("SANDBOX_TOKEN is the default value: set SANDBOX_TOKEN in the environment")
    yield


app = FastAPI(title="CodeQuest AI", lifespan=lifespan,
              dependencies=[Depends(require_token), Depends(rate_limit)])
errors.install(app)


@app.middleware("http")
async def limit_body(request, call_next):
    try:
        size = int(request.headers.get("content-length", "0"))
    except ValueError:
        size = 0
    if size > MAX_BODY_BYTES:
        return JSONResponse({"code": "VALIDATION_ERROR", "message": "request body too large",
                             "message_key": "errors.VALIDATION_ERROR"}, status_code=413)
    return await call_next(request)


app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_origin_regex=config.CORS_ORIGIN_REGEX,
                   allow_methods=["*"], allow_headers=["*"])

# MOCK=1: canned example responses are mounted FIRST so they win over real routers.
if config.MOCK:
    from .mock import router as mock_router
    app.include_router(mock_router)

# FEATURE_DEV_UI=1: manual test page for the chat + consent flow at /dev/ (static files are not behind the API token;
# every API call the page makes is). Off by default; never enable on a shared deployment.
if config.FEATURE_DEV_UI:
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    _root = Path(__file__).resolve()
    _fixtures = _root.parents[2] / "fixtures" / "lc"
    if _fixtures.is_dir():
        app.mount("/dev/fixtures", StaticFiles(directory=_fixtures), name="dev-fixtures")
    app.mount("/dev", StaticFiles(directory=_root.parent / "static", html=True), name="dev-ui")

# Router autoload: every routers/*.py exposing `router` is mounted (plan §3.1 rule 4).
for m in pkgutil.iter_modules(routers.__path__):
    mod = importlib.import_module(f"{routers.__name__}.{m.name}")
    if hasattr(mod, "router"):
        app.include_router(mod.router)
