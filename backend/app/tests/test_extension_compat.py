"""The browser extension's API client talks to us with Bearer auth and its own request shape."""
from conftest import H, needs_sandbox
from app.tests.test_analyze import GOOD_TWO_SUM, _fixture

BEARER = {"Authorization": "Bearer change-me"}
EXT_ORIGIN = "chrome-extension://" + "a" * 32


def test_bearer_token_accepted_and_bad_rejected(real_client):
    assert real_client.get("/health", headers=BEARER).json()["status"] == "ok"
    assert real_client.get("/health", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert real_client.get("/health").status_code == 401


def test_cors_preflight_from_extension_origin(real_client):
    r = real_client.options("/analyze", headers={"Origin": EXT_ORIGIN, "Access-Control-Request-Method": "POST",
                                                  "Access-Control-Request-Headers": "authorization,content-type"})
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == EXT_ORIGIN
    r = real_client.options("/analyze", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers


def test_extension_capture_shape(real_client):
    p = _fixture("two-sum")  # includes extension-only fields: source, captured_at
    p["lang_selected"] = "Python3"  # LeetCode's label
    r = real_client.post("/problems/capture", headers=BEARER, json=p).json()
    assert r["slug"] == "two-sum" and r["supported"] is True
    assert real_client.post("/problems/capture", headers=BEARER, json={**p, "lang_selected": "Java"}).json()["supported"] is False


@needs_sandbox
def test_extension_analyze_shape_end_to_end(real_client):
    real_client.post("/problems/capture", headers=BEARER, json=_fixture("two-sum"))
    req = {"slug": "two-sum", "source": "leetcode", "code": GOOD_TWO_SUM, "lang": "Python3",
           "paste_chars": 0, "elapsed_ms": 1500, "lang_pref": "hi"}
    body = real_client.post("/analyze", headers=BEARER, json=req).json()
    assert [r["outcome"] for r in body["results"]] == ["passed"] * 3
