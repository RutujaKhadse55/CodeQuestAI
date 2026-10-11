import pytest

from app.agents.evals import agent_safety_eval as ev
from app.agents.evals.injection_tests import INJECTIONS
from app.chat.lang import is_policy_override, is_solution_request


@pytest.mark.parametrize("text", INJECTIONS)
def test_each_injection_refused(text):
    assert is_policy_override(text) or is_solution_request(text)


def test_full_block_rate():
    r = ev.run()
    assert r["block_rate"] == 1.0, r
    assert len(INJECTIONS) >= 20


def test_mentor_reexports():
    from app.agents.mentor import agent, intents, rule_based
    from app.chat import agent as ca
    assert agent.respond is ca.respond
    assert intents.classify_intent("give me the full solution") == "solution_request"
    assert hasattr(rule_based, "REFUSAL")
