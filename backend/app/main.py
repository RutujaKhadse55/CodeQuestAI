import importlib
import pkgutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config, routers

app = FastAPI(title="CodeQuest AI")
app.add_middleware(
    CORSMiddleware, allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"], allow_headers=["*"],
)

# Router autoload: every routers/*.py exposing `router` is mounted (plan §3.1 rule 4).
for m in pkgutil.iter_modules(routers.__path__):
    mod = importlib.import_module(f"{routers.__name__}.{m.name}")
    if hasattr(mod, "router"):
        app.include_router(mod.router)
