"""Per-user monthly ElevenLabs character meter (JSON file). `snapshot(user_id)` is what providers.register_credits
serves to the dashboard; reaching the cap yields CREDIT_CAP_REACHED semantics (browser-TTS fallback, not an error)."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

_lock = threading.Lock()


def monthly_cap() -> int:
    return int(os.getenv("TTS_MONTHLY_CHAR_CAP", "20000"))


def _file() -> Path:
    return Path(os.getenv("TTS_CREDITS_FILE", "./data/tts_credits.json"))


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _load() -> dict:
    try:
        data = json.loads(_file().read_text("utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    try:
        f = _file()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data), "utf-8")
    except OSError:
        pass


def used(user_id: str) -> int:
    return int(_load().get(_month(), {}).get(user_id, 0))


def remaining(user_id: str) -> int:
    return max(0, monthly_cap() - used(user_id))


def can_spend(user_id: str, chars: int) -> bool:
    return chars <= remaining(user_id)


def spend(user_id: str, chars: int) -> None:
    with _lock:
        m = _load().get(_month(), {})
        m[user_id] = int(m.get(user_id, 0)) + chars
        _save({_month(): m})  # older months are dropped


def snapshot(user_id: str) -> dict:
    u, cap = used(user_id), monthly_cap()
    return {"provider": "elevenlabs", "period": _month(), "used": u, "cap": cap, "remaining": max(0, cap - u),
            "cap_reached": u >= cap}


def delete_user(user_id: str) -> None:
    with _lock:
        data = _load()
        for m in data.values():
            if isinstance(m, dict):
                m.pop(user_id, None)
        _save(data)
