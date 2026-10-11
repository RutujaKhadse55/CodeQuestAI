import importlib
import pkgutil
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config, db, errors, routers
from .deps import rate_limit, require_token


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.create_all()  # no migrations (plan §3.1 rule 5)
    yield


app = FastAPI(title="CodeQuest AI", lifespan=lifespan,
              dependencies=[Depends(require_token), Depends(rate_limit)])
errors.install(app)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])

# MOCK=1: canned example responses are mounted FIRST so they win over real routers.
if config.MOCK:
    from .mock import router as mock_router
    app.include_router(mock_router)

# Router autoload: every routers/*.py exposing `router` is mounted (plan §3.1 rule 4).
for m in pkgutil.iter_modules(routers.__path__):
    mod = importlib.import_module(f"{routers.__name__}.{m.name}")
    if hasattr(mod, "router"):
        app.include_router(mod.router)
