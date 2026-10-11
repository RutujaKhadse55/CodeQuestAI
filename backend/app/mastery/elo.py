"""Elo-style concept mastery. Problem difficulty acts as the opponent rating."""

K = 32.0
BASE_RATING = 1000.0
DIFFICULTY_RATING = {"easy": 900.0, "medium": 1100.0, "hard": 1300.0}  # design choice, tune with evidence


def expected(rating: float, opponent: float) -> float:
    return 1.0 / (1.0 + 10 ** ((opponent - rating) / 400.0))


def update(rating: float, opponent: float, success: bool, k: float = K) -> float:
    return rating + k * ((1.0 if success else 0.0) - expected(rating, opponent))


def opponent_for(difficulty: str) -> float:
    return DIFFICULTY_RATING.get((difficulty or "").lower(), 1100.0)
