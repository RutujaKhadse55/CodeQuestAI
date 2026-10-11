import ast
import re
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..contracts.enums import ErrorCode
from sqlmodel import func, select

from .. import config, providers
from ..contracts.models import AnalyzeRequest, AnalyzeResponse, Diagnosis, LCProblem, TestResult
from ..db.models_core import (Attempt, DiagnosisRow, HabitEvent, LCProblemRow, TestResultRow, User)
from ..deps import get_session
from ..engine import ast_policy
from ..engine.copy_detector import is_copy
from ..engine.diagnosis_fallback import FALLBACK_CONFIDENCE, mistake_from_failure_class
from ..engine.hint_state import HintStateService
from ..mastery.service import MasteryService
from ..engine.lang import normalize_lang
from ..engine.examples_parser import ParseError, args_for, parse_inputs
from ..engine.sandbox.runner import SandboxUnavailable
from ..engine.service import SandboxEngine
from ..engine.signature import parse_signature
from ..errors import ApiError

router = APIRouter()
engine = SandboxEngine()
MAX_EXAMPLES = 10
HARDCODE_CONFIDENCE = 0.9


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
    """v1: policy -> examples (+ Run capture) -> fuzz vs oracle -> shrink -> trace -> diagnose -> persist."""
    if normalize_lang(req.language) != "python3":
        raise ApiError(ErrorCode.UNSUPPORTED_LANGUAGE, "only python3 is executed")
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    used = session.exec(select(func.count()).select_from(Attempt).where(
        Attempt.user_id == req.user_id, Attempt.created_at >= today)).one()
    if used >= config.DAILY_ANALYZE_CAP:
        raise ApiError(ErrorCode.RATE_LIMITED, f"daily analyze cap of {config.DAILY_ANALYZE_CAP} reached")
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
    syntax_error = None
    if own.entry is None:
        try:
            ast.parse(req.code)
        except SyntaxError as e:  # a learner typo is a normal result, not an API error
            syntax_error = f"SyntaxError: {e.msg} (line {e.lineno})"
        else:
            raise ApiError(ErrorCode.VALIDATION_ERROR, "no function or class Solution found in code")
    params = own.params or starter.params
    tests, flags = build_tests(problem, req, params)
    results = []
    fuzz = None
    bundle = providers.bundle_for(problem)
    use_fuzz = bundle.verified
    if not bundle.verified:
        flags.append("no_reference_bundle")
    elif any(ast_policy.check(c) for c in (bundle.oracle_code, bundle.reference_code, bundle.gen_inputs_code)):
        flags.append("bundle_rejected")
        use_fuzz = False
    if not tests:
        flags.append("no_runnable_tests")
    try:
        if syntax_error:
            results = [TestResult(kind="example", outcome="runtime_error", error=syntax_error)]
            flags.append("syntax_error")
        elif use_fuzz:
            seed = secrets.randbelow(2**31)  # fresh per attempt; stored, never shown
            results, fuzz = engine.run_and_fuzz(req.code, tests, bundle, seed)
            flags.extend(fuzz.flags)
            if fuzz.ran:
                results.append(TestResult(kind="fuzz", outcome=fuzz.first_kind or "passed",
                                          failure_class=fuzz.failure_class))  # never input/expected/actual
        elif tests:
            results = engine.sandbox_run(req.code, req.code, tests)
    except SandboxUnavailable as e:
        raise ApiError(ErrorCode.UPSTREAM_FAILED, f"sandbox unavailable: {e}")

    hardcode_reasons: list[str] = []
    try:
        hardcode_reasons = providers.hardcode_detector()(
            req.code, [(e.input_text, e.output_text) for e in problem.examples])
    except Exception:  # noqa: BLE001  (a broken detector must never fail an analysis)
        hardcode_reasons = []
    if hardcode_reasons:
        flags.append("hardcode_suspected")

    examples_ok = bool(results) and all(r.outcome == "passed" for r in results if r.kind != "fuzz")
    fuzz_ok = fuzz is None or not fuzz.ran or fuzz.passed
    passed_all = bool(results) and examples_ok and fuzz_ok
    code_len = len(req.code)
    copy_flagged = is_copy(req.paste_chars, code_len, req.elapsed_ms, passed_all)
    if copy_flagged:
        flags.append("copy_suspected")

    if session.get(User, req.user_id) is None:
        session.add(User(user_id=req.user_id))
    attempt = Attempt(user_id=req.user_id, problem_slug=req.problem_slug, code=req.code, language="python3",
                      verified="oracle-verified" if (fuzz and fuzz.ran) else "unverified", passed_all=passed_all,
                      paste_chars=req.paste_chars, elapsed_ms=req.elapsed_ms,
                      fuzz_seed=fuzz.seed if fuzz else None, copy_flagged=copy_flagged,
                      mastery_pending=copy_flagged)
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    for r in results:
        session.add(TestResultRow(attempt_id=attempt.id, kind=r.kind, outcome=r.outcome, input=r.input,
                                  expected=r.expected, actual=r.actual, error=r.error,
                                  failure_class=r.failure_class))

    diagnosis = None
    if not passed_all and results:
        diagnosis = providers.diagnoser().diagnose(fuzz.vector if fuzz else "", req.problem_slug,
                                                   fuzz.divergence if fuzz else None)
        diagnosis.failure_class = diagnosis.failure_class or (fuzz.failure_class if fuzz else None)
        if hardcode_reasons:  # strongest, most specific signal wins over the failure-class rule
            diagnosis.mistake_class, diagnosis.confidence = "hardcoded_output", HARDCODE_CONFIDENCE
        elif diagnosis.mistake_class is None:
            diagnosis.mistake_class = mistake_from_failure_class(diagnosis.failure_class)
            diagnosis.confidence = FALLBACK_CONFIDENCE if diagnosis.mistake_class else 0.0
        session.add(DiagnosisRow(
            attempt_id=attempt.id, mistake_class=diagnosis.mistake_class, confidence=diagnosis.confidence,
            failure_class=diagnosis.failure_class, fuzz_vector=fuzz.vector if fuzz else None,
            divergence_json=diagnosis.divergence.model_dump_json() if diagnosis.divergence else None))
        session.commit()
        if diagnosis.mistake_class:
            MasteryService(session).record_mistake(req.user_id, diagnosis.mistake_class)
    if not copy_flagged:
        MasteryService(session).apply_attempt(attempt)

    if req.paste_chars:
        session.add(HabitEvent(user_id=req.user_id, kind="paste", value=req.paste_chars,
                               problem_slug=req.problem_slug))
    if req.elapsed_ms:
        session.add(HabitEvent(user_id=req.user_id, kind="run", value=req.elapsed_ms,
                               problem_slug=req.problem_slug))
    session.commit()
    return AnalyzeResponse(attempt_id=attempt.id, verified=attempt.verified, results=results, diagnosis=diagnosis,
                           flags=flags, allowed_hint_level=HintStateService(session).allowed_level(
                               req.user_id, req.problem_slug))
