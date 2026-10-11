import pytest

from app import providers
from app.ai.rubric.explainback_score import RubricScorerImpl, default_rubric, keyword_score

GOOD = "My code is wrong because it fails on an empty list, so I should check the length first."


@pytest.fixture(autouse=True)
def _reset():
    yield
    providers._llm = None


def test_keyword_pass_and_fail():
    r = default_rubric("missing_empty_case")
    s, fb = keyword_score(GOOD, r, "en")
    assert s == 1.0 and fb
    s, fb = keyword_score("I think it is something about numbers and stuff.", r, "en")
    assert s < 0.6 and "Try to also cover" in fb
    assert keyword_score("ok", r, "en")[0] == 0.0


def test_keyword_hindi_marathi():
    r = default_rubric("missing_empty_case")
    assert keyword_score("मेरा कोड खाली input पर गलत है क्योंकि उसे जाँच चाहिए", r, "hi")[0] >= 0.6
    assert keyword_score("माझा कोड रिकाम्या input वर चुकीचे आहे कारण तपास पाहिजे", r, "mr")[0] >= 0.6


def test_custom_rubric_points():
    rub = {"points": [{"id": "a", "keywords": ["pointer"]}, {"id": "b", "keywords": {"en": ["swap"]}}]}
    assert RubricScorerImpl().score("the pointer moves and then we swap them", rub, "en")[0] == 1.0
    assert RubricScorerImpl().score("the pointer moves and then it ends", rub, "en")[0] == 0.5


def test_llm_scoring_clamped_and_guarded():
    providers.register_llm(lambda p: '{"score": 0.8, "feedback": "Nice, mention the empty case too."}')
    assert RubricScorerImpl().score(GOOD, {}, "en") == (0.8, "Nice, mention the empty case too.")
    providers.register_llm(lambda p: '{"score": 7, "feedback": "x"}')  # invalid -> keyword fallback
    assert RubricScorerImpl().score(GOOD, {}, "en")[0] <= 1
    providers.register_llm(lambda p: '{"score": 1, "feedback": "```python\\ndef f(x):\\n    return x\\n```"}')
    s, fb = RubricScorerImpl().score(GOOD, {}, "en")
    assert "```" not in fb


def test_never_raises():
    def boom(p):
        raise RuntimeError("x")
    providers.register_llm(boom)
    assert RubricScorerImpl().score(GOOD, None, "zz")[0] >= 0
