from datetime import datetime, timedelta, timezone

from app.agents.nudge.nudge_agent import compute_nudge
from app.db.models_core import Attempt, HabitEvent

NOW = datetime(2026, 1, 10, tzinfo=timezone.utc)


def att(i, passed=False, paste=0, days=0, slug="two-sum"):
    return Attempt(id=i, user_id="u", problem_slug=slug, code="x", passed_all=passed, paste_chars=paste,
                   created_at=NOW - timedelta(days=days))


def test_stuck():
    n = compute_nudge([att(3), att(2), att(1)], [], {1: "boundary", 2: "boundary", 3: "boundary"}, now=NOW)
    assert n["kind"] == "stuck" and "boundary" in n["text"]


def test_paste_heavy_and_hindi():
    n = compute_nudge([att(2, True, 500), att(1, True, 300)], [], {}, "hi", now=NOW)
    assert n["kind"] == "paste_heavy" and n["lang"] == "hi"


def test_idle_and_none():
    assert compute_nudge([att(1, True, days=5)], [], {}, now=NOW)["kind"] == "idle"
    assert compute_nudge([att(1, True)], [], {}, now=NOW) is None
    ev = HabitEvent(user_id="u", kind="run", created_at=NOW - timedelta(days=9))
    assert compute_nudge([], [ev], {}, now=NOW)["kind"] == "idle"
    assert compute_nudge([], [], {}, now=NOW) is None


def test_route():
    from fastapi.testclient import TestClient
    from app import config
    from app.main import app
    with TestClient(app) as c:
        r = c.get("/nudge/nobody", headers={"X-API-Token": config.API_TOKEN})
    assert r.status_code == 200 and r.json()["nudge"] is None
