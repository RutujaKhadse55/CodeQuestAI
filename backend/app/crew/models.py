"""Pydantic schemas of the CodeQuest agent crew (ported from the CodeQuest_Agent prototype)."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ProblemExplanation(BaseModel):
    what_is_asked: str
    input_meaning: str
    output_meaning: str
    constraints_and_conditions: List[str]
    examples_walkthrough: List[str]
    code_relation: str
    code_solves_problem: Literal["yes", "no", "partially", "unclear"]
    mismatches: List[str]


class GeneratedTestCase(BaseModel):
    category: Literal[
        "normal", "boundary", "minimum", "maximum", "special"
    ]
    input: str
    expected_output: str
    reason: str
    actual_output: str = ""
    status: Literal["PASS", "FAIL", "NOT_RUN"] = "NOT_RUN"


class TestCaseReport(BaseModel):
    disclaimer: str = (
        "Generated tests only; these are not official LeetCode hidden tests."
    )
    test_cases: List[GeneratedTestCase] = Field(default_factory=list)
    failure_analysis: List[str] = Field(default_factory=list)
    required_fixes: List[str] = Field(default_factory=list)


class DebugReport(BaseModel):
    diagnosis: str
    bug_types: List[Literal["syntax", "logical", "boundary"]]
    variable_trace_of_bug: str
    root_cause: str
    expected_vs_actual: str
    corrected_code: str
    corrected_code_trace: str
    changes_and_reasons: List[str]


class TraceStep(BaseModel):
    step: int
    statement: str
    variables: str
    condition_result: str = ""
    observed_vs_expected: str = ""


class TraceReport(BaseModel):
    trace_source: Literal["actual_runtime", "static_simulation"]
    note: str
    steps: List[TraceStep] = Field(default_factory=list)
    divergence_step: Optional[int] = None
    failure_explanation: str


class HintResult(BaseModel):
    hint_level: int
    hint: str
    relevant_topics: List[str] = Field(default_factory=list)
    approaches_and_tradeoffs: List[str] = Field(default_factory=list)
    time_complexity: str
    space_complexity: str
    next_step_guidance: str


# ---- additions for the backend integration -----------------------------------------------------------------------
class TraceAnalysis(BaseModel):
    """What the LLM adds to a REAL runtime trace (the steps themselves always come from the sandbox)."""
    divergence_step: Optional[int] = None
    failure_explanation: str = ""
    note: str = ""


class FailureNotes(BaseModel):
    failure_analysis: List[str] = Field(default_factory=list)
    required_fixes: List[str] = Field(default_factory=list)


class GeneratedCases(BaseModel):
    test_cases: List[GeneratedTestCase] = Field(default_factory=list)
