"""/hint and /explain fallbacks used by the extension until AI's real routers exist."""
from sqlmodel import Session

from conftest import H
from app import db, providers
from app.chat.tests.test_chat_api import chat, new_user, seed_attempt  # noqa: F401  (fixtures + helper)
from app.profile_rag.tests.test_profile_rag import chroma_store, rag  # noqa: F401  (fixtures chat depends on)
from app.db.models_core import Attempt


def test_routes_are_registered(real_client):
    paths = real_client.get("/openapi.json", headers=H).json()["paths"]
    assert "/hint" in paths and "/explain" in paths


def test_hint_levels_unlock_with_attempts_and_text_is_never_code(chat):
    uid, h = new_user(chat)
    aid = seed_attempt(uid)
    r1 = chat.post("/hint", headers=h, json={"problem_slug": "binary-search", "attempt_id": aid, "level": 1}).json()
    assert r1["locked"] is False and r1["level"] == 1 and "exactly one element" in r1["text"]
    assert r1["guard"]["source"] == "template" and "def " not in r1["text"]
    r4 = chat.post("/hint", headers=h, json={"problem_slug": "binary-search", "attempt_id": aid, "level": 4}).json()
    assert r4["locked"] is True and r4["text"] == "" and "attempts" in r4["requirements"]
    seed_attempt(uid)  # 2 attempts -> level 2 unlocks
    r2 = chat.post("/hint", headers=h, json={"problem_slug": "binary-search", "attempt_id": aid, "level": 2}).json()
    assert r2["locked"] is False and "`lo`" in r2["text"]
    seed_attempt(uid)
    r3 = chat.post("/hint", headers=h, json={"problem_slug": "binary-search", "attempt_id": aid}).json()  # next level
    assert r3["level"] == 3 and "line 9" in r3["text"]


def test_hint_default_level_advances_and_provider_overrides(chat):
    uid, h = new_user(chat)
    aid = seed_attempt(uid)
    seed_attempt(uid)
    first = chat.post("/hint", headers=h, json={"attempt_id": aid}).json()
    second = chat.post("/hint", headers=h, json={"attempt_id": aid}).json()
    assert (first["level"], second["level"]) == (1, 2)
    providers.register_hint_service(lambda user, slug, level, ctx: f"AI hint {level}")
    assert chat.post("/hint", headers=h, json={"attempt_id": aid, "level": 1}).json()["text"] == "AI hint 1"


def test_hint_and_explain_respect_attempt_ownership(chat):
    a, ha = new_user(chat)
    b, hb = new_user(chat)
    aid = seed_attempt(a)
    assert chat.post("/hint", headers=hb, json={"attempt_id": aid, "level": 1}).status_code == 403
    assert chat.post("/explain", headers=hb, json={"attempt_id": aid}).status_code == 403
    assert chat.post("/explain", headers=ha, json={"attempt_id": aid}).status_code == 200
    assert chat.post("/hint", headers=ha, json={}).status_code == 422  # needs slug or attempt


def test_explain_gives_plain_language_without_hidden_data(chat):
    uid, h = new_user(chat)
    aid = seed_attempt(uid)
    t = chat.post("/explain", headers=h, json={"attempt_id": aid, "lang": "en"}).json()["text"]
    assert "single element" in t and "`lo`" in t and "[1]" not in t and "def " not in t
    with Session(db.engine) as s:
        s.add(Attempt(user_id=uid, problem_slug="binary-search", code="x", passed_all=True))
        s.commit()
        passed = s.exec(__import__("sqlmodel").select(Attempt).where(Attempt.passed_all == True)).first()  # noqa: E712
    assert "passed all checks" in chat.post("/explain", headers=h, json={"attempt_id": passed.id}).json()["text"]


def test_works_without_a_user_token_like_the_current_extension(chat):
    aid = seed_attempt("local-user")
    r = chat.post("/hint", headers=H, json={"problem_slug": "binary-search", "attempt_id": aid, "level": 1})
    assert r.status_code == 200 and r.json()["locked"] is False
    assert chat.post("/explain", headers=H, json={"attempt_id": aid}).status_code == 200
