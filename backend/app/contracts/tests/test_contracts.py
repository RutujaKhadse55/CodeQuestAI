
from app.contracts import enums, models, protocols


def test_models_roundtrip():
    p = models.LCProblem(slug="two-sum", title="Two Sum", difficulty="Easy", tags=["array"],
                         statement_text="s", examples=[models.Example(input_text="a", output_text="b")],
                         constraints_text="c", lang_selected="python3", content_hash="h")
    assert models.LCProblem.model_validate_json(p.model_dump_json()) == p


def test_frozen_error_codes():
    assert {e.value for e in enums.ErrorCode} == {
        "UNAUTHORIZED", "FORBIDDEN", "VALIDATION_ERROR", "RATE_LIMITED", "CODE_REJECTED", "HINT_LOCKED",
        "UNSUPPORTED_PROBLEM", "UNSUPPORTED_LANGUAGE", "CREDIT_CAP_REACHED", "UPSTREAM_FAILED"}


def test_protocols_present():
    for n in ["Engine", "HintState", "Mastery", "ReferenceBuilder", "Diagnoser", "Explainer", "Guard",
              "Translator", "LearnerModel", "RubricScorer", "Memory", "VoiceService"]:
        assert getattr(getattr(protocols, n), "_is_protocol", False)
