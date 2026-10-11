import importlib
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")  # before any app import

import pytest
from fastapi.testclient import TestClient

H = {"X-API-Token": "change-me"}


def _docker_ok() -> bool:
    import shutil
    import subprocess
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=20).returncode == 0
    except Exception:
        return False


DOCKER = _docker_ok()
needs_sandbox = pytest.mark.skipif(not DOCKER, reason="Docker daemon not available")


@pytest.fixture()
def real_client(monkeypatch):
    """Real routers (MOCK=0) on a fresh in-memory DB."""
    monkeypatch.setenv("MOCK", "0")
    from sqlmodel import SQLModel
    from app import config, db, deps, main
    importlib.reload(config)
    importlib.reload(main)
    SQLModel.metadata.drop_all(db.engine)
    deps.reset_rate_limits()
    with TestClient(main.app) as c:
        yield c
