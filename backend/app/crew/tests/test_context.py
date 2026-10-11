"""Explain-by-URL stores the learner's username profile in the vector DB and the problem URL in the DB for other tabs."""
from sqlmodel import Session

from conftest import H
from app import config, db, lcfetch
from app.chat.tests.test_chat_api import chat, new_user  # noqa: F401  (fixtures + helper)
from app.contracts.models import LCProblem
from app.db.models_core import LearnerContext
from app.profile_rag import store
from app.profile_rag.tests.test_profile_rag import chroma_store, rag  # noqa: F401
from app.tests.test_analyze import _fixture


def test_username_goes_to_vector_db_and_url_to_db_for_other_tabs(chat, monkeypatch):  # noqa: F811
    monkeypatch.setattr(config, "FEATURE_CREW", True)
    p = LCProblem(**_fixture("binary-search"))
    monkeypatch.setattr(lcfetch, "fetch_problem", lambda url: p)
    uid, h = new_user(chat)

    r = chat.post("/explain/problem", headers=h, json={"url": "https://leetcode.com/problems/binary-search/",
                                                       "username": "someone"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["personalised"] is True and body["username"] == "someone"
    assert store.get_store().count(uid) > 10  # the public profile is indexed in the vector DB for THIS learner

    with Session(db.engine) as s:  # the question URL is stored in the DB
        row = s.get(LearnerContext, uid)
        assert row.problem_url == "https://leetcode.com/problems/binary-search/" and row.leetcode_username == "someone"

    ctx = chat.get("/context", headers=h).json()["context"]
    assert ctx["problem_slug"] == "binary-search" and ctx["leetcode_username"] == "someone"

    # another tab: no problem_slug sent -> the stored problem is used
    t = chat.post("/crew/tests", headers=h, json={})
    assert t.status_code == 200 and t.json()["agent"] == "tests"
    # a foreign host is rejected
    assert chat.post("/context", headers=h, json={"url": "https://evil.com/problems/x/"}).status_code == 422
    # setting the context by URL alone
    assert chat.post("/context", headers=h, json={"url": "https://leetcode.com/problems/two-sum/"}).json()["context"]["problem_slug"] == "two-sum"


def test_deleting_user_data_removes_the_stored_context(chat, monkeypatch):  # noqa: F811
    monkeypatch.setattr(config, "FEATURE_CREW", True)
    uid, h = new_user(chat)
    chat.post("/context", headers=h, json={"url": "https://leetcode.com/problems/two-sum/"})
    assert chat.get("/context", headers=h).json()["context"] is not None
    assert chat.delete(f"/users/{uid}/data", headers=h).status_code == 200
    with Session(db.engine) as s:  # the learner's token is gone too, so check the table directly
        assert s.get(LearnerContext, uid) is None
