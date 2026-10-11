"""Engine Protocol implementation (Backend). Phase 1: sandbox_run. fuzz/trace arrive in Phase 2."""
import math
from dataclasses import dataclass, field
from typing import Any

from ..contracts.models import Divergence, ReferenceBundle, TestResult
from .examples_parser import ParseError, parse_value
from .sandbox import runner
from .signature import parse_signature


@dataclass
class FuzzResult:
    """Summary of a differential fuzz run. Never contains an input value (hidden-test secrecy)."""
    seed: int
    run: int = 0
    failures: int = 0
    first_kind: str | None = None          # wrong_output | runtime_error | timeout
    failure_class: str | None = None       # bucket of the SHRUNK failing input
    divergence: Divergence | None = None
    vector: str = ""                       # fixed-seed 0/1 pass-fail vector (mutation fingerprints)
    flags: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.run > 0 and self.failures == 0

    @property
    def ran(self) -> bool:
        return self.run > 0


def _canon(v: Any) -> Any:
    if isinstance(v, (list, tuple)):
        return [_canon(x) for x in v]
    if isinstance(v, float) and math.isfinite(v) and v == int(v) and abs(v) < 1e15:
        return float(v)  # NaN / +-inf stay as they are (int(nan) raises)
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


FINGERPRINT_SEED = 20261011  # fixed: every fingerprint is computed on the same input set
FINGERPRINT_N = 64
FUZZ_BUDGET_S = 15.0


class SandboxEngine:
    @staticmethod
    def _run_payload(code: str, signature: str, tests: list[dict], timeout_s: float) -> dict:
        sig = parse_signature(signature)
        entry = sig.entry or (signature if signature.isidentifier() else None)
        return {"code": code, "entry": entry, "tests": [{"args": t["args"]} for t in tests],
                "timeout_s": timeout_s}

    @staticmethod
    def _parse_results(tests: list[dict], lines: list[dict]) -> list[TestResult]:
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

    def sandbox_run(self, code: str, signature: str, tests: list[dict], timeout_s: float = 2.0) -> list[TestResult]:
        """tests: [{"args": [...], "expected_text": str|None, "input_text": str, "kind": "example"|"run_capture",
        "comparator": "exact"|"unordered"|"float_tol"}]. `signature` = starter/learner code or entry name."""
        payload = self._run_payload(code, signature, tests, timeout_s)
        return self._parse_results(tests, runner.run(payload, timeout_s * max(len(tests), 1)))

    @staticmethod
    def _verify_payload(code: str, entry: str, bundle: ReferenceBundle, seed: int, n: int) -> dict:
        return {"mode": "verify", "code": code, "entry": entry, "oracle_code": bundle.oracle_code,
                "reference_code": bundle.reference_code, "gen_code": bundle.gen_inputs_code,
                "comparator": bundle.comparator, "seed": seed, "fp_seed": FINGERPRINT_SEED, "n": n,
                "fp_n": FINGERPRINT_N, "budget_s": FUZZ_BUDGET_S}

    @staticmethod
    def _parse_fuzz(seed: int, lines: list[dict]) -> FuzzResult:
        res = FuzzResult(seed=seed)
        err = next((ln["load_error"] for ln in lines if "load_error" in ln), None)
        v = next((ln["verify"] for ln in lines if "verify" in ln), None)
        if err or v is None:
            res.flags.append("fuzz_unavailable")
            if err:
                res.flags.append(f"fuzz_error: {err[:120]}")
            return res
        res.run, res.failures = v["run"], v["failures"]
        res.first_kind, res.failure_class, res.vector = v["first_kind"], v["failure_class"], v["vector"]
        if v.get("divergence"):
            res.divergence = Divergence(**v["divergence"])
        if v["run"] == 0:
            res.flags.append("generator_produced_no_valid_inputs")
        if v.get("budget_hit"):
            res.flags.append("fuzz_budget_hit")
        return res

    def run_and_fuzz(self, code: str, tests: list[dict], bundle: ReferenceBundle, seed: int, n: int = 200,
                     timeout_s: float = 2.0) -> tuple[list[TestResult], FuzzResult]:
        """Examples + differential fuzz + shrink + trace in ONE container start (saves ~0.5 s per /analyze)."""
        sig = parse_signature(code)
        if sig.entry is None:
            res = FuzzResult(seed=seed)
            res.flags.append("no_entry_point")
            return [], res
        payload = {**self._run_payload(code, code, tests, timeout_s),
                   **self._verify_payload(code, sig.entry, bundle, seed, n), "mode": "both"}
        lines = runner.run(payload, timeout_s * max(len(tests), 1) + FUZZ_BUDGET_S + 30)
        return self._parse_results(tests, lines), self._parse_fuzz(seed, lines)

    def fuzz(self, learner_code: str, bundle: ReferenceBundle, seed: int, n: int = 200) -> FuzzResult:
        """Differential fuzz vs the oracle (fresh `seed` per attempt, stored, never shown) + shrink + trace."""
        sig = parse_signature(learner_code)
        if sig.entry is None:
            res = FuzzResult(seed=seed)
            res.flags.append("no_entry_point")
            return res
        lines = runner.run(self._verify_payload(learner_code, sig.entry, bundle, seed, n), FUZZ_BUDGET_S + 30)
        return self._parse_fuzz(seed, lines)

    def trace(self, reference_code: str, learner_code: str, args: Any) -> Divergence | None:
        sig = parse_signature(learner_code)
        lines = runner.run({"mode": "trace", "code": learner_code, "reference_code": reference_code,
                            "entry": sig.entry, "args": args}, 15)
        d = next((ln["trace"] for ln in lines if "trace" in ln), None)
        return Divergence(**d) if d else None


def _show(v: Any) -> str:
    import json
    return json.dumps(v, separators=(",", ":"))
