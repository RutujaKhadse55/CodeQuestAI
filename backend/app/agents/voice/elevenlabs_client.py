"""Minimal ElevenLabs text-to-speech client (httpx). The key comes from the environment only and is never logged."""
from __future__ import annotations

import os

import httpx

BASE = "https://api.elevenlabs.io/v1"


class TTSError(RuntimeError):
    """Provider failure; the message never contains the key."""


def api_key() -> str:
    return os.getenv("ELEVENLABS_API_KEY", "").strip()


def synthesize(text: str, voice_id: str, model_id: str, timeout: float = 20.0) -> bytes:
    key = api_key()
    if not key:
        raise TTSError("no api key")
    try:
        r = httpx.post(f"{BASE}/text-to-speech/{voice_id}", params={"output_format": "mp3_44100_64"},
                       headers={"xi-api-key": key, "accept": "audio/mpeg"},
                       json={"text": text, "model_id": model_id}, timeout=timeout)
    except httpx.HTTPError as e:
        raise TTSError(f"request failed: {type(e).__name__}") from None
    if r.status_code != 200 or not r.content:
        raise TTSError(f"provider status {r.status_code}")
    return r.content
