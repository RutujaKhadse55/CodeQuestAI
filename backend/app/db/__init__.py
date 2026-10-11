"""DB bootstrap. Per-owner model files are imported so create_all() sees every table."""
import os

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from .. import config
from . import models_agents, models_ai, models_core  # noqa: F401

if config.DATABASE_URL.startswith("sqlite:///") and ":memory:" not in config.DATABASE_URL:
    os.makedirs(os.path.dirname(config.DATABASE_URL.replace("sqlite:///", "")) or ".", exist_ok=True)

_kw = {"poolclass": StaticPool} if ":memory:" in config.DATABASE_URL else {}
engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False}, **_kw)


def create_all() -> None:
    SQLModel.metadata.create_all(engine)
