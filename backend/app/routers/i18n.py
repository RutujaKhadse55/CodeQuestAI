"""POST /i18n/translate {text, lang} (guarded; untranslated fallback) and GET /i18n/voice-text (symbols to words)."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ..ai.i18n.detect import detect
from ..ai.i18n.translate import translate_detailed
from ..ai.i18n.voice_text import voice_text

router = APIRouter()


class TranslateRequest(BaseModel):
    text: str = Field(max_length=6000)
    lang: str = "hi"


@router.post("/i18n/translate")
def translate(req: TranslateRequest):
    text, translated, guard = translate_detailed(req.text, req.lang)
    return {"text": text, "lang": req.lang, "translated": translated, "guard": guard.model_dump()}


@router.get("/i18n/voice-text")
def voice(text: str = Query(max_length=6000), lang: str = "en"):
    return {"text": voice_text(text, lang), "lang": lang}


@router.get("/i18n/detect")
def detect_language(text: str = Query(max_length=2000)):
    return detect(text)
