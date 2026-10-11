"""Disk cache for synthesized audio, keyed by sha256(text, lang, voice). Directory data/tts_cache (git-ignored)."""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path


def cache_dir() -> Path:
    return Path(os.getenv("TTS_CACHE_DIR", "./data/tts_cache"))


def key(text: str, lang: str, voice: str) -> str:
    return hashlib.sha256(f"{lang}\x00{voice}\x00{text}".encode()).hexdigest()


def get(k: str) -> bytes | None:
    p = cache_dir() / f"{k}.mp3"
    try:
        return p.read_bytes() if p.is_file() else None
    except OSError:
        return None


def put(k: str, audio: bytes) -> None:
    try:
        d = cache_dir()
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{k}.mp3").write_bytes(audio)
    except OSError:
        pass


def clear() -> None:
    """Content-keyed (no per-user data), so clearing is always safe."""
    shutil.rmtree(cache_dir(), ignore_errors=True)
