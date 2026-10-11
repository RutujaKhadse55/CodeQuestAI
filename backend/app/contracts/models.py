from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field


class Example(BaseModel):
    input_text: str
    output_text: str


class RunCapture(BaseModel):
    verdict: str
    input: str | None = None
    output: str | None = None
    expected: str | None = None
    stdout: str | None = None
    error: str | None = None


class LCProblem(BaseModel):
    slug: str
    title: str
    difficulty: str
    tags: list[str]
    statement_text: str
    examples: list[Example]
    constraints_text: str
    starter_python: str | None = None
    lang_selected: str
    content_hash: str
    run_capture: RunCapture | None = None


class ReferenceBundle(BaseModel):
    oracle_code: str
    reference_code: str
    gen_inputs_code: str
    comparator: Literal["exact", "unordered", "float_tol"]
    constraints: dict
    verified: bool
    notes: str | None = None


class TestResult(BaseModel):
    kind: Literal["example", "run_capture", "fuzz"]
    outcome: Literal["passed", "wrong_output", "runtime_error", "timeout"]
    input: str | None = None
    expected: str | None = None
    actual: str | None = None  # fuzz => None (never shown)
    failure_class: str | None = None
    error: str | None = None  # additive (Phase 1): runtime error / timeout text for example runs


class Divergence(BaseModel):
    iteration: int | None = None
    variable: str | None = None
    expected: Any = None
    actual: Any = None
    line: int | None = None


class Diagnosis(BaseModel):
    mistake_class: str | None = None
    confidence: float = 0.0
    failure_class: str | None = None
    divergence: Divergence | None = None


class NeutralMessage(BaseModel):
    kind: Literal["diagnosis", "hint", "concept"]
    mistake_class: str | None = None
    failure_class: str | None = None
    divergence: Divergence | None = None
    tier: int | None = None
    concept: str | None = None


class GuardResult(BaseModel):
    passed: bool
    retries: int
    source: Literal["llm", "template"]


class HintResult(BaseModel):
    level: int
    text: str
    locked: bool = False
    requirements: str | None = None
    guard: GuardResult | None = None


class ChatEvent(BaseModel):
    event: Literal["token", "done", "error"]
    data: str | None = None
    guard: GuardResult | None = None


class ErrorBody(BaseModel):
    """Common error body used by every endpoint."""
    code: str
    message: str | None = None


class CaptureResponse(BaseModel):
    problem_id: str
    slug: str | None = None  # additive: extension client reads `slug`
    supported: bool
    reason: str | None = None


class AnalyzeRequest(BaseModel):
    # Additive aliases so the extension's request shape ({slug, lang, lang_pref, ...}) is accepted as-is.
    user_id: str = "local-user"
    problem_slug: str = Field(validation_alias=AliasChoices("problem_slug", "slug"))
    code: str
    language: str = Field(default="python3", validation_alias=AliasChoices("language", "lang"))
    lang_pref: str | None = None
    run_capture: RunCapture | None = None
    paste_chars: int = 0
    elapsed_ms: int = 0


class AnalyzeResponse(BaseModel):
    attempt_id: int
    verified: Literal["oracle-verified", "unverified"]
    results: list[TestResult]
    diagnosis: Diagnosis | None = None
    explanation: str | None = None
    flags: list[str] = []
    allowed_hint_level: int | None = None  # additive (Phase 2): highest hint tier unlocked right now
