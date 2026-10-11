from fastapi import APIRouter

from ..engine import ast_policy
from ..engine.attacks import ATTACKS
from ..engine.sandbox.runner import SandboxUnavailable
from ..engine.service import SandboxEngine

router = APIRouter()
_engine = SandboxEngine()


def run_attack(name: str, code: str) -> dict:
    v = ast_policy.check(code)
    if v:
        return {"name": name, "blocked": True, "by": "policy", "detail": v[0].rule}
    try:
        r = _engine.sandbox_run(code, "f", [{"args": [[1]], "kind": "example", "input_text": "nums = [1]",
                                              "expected_text": "1"}], timeout_s=2.0)[0]
    except SandboxUnavailable as e:
        return {"name": name, "blocked": False, "by": "sandbox", "detail": f"unavailable: {e}"}
    return {"name": name, "blocked": r.outcome in ("timeout", "runtime_error"), "by": "sandbox", "detail": r.outcome}


@router.get("/admin/attacks")
def attacks():
    """Runs the attack set; every entry must report blocked=true (evidence: sandbox_attacks.md)."""
    results = [run_attack(n, c) for n, c in ATTACKS.items()]
    return {"total": len(results), "blocked": sum(r["blocked"] for r in results), "results": results}
