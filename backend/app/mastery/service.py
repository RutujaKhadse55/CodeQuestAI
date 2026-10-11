"""Applies Elo updates per concept (LeetCode topic tags) and tracks mistake counts. Implements Mastery Protocol."""
import json

from sqlmodel import Session, select

from ..db.models_core import (Attempt, ConceptMastery, LCProblemRow, UserMistakeCount)
from . import elo


class MasteryService:
    def __init__(self, session: Session):
        self.s = session

    def _concepts(self, slug: str) -> tuple[list[str], str]:
        row = self.s.get(LCProblemRow, slug)
        if row is None:
            return ["general"], "medium"
        tags = json.loads(row.payload_json).get("tags") or []
        return [t.strip().lower() for t in tags][:4] or ["general"], row.difficulty

    def apply_attempt(self, a: Attempt) -> None:
        """Update every concept of the problem. Re-passing an already-passed problem is not rewarded again."""
        if a.passed_all:
            earlier = self.s.exec(select(Attempt).where(Attempt.user_id == a.user_id,
                                                         Attempt.problem_slug == a.problem_slug,
                                                         Attempt.passed_all == True,  # noqa: E712
                                                         Attempt.id != a.id)).first()
            if earlier is not None:
                return
        concepts, difficulty = self._concepts(a.problem_slug)
        opp = elo.opponent_for(difficulty)
        for c in concepts:
            row = self.s.exec(select(ConceptMastery).where(ConceptMastery.user_id == a.user_id,
                                                           ConceptMastery.concept == c)).first()
            if row is None:
                row = ConceptMastery(user_id=a.user_id, concept=c, rating=elo.BASE_RATING)
            row.rating = round(elo.update(row.rating, opp, a.passed_all), 2)
            self.s.add(row)
        self.s.commit()

    def record_mistake(self, user_id: str, mistake_class: str) -> None:
        row = self.s.exec(select(UserMistakeCount).where(UserMistakeCount.user_id == user_id,
                                                          UserMistakeCount.mistake_class == mistake_class)).first()
        if row is None:
            row = UserMistakeCount(user_id=user_id, mistake_class=mistake_class)
        row.count += 1
        self.s.add(row)
        self.s.commit()

    def release_pending(self, user_id: str, attempt_id: int) -> None:
        """Explain-back passed: apply the deferred mastery update of a copy-flagged attempt."""
        a = self.s.get(Attempt, attempt_id)
        if a is None or a.user_id != user_id or not a.mastery_pending:
            return
        a.mastery_pending = False
        self.s.add(a)
        self.s.commit()
        self.apply_attempt(a)
