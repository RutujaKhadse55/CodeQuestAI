"""Proactive nudge: deterministic, template-based, safe (no code, no answers, no hidden inputs, no LLM)."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, desc, select

from ...db.models_core import Attempt, DiagnosisRow, HabitEvent

IDLE_DAYS = 3
STUCK_N = 3
PASTE_CHARS = 200

TEMPLATES = {
    "stuck": {"en": "You have hit the same kind of failure ({fc}) {n} times on this problem. Step away from the code, "
                    "write the plan in plain words, then check each step against that failure.",
              "hi": "इस सवाल पर आप एक ही तरह की गलती ({fc}) {n} बार कर चुके हैं। कोड से हटकर योजना सादे शब्दों में लिखें, "
                    "फिर हर चरण को जाँचें।",
              "mr": "या प्रश्नावर तुम्ही एकाच प्रकारची चूक ({fc}) {n} वेळा केली आहे. कोडपासून दूर होऊन योजना साध्या शब्दांत "
                    "लिहा, मग प्रत्येक पायरी तपासा."},
    "idle": {"en": "It has been a few days since your last practice. A single easy problem today keeps the streak alive.",
             "hi": "आपकी पिछली प्रैक्टिस को कुछ दिन हो गए हैं। आज एक आसान सवाल हल करके शुरुआत करें।",
             "mr": "तुमच्या मागील सरावाला काही दिवस झाले आहेत. आज एक सोपा प्रश्न सोडवून सुरुवात करा."},
    "paste_heavy": {"en": "Lately a lot of your code arrived by pasting. Try typing the next solution from your own plan; "
                          "it builds the skill the interview will test.",
                    "hi": "हाल में आपका बहुत सा कोड पेस्ट किया हुआ था। अगला हल अपनी योजना से खुद टाइप करके देखें।",
                    "mr": "अलीकडे तुमचा बराच कोड पेस्ट केलेला होता. पुढचे उत्तर स्वतःच्या योजनेतून टाइप करून पाहा."},
}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def compute_nudge(attempts: list[Attempt], events: list[HabitEvent], failure_by_attempt: dict[int, str | None],
                  lang: str = "en", now: datetime | None = None) -> dict | None:
    """attempts/events: newest first. Priority: stuck > paste_heavy > idle."""
    now = now or datetime.now(timezone.utc)
    lang = lang if lang in ("en", "hi", "mr") else "en"
    if attempts:
        slug = attempts[0].problem_slug
        fails = [a for a in attempts if a.problem_slug == slug and not a.passed_all][:STUCK_N + 2]
        if attempts[0].passed_all is False and len(fails) >= STUCK_N:
            counts = Counter(failure_by_attempt.get(a.id) or "general" for a in fails)
            fc, n = counts.most_common(1)[0]
            if n >= STUCK_N:
                return _out("stuck", lang, fc=fc.replace("_", " "), n=n, problem_slug=slug)
        recent = attempts[:5]
        heavy = sum(1 for a in recent if a.paste_chars >= PASTE_CHARS)
        pastes = sum(1 for e in events[:20] if e.kind == "paste")
        if heavy >= 2 or (len(recent) >= 3 and pastes >= 3):
            return _out("paste_heavy", lang)
    stamps = [_aware(a.created_at) for a in attempts[:1]] + [_aware(e.created_at) for e in events[:1]]
    if stamps and now - max(stamps) > timedelta(days=IDLE_DAYS):
        return _out("idle", lang)
    return None


def _out(kind: str, lang: str, **kw) -> dict:
    slug = kw.pop("problem_slug", None)
    return {"kind": kind, "text": TEMPLATES[kind][lang].format(**kw), "lang": lang, "problem_slug": slug}


def nudge_for_user(session: Session, user_id: str, lang: str = "en") -> dict | None:
    attempts = list(session.exec(select(Attempt).where(Attempt.user_id == user_id).order_by(desc(Attempt.id)).limit(20)))
    events = list(session.exec(select(HabitEvent).where(HabitEvent.user_id == user_id)
                               .order_by(desc(HabitEvent.id)).limit(40)))
    fb: dict[int, str | None] = {}
    ids = [a.id for a in attempts]
    if ids:
        for row in session.exec(select(DiagnosisRow).where(DiagnosisRow.attempt_id.in_(ids))):
            fb[row.attempt_id] = row.failure_class
    return compute_nudge(attempts, events, fb, lang)
