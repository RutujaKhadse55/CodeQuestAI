"""Build a language-neutral NeutralMessage from a stored attempt summary (chat.tools.attempt_summary shape) or a
Diagnosis. Carries classes, tier and a short divergence only: no code, no hidden inputs, no expected/actual values."""
from __future__ import annotations

from ...contracts.models import Diagnosis, Divergence, NeutralMessage

PASSED = "passed"
NO_DATA = "no_data"


def _div(d: dict | Divergence | None) -> Divergence | None:
    if d is None:
        return None
    if isinstance(d, Divergence):
        d = d.model_dump()
    keep = {k: d.get(k) for k in ("variable", "iteration", "line") if d.get(k) is not None}
    return Divergence(**keep) if keep else None


def from_diagnosis(d: Diagnosis | None, kind: str = "diagnosis", tier: int | None = None) -> NeutralMessage:
    if d is None:
        return NeutralMessage(kind=kind, tier=tier, concept=NO_DATA)  # type: ignore[arg-type]
    return NeutralMessage(kind=kind, mistake_class=d.mistake_class, failure_class=d.failure_class,  # type: ignore[arg-type]
                          divergence=_div(d.divergence), tier=tier)


def from_summary(summary: dict | None, kind: str = "diagnosis", tier: int | None = None) -> NeutralMessage:
    s = summary or {}
    if not s.get("available", True) or not s:
        return NeutralMessage(kind=kind, tier=tier, concept=NO_DATA)  # type: ignore[arg-type]
    if s.get("passed_all"):
        return NeutralMessage(kind=kind, tier=tier, concept=PASSED)  # type: ignore[arg-type]
    diag = s.get("diagnosis") or {}
    fc = diag.get("failure_class")
    if not fc:  # fall back to a failure class seen on any (non-fuzz) test row
        fc = next((t.get("failure_class") for t in s.get("tests", []) + s.get("fuzz", []) if t.get("failure_class")), None)
    return NeutralMessage(kind=kind, mistake_class=diag.get("mistake_class"), failure_class=fc,  # type: ignore[arg-type]
                          divergence=_div(diag.get("divergence")), tier=tier)
