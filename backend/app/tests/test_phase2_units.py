from app.engine.copy_detector import is_copy
from app.engine.hint_state import RULES, requirements_text
from app.mastery import elo


def test_copy_detector():
    assert is_copy(500, 600, 5_000, True)
    assert not is_copy(500, 600, 5_000, False)        # not a pass
    assert not is_copy(50, 600, 5_000, True)          # small paste
    assert not is_copy(130, 600, 5_000, True)         # paste is a small share of the code
    assert not is_copy(500, 600, 400_000, True)       # not quick
    assert not is_copy(500, 600, 0, True)             # elapsed unknown -> do not accuse


def test_hint_rules_text():
    assert set(RULES) == {2, 3, 4} and RULES[4] == (4, 600)
    assert requirements_text(2) == "Unlocks after 2 attempts or 3 minutes on this problem"
    assert requirements_text(1) is None


def test_elo_direction_and_symmetry():
    r = elo.BASE_RATING
    assert elo.update(r, 1100, True) > r > elo.update(r, 1100, False)
    assert abs((elo.update(1000, 1000, True) - 1000) - 16) < 1e-9
    assert elo.update(1000, 1300, True) - 1000 > elo.update(1000, 900, True) - 1000  # harder win pays more
