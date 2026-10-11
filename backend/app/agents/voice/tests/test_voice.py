import base64

import httpx
import pytest

from app.agents.voice import cache, credits, voice_agent
from app.agents.voice import elevenlabs_client as el


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("TTS_CACHE_DIR", str(tmp_path / "c"))
    monkeypatch.setenv("TTS_CREDITS_FILE", str(tmp_path / "cr.json"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")


class Resp:
    def __init__(self, status=200, content=b"MP3DATA"):
        self.status_code, self.content = status, content


def test_no_key_falls_back():
    r = voice_agent.tts("hello world", "en", "u1")
    assert r["fallback"] == "browser" and r["audio_base64"] is None


def test_synth_cache_and_credits(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "sk-secret")
    calls = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: calls.append(k) or Resp())
    r = voice_agent.tts("hello", "hi", "u1")
    assert base64.b64decode(r["audio_base64"]) == b"MP3DATA" and not r["cached"]
    assert r["credits"]["used"] == 5
    r2 = voice_agent.tts("hello", "hi", "u1")
    assert r2["cached"] and len(calls) == 1
    assert calls[0]["headers"]["xi-api-key"] == "sk-secret"


def test_cap_reached(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    monkeypatch.setenv("TTS_MONTHLY_CHAR_CAP", "10")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: Resp())
    assert "audio_base64" in voice_agent.tts("12345678", "en", "u")
    r = voice_agent.tts("another text", "en", "u")
    assert r["fallback"] == "browser" and r["reason"] == "CREDIT_CAP_REACHED"
    assert credits.snapshot("u")["remaining"] == 2
    credits.delete_user("u")
    assert credits.used("u") == 0


def test_provider_error_is_clean(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: Resp(500, b""))
    assert voice_agent.tts("hi", "en", "u")["fallback"] == "browser"

    def boom(*a, **k):
        raise httpx.ConnectError("x")
    monkeypatch.setattr(httpx, "post", boom)
    assert voice_agent.tts("hi there", "en", "u")["fallback"] == "browser"
    with pytest.raises(el.TTSError):
        el.synthesize("x", "v", "m")


def test_cache_key_varies():
    assert cache.key("a", "en", "v") != cache.key("a", "hi", "v")


def test_register_and_route(monkeypatch):
    from fastapi.testclient import TestClient
    from app import config, providers
    from app.agents import voice
    from app.main import app
    voice.register()
    assert providers.credits("u9")["cap"] > 0
    c = TestClient(app)
    h = {"X-API-Token": config.API_TOKEN}
    r = c.post("/tts", json={"text": "hello", "lang": "en", "user_id": "u9"}, headers=h)
    assert r.status_code == 200 and r.json()["fallback"] == "browser"
    assert c.post("/tts", json={"text": "x" * 5000, "user_id": "u9"}, headers=h).status_code == 422
    assert c.post("/stt", headers=h).status_code == 502
