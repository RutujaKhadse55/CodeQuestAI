"""Validate a candidate ReferenceBundle in the sandbox. verified=True only when every check passes.

Checks: (1) oracle passes every parseable problem example; (2) generator yields valid inputs and the efficient
reference agrees with the oracle on N generated inputs (sandbox verify mode). Never raises: returns (ok, notes).
"""
from __future__ import annotations

import logging

from ...contracts.models import LCProblem, ReferenceBundle
from ...engine.examples_parser import ParseError, args_for, parse_inputs, parse_value
from ...engine.signature import parse_signature

log = logging.getLogger(__name__)

FUZZ_N = 60
FUZZ_SEED = 424242


def _example_tests(problem: LCProblem, params: list[str], comparator: str) -> list[dict]:
    tests = []
    for ex in problem.examples:
        try:
            args = args_for(params, parse_inputs(ex.input_text))
            parse_value(ex.output_text)
        except ParseError:
            continue
        tests.append({"args": args, "expected_text": ex.output_text, "input_text": ex.input_text,
                      "kind": "example", "comparator": comparator})
    return tests


def validate(problem: LCProblem, bundle: ReferenceBundle, engine=None, n: int = FUZZ_N) -> tuple[bool, str]:
    try:
        if not (bundle.oracle_code.strip() and bundle.reference_code.strip() and bundle.gen_inputs_code.strip()):
            return False, "bundle has empty oracle/reference/generator"
        sig = parse_signature(bundle.oracle_code)
        if sig.entry is None:
            return False, "oracle defines no entry point"
        if parse_signature(bundle.reference_code).entry != sig.entry:
            return False, "reference entry point differs from oracle"
        if engine is None:
            from ...engine.service import SandboxEngine
            engine = SandboxEngine()

        # prefer the problem's starter parameter order; fall back to the oracle's
        params = parse_signature(problem.starter_python).params or sig.params
        tests = _example_tests(problem, params, bundle.comparator)
        if not tests:
            return False, "no parseable problem examples to check the oracle against"
        results = engine.sandbox_run(bundle.oracle_code, bundle.oracle_code, tests, timeout_s=3.0)
        bad = [r for r in results if r.outcome != "passed"]
        if bad:
            return False, f"oracle failed {len(bad)}/{len(results)} problem examples ({bad[0].outcome})"

        fz = engine.fuzz(bundle.reference_code, bundle, FUZZ_SEED, n=n)
        if not fz.ran:
            return False, "generator/oracle produced no valid inputs: " + ", ".join(fz.flags or ["unknown"])
        if fz.failures:
            return False, f"reference disagreed with oracle on {fz.failures}/{fz.run} generated inputs"
        if fz.run < max(1, n // 2):
            return False, f"generator yielded too few valid inputs ({fz.run}/{n})"
        return True, f"verified: oracle passed {len(results)} examples; reference agreed on {fz.run} fuzz inputs"
    except Exception as exc:  # noqa: BLE001 - sandbox down, bad payload, ...
        log.warning("reference validation error: %s", type(exc).__name__)
        return False, f"validation unavailable ({type(exc).__name__})"
