import pytest

from conftest import needs_sandbox
from app.engine.attacks import ATTACKS, SANDBOX_CONTAINED
from app.routers.admin_attacks import run_attack
from app.engine import ast_policy

POLICY_BLOCKED = [n for n in ATTACKS if n not in SANDBOX_CONTAINED]


@pytest.mark.parametrize("name", POLICY_BLOCKED)
def test_policy_blocks_attack(name):
    assert ast_policy.check(ATTACKS[name]), f"{name} was not rejected by the policy"


def test_attack_set_size():
    assert len(ATTACKS) >= 7


@needs_sandbox
@pytest.mark.parametrize("name", sorted(SANDBOX_CONTAINED))
def test_sandbox_contains_attack(name):
    r = run_attack(name, ATTACKS[name])
    assert r["blocked"], r


@needs_sandbox
def test_all_attacks_blocked_end_to_end():
    results = [run_attack(n, c) for n, c in ATTACKS.items()]
    assert all(r["blocked"] for r in results), results
