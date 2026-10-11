"""Phase 3: recommend, dashboard v2, delete-all, localised errors, daily cap, provider hooks."""
from sqlmodel import Session, func, select

from conftest import H, needs_sandbox
from app.tests.test_analyze import GOOD_TWO_SUM, _analyze, _fixture
from app.tests.test_analyze_v1 import BS_BUG, BS_GOOD, _capture


# ---------- localised errors ----------
def test_errors_carry_key_and_localised_message(real_client):
    en = real_client.get("/health").json()
    assert en["code"] == "UNAUTHORIZED" and en["message_key"] == "errors.UNAUTHORIZED"
    assert en["localized"] == "Missing or invalid API token."
    hi = real_client.get("/health", headers={"X-Lang": "hi"}).json()
    assert "टोकन" in hi["localized"]
    mr = real_client.get("/health", headers={"Accept-Language": "mr-IN,mr;q=0.9"}).json()
    assert "टोकन" in mr["localized"] and mr["localized"] != hi["localized"]
    assert real_client.get("/health", headers={"X-Lang": "fr"}).json()["localized"] == en["localized"]


def test_every_error_code_has_all_three_languages():
    from app.contracts.enums import ErrorCode
    from app.i18n_errors import LANGS, MESSAGES
    for c in ErrorCode:
        assert set(MESSAGES[c.value]) == set(LANGS), c


def test_validation_error_is_localised(real_client):
    r = real_client.post("/analyze", headers={**H, "X-Lang": "hi"}, json={"code": 1})
    assert r.status_code == 422 and r.json()["message_key"] == "errors.VALIDATION_ERROR"


# ---------- daily cap ----------
def test_daily_analyze_cap(real_client, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "DAILY_ANALYZE_CAP", 2)
    real_client.post("/problems/capture", headers=H, json=_fixture("two-sum"))
    from app.db.models_core import Attempt
    from app import db
    with Session(db.engine) as s:
        for _ in range(2):
            s.add(Attempt(user_id="u1", problem_slug="two-sum", code="x"))
        s.commit()
    r = _analyze(real_client, GOOD_TWO_SUM)
    assert r.status_code == 429 and r.json()["code"] == "RATE_LIMITED" and "daily" in r.json()["message"]
    other = real_client.post("/analyze", headers=H, json={"user_id": "someone-else", "problem_slug": "two-sum",
                                                          "code": "import os"})
    assert other.json()["code"] == "CODE_REJECTED"  # a different user is not capped


# ---------- recommend ----------
def test_recommend_without_history_and_with_weak_concept(real_client):
    first = real_client.get("/recommend/new-user", headers=H).json()
    assert first["slug"] == "two-sum" and first["url"] == "https://leetcode.com/problems/two-sum/"
    from app import db
    from app.db.models_core import ConceptMastery
    with Session(db.engine) as s:
        s.add(ConceptMastery(user_id="u9", concept="binary search", rating=800.0))
        s.add(ConceptMastery(user_id="u9", concept="array", rating=950.0))
        s.commit()
    rec = real_client.get("/recommend/u9", headers=H).json()
    assert rec["concept"] == "binary search" and rec["slug"] == "binary-search"
    assert rec["difficulty"] == "Easy" and "weakest concept" in rec["reason"]


def test_recommend_skips_solved_and_is_deterministic(real_client):
    from app import db
    from app.db.models_core import Attempt, ConceptMastery
    with Session(db.engine) as s:
        s.add(ConceptMastery(user_id="u8", concept="binary search", rating=800.0))
        s.add(Attempt(user_id="u8", problem_slug="binary-search", code="x", passed_all=True))
        s.commit()
    a, b = (real_client.get("/recommend/u8", headers=H).json() for _ in range(2))
    assert a == b and a["slug"] == "missing-number"  # next unsolved problem tagged "binary search"


def test_recommend_when_everything_solved(real_client):
    from app import db
    from app.db.models_core import Attempt
    from app.mastery.recommender import CURATED
    with Session(db.engine) as s:
        for p in CURATED:
            s.add(Attempt(user_id="u7", problem_slug=p["slug"], code="x", passed_all=True))
        s.commit()
    assert real_client.get("/recommend/u7", headers=H).json()["slug"] is None


# ---------- dashboard v2 + hooks + delete-all ----------
@needs_sandbox
def test_dashboard_v2_delete_all_and_hooks(real_client):
    from app import providers
    calls = []
    providers.register_credits(lambda uid: {"used_chars": 120, "daily_cap": 5000, "user": uid})
    providers.register_deletion_hook("memory", lambda uid: calls.append(("memory", uid)))
    providers.register_deletion_hook("broken", lambda uid: 1 / 0)
    try:
        _capture(real_client, "binary-search")
        _analyze(real_client, BS_BUG, slug="binary-search", paste_chars=10, elapsed_ms=2000)
        _analyze(real_client, BS_GOOD, slug="binary-search")
        d = real_client.get("/dashboard/u1", headers=H).json()
        assert d["credits"]["used_chars"] == 120
        assert d["profile"]["attempts"] == 2 and d["profile"]["habits"]["paste_rate"] == 0.5
        assert d["profile"]["habits"]["edge_case_miss_rate"] == 1.0 and d["profile"]["solved"] == 1
        assert d["heatmap"] == [{"problem_slug": "binary-search", "mistake_class": "missing_edge_single", "count": 1}]
        assert d["solved"] == 1 and d["mastery"] and d["recent"]

        r = real_client.delete("/users/u1/data", headers=H).json()
        assert r["deleted"]["attempts"] == 2 and r["deleted"]["test_results"] >= 6
        assert r["deleted"]["diagnoses"] == 1 and r["deleted"]["concept_mastery"] >= 1
        assert r["hooks"]["memory"] == "ok" and r["hooks"]["broken"].startswith("error")
        assert calls == [("memory", "u1")]
        empty = real_client.get("/dashboard/u1", headers=H).json()
        assert empty["attempts"] == 0 and empty["mastery"] == {} and empty["mistakes"] == {} and empty["recent"] == []
        from app import db
        from app.db.models_core import Attempt, TestResultRow
        with Session(db.engine) as s:
            assert s.exec(select(func.count()).select_from(Attempt)).one() == 0
            assert s.exec(select(func.count()).select_from(TestResultRow)).one() == 0
        again = real_client.delete("/users/u1/data", headers=H).json()  # idempotent
        assert again["deleted"]["attempts"] == 0
    finally:
        providers._credits = None
        providers._deletion_hooks.clear()


def test_credits_provider_failure_never_breaks_dashboard(real_client):
    from app import providers
    providers.register_credits(lambda uid: 1 / 0)
    try:
        assert real_client.get("/dashboard/x", headers=H).json()["credits"] is None
    finally:
        providers._credits = None


def test_delete_other_users_data_untouched(real_client):
    from app import db
    from app.db.models_core import Attempt
    with Session(db.engine) as s:
        s.add(Attempt(user_id="keep", problem_slug="two-sum", code="x"))
        s.add(Attempt(user_id="drop", problem_slug="two-sum", code="x"))
        s.commit()
    real_client.delete("/users/drop/data", headers=H)
    with Session(db.engine) as s:
        assert [a.user_id for a in s.exec(select(Attempt)).all()] == ["keep"]
