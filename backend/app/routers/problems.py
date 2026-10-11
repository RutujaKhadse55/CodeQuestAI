from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..contracts.models import CaptureResponse, LCProblem
from ..db.models_core import LCProblemRow
from ..deps import get_session
from ..engine.lang import normalize_lang
from ..engine.signature import parse_signature, unsupported_reason

router = APIRouter()
MAX_STATEMENT_CHARS = 8000


def supported_decision(p: LCProblem) -> tuple[bool, str | None]:
    """Only python3 + simple types are executed; everything else is explanation-only."""
    if normalize_lang(p.lang_selected) != "python3":
        return False, "UNSUPPORTED_LANGUAGE"
    why = unsupported_reason(parse_signature(p.starter_python))
    if why:
        return False, f"UNSUPPORTED_TYPE: {why}"
    return True, None


@router.post("/problems/capture", response_model=CaptureResponse)
def capture(problem: LCProblem, session: Session = Depends(get_session)):
    """Idempotent by (slug, content_hash, language): the same capture returns the stored decision."""
    problem = problem.model_copy(update={"statement_text": problem.statement_text[:MAX_STATEMENT_CHARS]})
    row = session.get(LCProblemRow, problem.slug)
    if row and row.content_hash == problem.content_hash and normalize_lang(row.lang_selected) == normalize_lang(problem.lang_selected):
        return CaptureResponse(problem_id=row.slug, slug=row.slug, supported=row.supported, reason=row.reason)
    supported, reason = supported_decision(problem)
    data = dict(slug=problem.slug, title=problem.title, difficulty=problem.difficulty,
                content_hash=problem.content_hash, lang_selected=problem.lang_selected,
                supported=supported, reason=reason, payload_json=problem.model_dump_json())
    if row:
        for k, v in data.items():
            setattr(row, k, v)
    else:
        row = LCProblemRow(**data)
    session.add(row)
    session.commit()
    return CaptureResponse(problem_id=problem.slug, slug=problem.slug, supported=supported, reason=reason)
