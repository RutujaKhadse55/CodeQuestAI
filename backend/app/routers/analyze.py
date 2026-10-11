import re

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..contracts.enums import ErrorCode
from ..contracts.models import AnalyzeRequest, AnalyzeResponse, LCProblem
from ..db.models_core import Attempt, HabitEvent, LCProblemRow, TestResultRow, User
from ..deps import get_session
from ..engine import ast_policy
from ..engine.lang import normalize_lang
from ..engine.examples_parser import ParseError, args_for, parse_inputs
from ..engine.sandbox.runner import SandboxUnavailable
from ..engine.service import SandboxEngine
from ..engine.signature import parse_signature
from ..errors import ApiError

router = APIRouter()
engine = SandboxEngine()
MAX_EXAMPLES = 10


def build_tests(problem: LCProblem, req: AnalyzeRequest, params: list[str]) -> tuple[list[dict], list[str]]:
    comparator = "unordered" if re.search(r"any order", problem.statement_text, re.I) else "exact"
    tests, flags, seen = [], [], set()

    def add(kind: str, input_text: str, expected: str | None):
        try:
            args = args_for(params, parse_inputs(input_text))
        except ParseError:
            flags.append(f"{kind}_unparsed")
            return
        key = repr(args)
        if key in seen:
            return
        seen.add(key)
        tests.append({"kind": kind, "args": args, "input_text": input_text,
                      "expected_text": expected, "comparator": comparator})

    for ex in problem.examples[:MAX_EXAMPLES]:
        add("example", ex.input_text, ex.output_text)
    rc = req.run_capture
    if rc and rc.input and rc.expected:  # the learner's own Run result: LeetCode's judged ground truth
        add("run_capture", rc.input, rc.expected)
    return tests, flags


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, session: Session = Depends(get_session)):
    """v0: policy -> run examples (+ Run capture) -> per-test outcomes. Fuzz/trace/diagnosis: Phase 2."""
    if normalize_lang(req.language) != "python3":
        raise ApiError(ErrorCode.UNSUPPORTED_LANGUAGE, "only python3 is executed")
    row = session.get(LCProblemRow, req.problem_slug)
    if row is None:
        raise ApiError(ErrorCode.UNSUPPORTED_PROBLEM, "problem not captured; call /problems/capture first")
    if not row.supported:
        raise ApiError(ErrorCode.UNSUPPORTED_PROBLEM, row.reason)
    violations = ast_policy.check(req.code)
    if violations:
        raise ApiError(ErrorCode.CODE_REJECTED, "code rejected by sandbox policy",
                       violations=[v.as_dict() for v in violations][:10])
    problem = LCProblem.model_validate_json(row.payload_json)
    own = parse_signature(req.code)
    starter = parse_signature(problem.starter_python)
    if own.entry is None:
        raise ApiError(ErrorCode.VALIDATION_ERROR, "no function or class Solution found in code")
    params = own.params or starter.params
    tests, flags = build_tests(problem, req, params)
    results = []
    if not tests:
        flags.append("no_runnable_tests")
    else:
        try:
            results = engine.sandbox_run(req.code, req.code, tests)
        except SandboxUnavailable as e:
            raise ApiError(ErrorCode.UPSTREAM_FAILED, f"sandbox unavailable: {e}")

    if session.get(User, req.user_id) is None:
        session.add(User(user_id=req.user_id))
    attempt = Attempt(user_id=req.user_id, problem_slug=req.problem_slug, code=req.code, language=req.language,
                      verified="unverified", passed_all=bool(results) and all(r.outcome == "passed" for r in results),
                      paste_chars=req.paste_chars, elapsed_ms=req.elapsed_ms)
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    for r in results:
        session.add(TestResultRow(attempt_id=attempt.id, kind=r.kind, outcome=r.outcome, input=r.input,
                                  expected=r.expected, actual=r.actual, error=r.error,
                                  failure_class=r.failure_class))
    if req.paste_chars:
        session.add(HabitEvent(user_id=req.user_id, kind="paste", value=req.paste_chars,
                               problem_slug=req.problem_slug))
    if req.elapsed_ms:
        session.add(HabitEvent(user_id=req.user_id, kind="run", value=req.elapsed_ms,
                               problem_slug=req.problem_slug))
    session.commit()
    # Oracle/reference bundle (AI) is not wired yet => always "unverified"; no fuzz data exists in v0.
    return AnalyzeResponse(attempt_id=attempt.id, verified="unverified", results=results, flags=flags)
