"""Hint unlock rules (plan §6 P2): level 1 always; 2 after >=2 attempts or 3 min; 3 after >=3 or 6 min;
4 after >=4 or 10 min. Copy-flagged attempts do not count (effort-aware unlock)."""
from datetime import datetime, timezone

from sqlmodel import Session, select

from ..db.models_core import Attempt, HintState

RULES = {2: (2, 180), 3: (3, 360), 4: (4, 600)}  # level -> (attempts, seconds)


def requirements_text(level: int) -> str | None:
    if level not in RULES:
        return None
    n, secs = RULES[level]
    return f"Unlocks after {n} attempts or {secs // 60} minutes on this problem"


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class HintStateService:
    """Implements the HintState Protocol (contracts/protocols.py)."""

    def __init__(self, session: Session):
        self.s = session

    def stats(self, user_id: str, problem_key: str) -> tuple[int, float]:
        rows = self.s.exec(select(Attempt).where(Attempt.user_id == user_id,
                                                  Attempt.problem_slug == problem_key)).all()
        counted = [a for a in rows if not a.copy_flagged]
        if not rows:
            return 0, 0.0
        first = min(_aware(a.created_at) for a in rows)
        wall = (datetime.now(timezone.utc) - first).total_seconds()
        reported = max((a.elapsed_ms for a in rows), default=0) / 1000
        return len(counted), max(wall, reported)

    def allowed_level(self, user_id: str, problem_key: str) -> int:
        attempts, secs = self.stats(user_id, problem_key)
        level = 1
        for lv, (n, t) in RULES.items():
            if attempts >= n or secs >= t:
                level = lv
        return level

    def record_hint(self, user_id: str, problem_key: str, level: int) -> None:
        row = self.s.exec(select(HintState).where(HintState.user_id == user_id,
                                                  HintState.problem_slug == problem_key)).first()
        if row is None:
            row = HintState(user_id=user_id, problem_slug=problem_key)
        row.max_level_given = max(row.max_level_given, level)
        row.updated_at = datetime.now(timezone.utc)
        self.s.add(row)
        self.s.commit()

    def max_level_given(self, user_id: str, problem_key: str) -> int:
        row = self.s.exec(select(HintState).where(HintState.user_id == user_id,
                                                  HintState.problem_slug == problem_key)).first()
        return row.max_level_given if row else 0
