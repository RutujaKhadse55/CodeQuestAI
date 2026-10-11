"""Real /hint, /explain, /explainback, /i18n with the AI services (reuses the chat test fixtures)."""
from conftest import H
from app import providers
from app.chat.tests.test_chat_api import chat, new_user, seed_attempt  # noqa: F401
from app.profile_rag.tests.test_profile_rag import chroma_store, rag  # noqa: F401


def test_hint_locked_and_unlocked_shape(chat):
    uid, h = new_user(chat)
    aid = seed_attempt(uid)
    locked = chat.post("/hint", headers=h, json={"attempt_id": aid, "level": 4}).json()
    assert locked["locked"] is True and locked["text"] == "" and "attempts" in locked["requirements"]
    assert locked["allowed_level"] == 1
    ok = chat.post("/hint", headers=h, json={"attempt_id": aid, "level": 1, "lang": "hi"}).json()
    assert ok["locked"] is False and ok["level"] == 1 and ok["text"] and ok["guard"]["passed"] is True
    assert chat.post("/hint", headers=h, json={}).status_code == 422


def test_hint_guard_rejects_provider_code_and_falls_back(chat):
    uid, h = new_user(chat)
    aid = seed_attempt(uid)
    providers.register_hint_service(lambda *a: "```python\ndef search(a):\n    return 1\n```")
    r = chat.post("/hint", headers=h, json={"attempt_id": aid, "level": 1}).json()
    assert "```" not in r["text"] and r["guard"]["source"] == "template"
    providers.register_hint_service(lambda *a: "Think about one element.")
    assert chat.post("/hint", headers=h, json={"attempt_id": aid, "level": 1}).json()["guard"]["source"] == "llm"


def test_explain_languages_and_ownership(chat):
    a, ha = new_user(chat)
    b, hb = new_user(chat)
    aid = seed_attempt(a)
    assert chat.post("/explain", headers=hb, json={"attempt_id": aid}).status_code == 403
    en = chat.post("/explain", headers=ha, json={"attempt_id": aid, "lang": "en"}).json()
    mr = chat.post("/explain", headers=ha, json={"attempt_id": aid, "lang": "mr"}).json()
    assert en["attempt_id"] == aid and en["text"] != mr["text"] and "def " not in mr["text"]


def test_explainback_scores_and_ownership(chat):
    a, ha = new_user(chat)
    b, hb = new_user(chat)
    aid = seed_attempt(a)
    body = {"attempt_id": aid, "lang": "en",
            "transcript": "My code is wrong because it fails on a single element, so I should handle that case instead."}
    assert chat.post("/explainback", headers=hb, json=body).status_code == 403
    r = chat.post("/explainback", headers=ha, json=body).json()
    assert r["passed"] is True and 0 <= r["score"] <= 1
    bad = chat.post("/explainback", headers=ha, json={**body, "transcript": "dunno"}).json()
    assert bad["passed"] is False and bad["feedback"]


def test_i18n_routes(chat):
    r = chat.post("/i18n/translate", headers=H, json={"text": "Check the loop.", "lang": "hi"}).json()
    assert r["text"] == "Check the loop." and r["translated"] is False  # no LLM: untranslated fallback
    v = chat.get("/i18n/voice-text", headers=H, params={"text": "if i <= n then O(n)", "lang": "en"}).json()
    assert "less than or equal to" in v["text"] and "big O of n" in v["text"]
    assert chat.get("/i18n/detect", headers=H, params={"text": "mujhe hint chahiye"}).json()["lang"] == "hinglish"
