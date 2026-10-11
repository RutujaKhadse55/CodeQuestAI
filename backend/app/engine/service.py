"""Engine Protocol implementation (Backend). Phase 1: sandbox_run. fuzz/trace arrive in Phase 2."""
from typing import Any

from ..contracts.models import ReferenceBundle, TestResult
from .examples_parser import ParseError, parse_value
from .sandbox import runner
from .signature import parse_signature


def _canon(v: Any) -> Any:
    if isinstance(v, (list, tuple)):
        return [_canon(x) for x in v]
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
        return float(v)
    return v


def values_equal(actual: Any, expected: Any, comparator: str = "exact") -> bool:
    a, e = _canon(actual), _canon(expected)
    if comparator == "unordered" and isinstance(a, list) and isinstance(e, list):
        try:
            return sorted(a) == sorted(e)
        except TypeError:
            return a == e
    if comparator == "float_tol" and isinstance(a, float) and isinstance(e, (int, float)):
        return abs(a - e) <= 1e-5
    return a == e


class SandboxEngine:
    def sandbox_run(self, code: str, signature: str, tests: list[dict], timeout_s: float = 2.0) -> list[TestResult]:
        """tests: [{"args": [...], "expected_text": str|None, "input_text": str, "kind": "example"|"run_capture",
        "comparator": "exact"|"unordered"|"float_tol"}]. `signature` = starter/learner code or entry name."""
        sig = parse_signature(signature)
        entry = sig.entry or (signature if signature.isidentifier() else None)
        payload = {"code": code, "entry": entry, "tests": [{"args": t["args"]} for t in tests],
                   "timeout_s": timeout_s}
        lines = runner.run(payload, timeout_s * max(len(tests), 1))
        load_error = next((ln["load_error"] for ln in lines if "load_error" in ln), None)
        killed = next((ln["killed"] for ln in lines if "killed" in ln), None)
        by_i = {ln["i"]: ln for ln in lines if "i" in ln}
        results: list[TestResult] = []
        for i, t in enumerate(tests):
            base = dict(kind=t.get("kind", "example"), input=t.get("input_text"), expected=t.get("expected_text"))
            if load_error:
                results.append(TestResult(outcome="runtime_error", error=load_error, **base))
                continue
            r = by_i.get(i)
            if r is None and killed:
                results.append(TestResult(outcome="runtime_error", error=killed, **base))
            elif r is None or r["status"] == "timeout":
                results.append(TestResult(outcome="timeout", error="time limit exceeded", **base))
            elif r["status"] == "error":
                results.append(TestResult(outcome="runtime_error", error=r.get("error"), **base))
            else:
                actual = r["value"]
                ok = False
                if t.get("expected_text") is not None:
                    try:
                        ok = values_equal(actual, parse_value(t["expected_text"]), t.get("comparator", "exact"))
                    except ParseError:
                        ok = False
                results.append(TestResult(outcome="passed" if ok else "wrong_output",
                                          actual=_show(actual), **base))
        return results

    def fuzz(self, learner_code: str, bundle: ReferenceBundle, seed: int, n: int = 200):
        raise NotImplementedError("Phase 2")

    def trace(self, reference_code: str, learner_code: str, args: Any):
        raise NotImplementedError("Phase 2")


def _show(v: Any) -> str:
    import json
    return json.dumps(v, separators=(",", ":"))
