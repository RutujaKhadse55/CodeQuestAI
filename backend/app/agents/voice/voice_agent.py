"""F-11 voice output. Implements VoiceService.tts; any problem (no key, cap reached, provider down) yields a clean
{"fallback": "browser"} so the extension uses speechSynthesis. Never raises to the caller."""
from __future__ import annotations

import base64
import re

from . import cache, credits, elevenlabs_client, voices

MAX_CHARS = 1500
_SYMBOLS = {"O(n^2)": "O of n squared", "O(n log n)": "O of n log n", "O(log n)": "O of log n", "O(n)": "O of n",
            "O(1)": "O of one", "==": " equals ", "!=": " not equal to ", "<=": " at most ", ">=": " at least ",
            "->": " to ", "=>": " implies ", "&&": " and ", "||": " or ", "`": ""}


def _local_speakable(text: str) -> str:
    for k, v in _SYMBOLS.items():
        text = text.replace(k, v)
    text = re.sub(r"[*_#>~]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def speakable(text: str, lang: str) -> str:
    try:
        from ...ai.i18n import voice_text as mod  # owned by the AI agent; optional
        out = mod.voice_text(text, lang)
        if isinstance(out, str) and out.strip():
            return out
    except Exception:  # noqa: BLE001
        pass
    return _local_speakable(text)


def _fallback(reason: str, user_id: str | None) -> dict:
    return {"fallback": "browser", "reason": reason, "audio_base64": None, "mime": None, "cached": False,
            "credits": credits.snapshot(user_id) if user_id else None}


def tts(text: str, lang: str = "en", user_id: str | None = None) -> dict:
    text = speakable((text or "")[:MAX_CHARS], lang)
    if not text:
        return _fallback("empty", user_id)
    voice = voices.voice_for(lang)
    k = cache.key(text, lang, voice)
    hit = cache.get(k)
    if hit is not None:  # cached audio costs nothing, even past the cap
        return {"audio_base64": base64.b64encode(hit).decode(), "mime": "audio/mpeg", "cached": True,
                "credits": credits.snapshot(user_id) if user_id else None}
    if not elevenlabs_client.api_key():
        return _fallback("no_key", user_id)
    uid = user_id or "anonymous"
    if not credits.can_spend(uid, len(text)):
        return _fallback("CREDIT_CAP_REACHED", uid)
    try:
        audio = elevenlabs_client.synthesize(text, voice, voices.model_id())
    except elevenlabs_client.TTSError:
        return _fallback("provider_error", uid)
    credits.spend(uid, len(text))
    cache.put(k, audio)
    return {"audio_base64": base64.b64encode(audio).decode(), "mime": "audio/mpeg", "cached": False,
            "credits": credits.snapshot(uid)}


def stt(audio: bytes, lang: str | None = None) -> dict:
    return {"error": "stt_not_configured"}


class VoiceAgent:
    """VoiceService Protocol implementation."""
    tts = staticmethod(tts)
    stt = staticmethod(stt)
