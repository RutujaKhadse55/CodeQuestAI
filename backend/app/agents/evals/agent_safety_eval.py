"""Runnable safety eval: `python -m app.agents.evals.agent_safety_eval` prints the block rate."""
from ...chat import guard
from ...chat.lang import is_policy_override, is_solution_request
from .injection_tests import BAD_OUTPUTS, GUARD_CTX, INJECTIONS


def run() -> dict:
    missed_in = [t for t in INJECTIONS if not (is_policy_override(t) or is_solution_request(t))]
    missed_out = [t for t in BAD_OUTPUTS if guard.violation(t, GUARD_CTX) is None]
    total = len(INJECTIONS) + len(BAD_OUTPUTS)
    missed = len(missed_in) + len(missed_out)
    return {"total": total, "blocked": total - missed, "block_rate": (total - missed) / total,
            "missed_inputs": missed_in, "missed_outputs": missed_out}


if __name__ == "__main__":
    r = run()
    print(f"block rate {r['blocked']}/{r['total']} = {r['block_rate']:.0%}")
    for m in r["missed_inputs"] + r["missed_outputs"]:
        print("MISSED:", m[:80])
