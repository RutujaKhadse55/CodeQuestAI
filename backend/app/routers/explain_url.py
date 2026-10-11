"""POST /explain/problem {url, username?, selected_text?, response_language?, code?} (behind FEATURE_CREW).

The learner gives a LeetCode problem link (and optionally their LeetCode username). The backend fetches the PUBLIC problem
itself, stores it like a captured problem, and returns a structured explanation of THAT problem, personalised with the
learner's public profile when permission exists. A username typed into this form counts as the learner's explicit
permission (the form says so) and is recorded exactly like POST /chat/consent. No full solution is ever returned.
"""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, desc, select

from .. import config, lcfetch
from ..auth import resolve_user, user_token_header
from ..chat import service as chat_service
from ..contracts.enums import ErrorCode
from ..crew import llm, service
from datetime import datetime, timezone

from ..db.models_core import Attempt, LCProblemRow, LearnerContext
from ..deps import get_session
from ..errors import ApiError
from ..engine.lang import normalize_lang
from .problems import capture

router = APIRouter(tags=["explain"])


class ExplainUrlRequest(BaseModel):
    url: str = Field(min_length=10, max_length=300)
    username: str | None = Field(default=None, max_length=40)
    selected_text: str | None = Field(default=None, max_length=3000)
    code: str | None = Field(default=None, max_length=20_000)
    language: str | None = Field(default=None, max_length=30)
    response_language: Literal["en", "hi", "mr", "hinglish"] = "en"
    user_id: str | None = None


def _profile_text(session: Session, uid: str) -> tuple[str, str | None]:
    st = chat_service.consent_status(session, uid)
    if not st["granted"] or not st.get("summary"):
        return "", st.get("leetcode_username")
    s = st["summary"]
    parts = [f"LeetCode username: {st['leetcode_username']}"]
    if s.get("solved"):
        parts.append("Solved: " + ", ".join(f"{k}={v}" for k, v in s["solved"].items()))
    if s.get("top_languages"):
        parts.append("Top languages: " + ", ".join(f"{x['language']} ({x['solved']})" for x in s["top_languages"][:3]))
    if s.get("streak") is not None:
        parts.append(f"Streak: {s['streak']} days")
    return "\n".join(parts), st["leetcode_username"]


def _remember(session: Session, uid: str, slug: str, title: str | None, username: str | None) -> None:
    """Persist the learner's current problem (+ LeetCode username) so every other tab / endpoint can use it."""
    row = session.get(LearnerContext, uid) or LearnerContext(user_id=uid, problem_slug=slug, problem_url="")
    row.problem_slug, row.problem_url = slug, f"https://leetcode.com/problems/{slug}/"
    row.problem_title, row.updated_at = title, datetime.now(timezone.utc)
    if username:
        row.leetcode_username = username
    session.add(row)
    session.commit()


def current_context(session: Session, uid: str) -> dict | None:
    row = session.get(LearnerContext, uid)
    return None if row is None else {"problem_slug": row.problem_slug, "problem_url": row.problem_url,
                                     "problem_title": row.problem_title, "leetcode_username": row.leetcode_username,
                                     "updated_at": row.updated_at.isoformat()}


class ContextRequest(BaseModel):
    url: str = Field(min_length=10, max_length=300)
    user_id: str | None = None


@router.get("/context")
def get_context(user_id: str | None = None, session: Session = Depends(get_session),
                token: str = Depends(user_token_header)):
    """The learner's current problem URL / slug / username (None if none chosen yet)."""
    return {"context": current_context(session, resolve_user(session, user_id, token))}


@router.post("/context")
def set_context(req: ContextRequest, session: Session = Depends(get_session), token: str = Depends(user_token_header)):
    """Select the current problem by URL without fetching it (the problem must already be captured or be fetched later)."""
    uid = resolve_user(session, req.user_id, token)
    try:
        slug = lcfetch.slug_from_url(req.url)
    except lcfetch.FetchError as e:
        raise ApiError(ErrorCode.VALIDATION_ERROR, str(e)) from e
    row = session.get(LCProblemRow, slug)
    _remember(session, uid, slug, row.title if row else None, None)
    return {"context": current_context(session, uid)}


@router.post("/explain/problem")
def explain_problem(req: ExplainUrlRequest, session: Session = Depends(get_session),
                    token: str = Depends(user_token_header)):
    if not config.FEATURE_CREW:
        raise ApiError(ErrorCode.UPSTREAM_FAILED, "the AI crew is disabled (set FEATURE_CREW=1)")
    uid = resolve_user(session, req.user_id, token)
    try:
        slug = lcfetch.slug_from_url(req.url)
    except lcfetch.FetchError as e:
        raise ApiError(ErrorCode.VALIDATION_ERROR, str(e)) from e

    # 1. the problem: fetch by URL; if LeetCode is unreachable fall back to a copy captured earlier
    source = "fetched"
    try:
        capture(lcfetch.fetch_problem(req.url), session)
    except lcfetch.FetchError as e:
        if session.get(LCProblemRow, slug) is None:
            raise ApiError(ErrorCode.UPSTREAM_FAILED, f"{e}. Open the problem page once so it can be captured.") from e
        source = "stored"
    row = session.get(LCProblemRow, slug)
    from ..contracts.models import LCProblem
    problem = LCProblem.model_validate_json(row.payload_json)

    # 2. the learner: an entered username is the learner's explicit permission to use their PUBLIC profile
    profile_notice = None
    if req.username and req.username.strip():
        st = chat_service.consent_status(session, uid)
        if not st["granted"] or (st["leetcode_username"] or "").lower() != req.username.strip().lower():
            out = chat_service.grant_consent(session, uid, req.username.strip())
            if out.get("sync_error"):
                profile_notice = "Permission saved, but the profile could not be fetched: " + str(out["sync_error"].get("message"))
    profile, username = _profile_text(session, uid)
    _remember(session, uid, problem.slug, problem.title, username)

    # 3. the learner's latest code for this problem (optional context)
    code = req.code
    if code is None:
        a = session.exec(select(Attempt).where(Attempt.user_id == uid, Attempt.problem_slug == slug)
                         .order_by(desc(Attempt.id))).first()
        code = a.code if a else ""
    ctx = service.Ctx(problem=problem, code=code or "", language=normalize_lang(req.language or problem.lang_selected),
                      response_language=req.response_language, profile=profile, focus=req.selected_text or "")
    result, llm_used = service.explain(ctx)
    return {"problem": {"slug": problem.slug, "title": problem.title, "difficulty": problem.difficulty,
                        "tags": problem.tags, "url": f"https://leetcode.com/problems/{problem.slug}/"},
            "explanation": result.model_dump(), "llm_used": llm_used, "source": source,
            "personalised": bool(profile), "username": username, "notes": ctx.notes + ([profile_notice] if profile_notice else []) + ([llm.failure_note()] if not llm_used and llm.failure_note() else [])}
