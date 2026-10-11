"""Next-problem recommendation: weakest concept first, from the curated demo list (plan §6 Phase 3)."""
import json
from pathlib import Path

from sqlmodel import Session, select

from ..db.models_core import Attempt, ConceptMastery

CURATED = json.loads((Path(__file__).parent / "curated_problems.json").read_text(encoding="utf-8"))
URL = "https://leetcode.com/problems/{slug}/"


def _solved(session: Session, user_id: str) -> set[str]:
    return {a.problem_slug for a in session.exec(select(Attempt).where(
        Attempt.user_id == user_id, Attempt.passed_all == True)).all()}  # noqa: E712


def _as_result(p: dict, concept: str | None, reason: str) -> dict:
    return {"slug": p["slug"], "title": p["title"], "number": p["number"], "difficulty": p["difficulty"],
            "url": URL.format(slug=p["slug"]), "concept": concept, "reason": reason}


def recommend(session: Session, user_id: str) -> dict:
    solved = _solved(session, user_id)
    ratings = {m.concept: m.rating for m in session.exec(
        select(ConceptMastery).where(ConceptMastery.user_id == user_id)).all()}
    # weakest concepts first; ties broken alphabetically so the answer is deterministic
    for concept, rating in sorted(ratings.items(), key=lambda kv: (kv[1], kv[0])):
        for p in CURATED:
            if concept in p["concepts"] and p["slug"] not in solved:
                return _as_result(p, concept, f"weakest concept: {concept} (rating {rating:.0f})")
    for p in CURATED:  # no history (or every weak-concept problem solved): first unsolved in curated order
        if p["slug"] not in solved:
            return _as_result(p, p["concepts"][0], "next unsolved problem in the curated list")
    return {"slug": None, "title": None, "url": None, "concept": None,
            "reason": "all curated problems solved"}
