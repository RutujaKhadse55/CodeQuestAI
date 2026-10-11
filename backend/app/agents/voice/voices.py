"""Per-language ElevenLabs voice ids. Override via env ELEVENLABS_VOICE_<LANG> (en/hi/mr). The multilingual model
speaks all three; the default ids are placeholders [NEEDS VERIFICATION against the account's voice library]."""
import os

DEFAULT_VOICES = {"en": "21m00Tcm4TlvDq8ikWAM", "hi": "21m00Tcm4TlvDq8ikWAM", "mr": "21m00Tcm4TlvDq8ikWAM"}


def model_id() -> str:
    return os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")


def voice_for(lang: str | None) -> str:
    lang = (lang or "en").lower()[:2]
    lang = lang if lang in DEFAULT_VOICES else "en"
    return os.getenv(f"ELEVENLABS_VOICE_{lang.upper()}") or DEFAULT_VOICES[lang]
