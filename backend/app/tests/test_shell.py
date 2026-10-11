import importlib

import pytest
from fastapi.testclient import TestClient

H = {"X-API-Token": "change-me"}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("MOCK", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    from app import config, deps, main
    importlib.reload(config)
    importlib.reload(main)
    deps.reset_rate_limits()
    with TestClient(main.app) as c:
        yield c


def test_health_requires_token(client):
    assert client.get("/health").status_code == 401
    assert client.get("/health").json()["code"] == "UNAUTHORIZED"
    assert client.get("/health", headers=H).json() == {"status": "ok"}


def test_mock_analyze_matches_contract_and_hides_fuzz(client):
    r = client.post("/analyze", headers=H, json={})
    assert r.status_code == 200
    body = r.json()
    assert body["verified"] == "oracle-verified"
    for t in body["results"]:
        if t["kind"] == "fuzz":
            assert t["input"] is None and t["expected"] is None and t["actual"] is None


def test_mock_endpoints(client):
    assert client.post("/users", headers=H).json()["user_id"]
    assert client.post("/hint", headers=H, json={}).json()["guard"]["passed"] is True
    assert "mastery" in client.get("/dashboard/u1", headers=H).json()


def test_rate_limit(client, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "RATE_LIMIT_PER_MIN", 3)
    codes = [client.get("/health", headers=H).status_code for _ in range(5)]
    assert codes[:3] == [200] * 3 and codes[3] == 429
    assert client.get("/health", headers=H).json()["code"] == "RATE_LIMITED"


def _problem(lang):
    return {"slug": "sum-of-squares-of-special-elements", "title": "Sum of Squares of Special Elements",
            "difficulty": "Easy", "tags": [], "statement_text": "s", "examples": [],
            "constraints_text": "", "lang_selected": lang, "content_hash": "h"}


def test_capture_python_supported_other_language_explanation_only(client):
    ok = client.post("/problems/capture", headers=H, json=_problem("python3")).json()
    assert ok["supported"] is True
    java = client.post("/problems/capture", headers=H, json=_problem("java")).json()
    assert java["supported"] is False and java["reason"] == "UNSUPPORTED_LANGUAGE"
