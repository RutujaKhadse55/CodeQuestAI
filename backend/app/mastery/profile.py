"""Backend's basic learner profile (habits), used until AI's LearnerModel.summary is registered."""
from collections import Counter
from statistics import median

from sqlmodel import Session, select

from ..db.models_core import Attempt, DiagnosisRow, UserMistakeCount

EDGE_CLASSES = {"empty", "single_element"}


def basic_profile(session: Session, user_id: str) -> dict:
    attempts = session.exec(select(Attempt).where(Attempt.user_id == user_id).order_by(Attempt.id)).all()
    n = len(attempts)
    if n == 0:
        return {"attempts": 0, "solved": 0, "habits": {}, "top_mistakes": [], "source": "backend-basic"}
    by_problem: dict[str, list[Attempt]] = {}
    for a in attempts:
        by_problem.setdefault(a.problem_slug, []).append(a)
    to_pass = []
    for rows in by_problem.values():
        idx = next((i for i, a in enumerate(rows) if a.passed_all), None)
        if idx is not None:
            to_pass.append(idx + 1)
    diags = session.exec(select(DiagnosisRow).where(DiagnosisRow.attempt_id.in_([a.id for a in attempts]))).all()
    classes = Counter(d.failure_class for d in diags if d.failure_class)
    mistakes = session.exec(select(UserMistakeCount).where(UserMistakeCount.user_id == user_id)
                            .order_by(UserMistakeCount.count.desc())).all()
    times = [a.elapsed_ms for a in attempts if a.elapsed_ms]
    return {
        "attempts": n,
        "solved": len(to_pass),
        "habits": {
            "paste_rate": round(sum(1 for a in attempts if a.paste_chars > 0) / n, 2),
            "edge_case_miss_rate": round(sum(classes[c] for c in EDGE_CLASSES) / max(len(diags), 1), 2),
            "avg_attempts_to_pass": round(sum(to_pass) / len(to_pass), 1) if to_pass else None,
            "median_elapsed_s": round(median(times) / 1000, 1) if times else None,
        },
        "top_mistakes": [{"mistake_class": m.mistake_class, "count": m.count} for m in mistakes[:3]],
        "source": "backend-basic",
    }
