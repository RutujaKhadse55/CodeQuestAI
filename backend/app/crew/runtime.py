"""Execution bridge for the crew: everything that runs learner code goes through the Backend sandbox (Docker /
remote service), never in the API process. This replaces the prototype's subprocess code_runner / tracer tools.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from ..contracts.models import LCProblem, TestResult
from ..engine.examples_parser import ParseError, args_for, parse_inputs, parse_value
from ..engine.sandbox.runner import SandboxUnavailable
from ..engine.service import SandboxEngine, values_equal
from ..engine.signature import parse_signature

log = logging.getLogger(__name__)
MAX_CASES = 12


@dataclass
class Case:
    input_text: str
    expected_text: str | None
    args: list | None = None  # None => could not be parsed (NOT_RUN)
    comparator: str = "exact"


def parse_case(input_text: str, expected_text: str | None, params: list[str], comparator: str = "exact") -> Case:
    try:
        args = args_for(params, parse_inputs(input_text))
        if expected_text is not None:
            parse_value(expected_text)  # validate only; the sandbox compares parsed values
    except ParseError:
        return Case(input_text, expected_text, None, comparator)
    return Case(input_text, expected_text, args, comparator)


def example_cases(problem: LCProblem, code: str) -> list[Case]:
    params = parse_signature(code or problem.starter_python).params
    return [parse_case(e.input_text, e.output_text, params) for e in problem.examples[:MAX_CASES]]


def run_cases(code: str, cases: list[Case]) -> list[TestResult | None] | None:
    """One TestResult per case (None where the case could not be parsed). None overall = sandbox unavailable."""
    runnable = [(i, c) for i, c in enumerate(cases) if c.args is not None]
    out: list[TestResult | None] = [None] * len(cases)
    if not runnable:
        return out
    tests = [{"args": c.args, "expected_text": c.expected_text, "input_text": c.input_text,
              "comparator": c.comparator, "kind": "example"} for _, c in runnable]
    try:
        results = SandboxEngine().sandbox_run(code, code, tests, timeout_s=2.0)
    except SandboxUnavailable as exc:
        log.warning("crew sandbox unavailable: %s", exc)
        return None
    for (i, _), r in zip(runnable, results):
        out[i] = r
    return out


def oracle_outputs(reference_code: str, cases: list[Case]) -> list[str | None] | None:
    """Output of the verified reference solution for each case (None where it failed / could not run)."""
    results = run_cases(reference_code, [Case(c.input_text, None, c.args, c.comparator) for c in cases])
    if results is None:
        return None
    return [r.actual if r is not None and r.outcome in ("passed", "wrong_output") else None for r in results]


def step_trace(code: str, args: list) -> dict | None:
    entry = parse_signature(code).entry
    if entry is None:
        return None
    try:
        return SandboxEngine().step_trace(code, entry, args)
    except SandboxUnavailable as exc:
        log.warning("crew sandbox unavailable: %s", exc)
        return None


def same(actual: str | None, expected: str | None, comparator: str = "exact") -> bool:
    try:
        return values_equal(parse_value(actual), parse_value(expected), comparator)
    except (ParseError, TypeError):
        return False
