from typing import Any, Literal

from pydantic import BaseModel


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
