"""AI agent crew endpoints (behind FEATURE_CREW): explain, generated tests, debug, trace. Hints go through the
existing POST /hint, whose wording this module upgrades by registering the crew's Hint Mentor with providers.

  POST /crew/explain | /crew/tests | /crew/debug | /crew/trace
  body: {problem_slug, code?, language?, selected_code?, response_language?: en|hi|mr|hinglish, attempt_id?, user_id?,
         input?, expected?}   (input/expected: trace only; default = the problem's first example)
  -> {agent, result, llm_used, executed, notes}
Learner code runs only in the Backend sandbox. Every model-written field passes the Guard.
"""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, desc, select

from .. import config, db, providers
from ..auth import resolve_user, user_token_header
from ..chat import rules
from ..chat.tools import attempt_summary
from ..contracts.enums import ErrorCode
from ..contracts.models import LCProblem
from ..crew import llm, service
from ..db.models_core import Attempt, LCProblemRow
from ..deps import get_session
from ..engine.lang import normalize_lang
from ..errors import ApiError

router = APIRouter(prefix="/crew", tags=["crew"])
MAX_CODE_CHARS = 20_000


def _enabled() -> None:
    if not config.FEATURE_CREW:
        raise ApiError(ErrorCode.UPSTREAM_FAILED, "the AI crew is disabled (set FEATURE_CREW=1)")


class CrewRequest(BaseModel):
    problem_slug: str | None = Field(default=None, max_length=200)  # omitted => the learner's stored current problem
    code: str | None = Field(default=None, max_length=MAX_CODE_CHARS)
    selected_code: str | None = Field(default=None, max_length=MAX_CODE_CHARS)
    language: str | None = Field(default=None, max_length=30)
    response_language: Literal["en", "hi", "mr", "hinglish"] = "en"
    attempt_id: int | None = None
    user_id: str | None = None
    input: str | None = Field(default=None, max_length=2000)
    expected: str | None = Field(default=None, max_length=2000)


def _problem(session: Session, slug: str) -> LCProblem:
    row = session.get(LCProblemRow, slug)
    if row is None:
        raise ApiError(ErrorCode.VALIDATION_ERROR, "unknown problem: capture it first (POST /problems/capture)")
    return LCProblem.model_validate_json(row.payload_json)


def _context(session: Session, req: CrewRequest, token: str) -> tuple[service.Ctx, str, Attempt | None]:
    probe = session.get(Attempt, req.attempt_id) if req.attempt_id is not None else None
    uid = resolve_user(session, req.user_id or (probe.user_id if probe else None), token)
    slug = req.problem_slug
    if not slug:
        from ..db.models_core import LearnerContext
        stored = session.get(LearnerContext, uid)
        if stored is None:
            raise ApiError(ErrorCode.VALIDATION_ERROR, "problem_slug is required (no current problem stored yet: use the Explain tab first)")
        slug = stored.problem_slug
    req = req.model_copy(update={"problem_slug": slug})
    attempt = None
    if req.attempt_id is not None:
        if probe is None or probe.user_id != uid:
            raise ApiError(ErrorCode.FORBIDDEN, "no access to this attempt")
        attempt = probe
    else:
        attempt = session.exec(select(Attempt).where(Attempt.user_id == uid, Attempt.problem_slug == req.problem_slug)
                               .order_by(desc(Attempt.id))).first()
    problem = _problem(session, req.problem_slug)
    code = req.code if req.code is not None else (attempt.code if attempt else "")
    lang = normalize_lang(req.language or (attempt.language if attempt else None) or problem.lang_selected)
    ctx = service.Ctx(problem=problem, code=code, selected_code=req.selected_code or "", language=lang,
                      response_language=req.response_language)
    return ctx, uid, attempt


def _envelope(agent: str, result, llm_used: bool, executed: bool, ctx: service.Ctx, **extra) -> dict:
    return {"agent": agent, "result": result.model_dump(), "llm_used": llm_used, "executed": executed,
            "notes": ctx.notes + ([llm.failure_note()] if not llm_used and llm.failure_note() else []), **extra}


@router.post("/explain")
def explain(req: CrewRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    _enabled()
    ctx, _, _ = _context(session, req, token)
    result, llm_used = service.explain(ctx)
    return _envelope("explain", result, llm_used, ctx.python, ctx)


@router.post("/tests")
def tests(req: CrewRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    _enabled()
    ctx, _, _ = _context(session, req, token)
    result, llm_used, executed = service.generate_tests(ctx)
    return _envelope("tests", result, llm_used, executed, ctx)


@router.post("/debug")
def debug(req: CrewRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    _enabled()
    ctx, _, attempt = _context(session, req, token)
    fallback = rules.why_failing({"data": attempt_summary(session, attempt)}) if attempt else None
    result, llm_used, executed = service.debug(ctx, fallback)
    return _envelope("debug", result, llm_used, executed, ctx, fix_code_withheld=not config.CREW_ALLOW_FIX_CODE)


@router.post("/trace")
def trace(req: CrewRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    _enabled()
    ctx, _, _ = _context(session, req, token)
    result, llm_used = service.trace(ctx, req.input, req.expected)
    return _envelope("trace", result, llm_used, result.trace_source == "actual_runtime", ctx)


# ---- Hint Mentor: plugs into POST /hint through the providers seam ----------------------------------------------
def _hint_service(user_id: str, slug: str, level: int, ctx: dict) -> str | None:
    with Session(db.engine) as session:
        row = session.get(LCProblemRow, slug)
        if row is None:
            return None
        attempt = session.exec(select(Attempt).where(Attempt.user_id == user_id, Attempt.problem_slug == slug)
                               .order_by(desc(Attempt.id))).first()
        lang = (ctx or {}).get("language") or "en"
        c = service.Ctx(problem=LCProblem.model_validate_json(row.payload_json),
                        code=attempt.code if attempt else "",
                        language=normalize_lang(attempt.language) if attempt else "python3",
                        response_language=lang if lang in service.LANGUAGES else "en")
        return service.hint(c, level)


if config.FEATURE_CREW:
    providers.register_hint_service(_hint_service)
