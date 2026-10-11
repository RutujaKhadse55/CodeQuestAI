"""Hardcode detector (F-08). Superset of Backend's fallback (engine/hardcode.py): keeps its reasons and adds

  example_if_chain      >= 2 `if` branches that compare a parameter with a value copied from an example input and
                        return a literal (if/elif chains and nested ifs)
  example_lookup_table  a dict literal keyed by >= 2 example inputs (raw values, their text, or tuples of them),
                        whatever the values are
  example_output_return a literal equal to an example's expected output is returned under a literal-vs-parameter test
  len_sum_check         sum(param) matches an example's sum, or >= 2 distinct len(param) checks match example
                        lengths, each returning a literal
  literal_if_chain      >= 4 literal-vs-parameter branches that each return a literal (a table written as code)

Returns reasons as list[str]; never raises.
"""
import ast
from typing import Any

from ...engine import hardcode as base
from ...engine.examples_parser import ParseError, parse_inputs, parse_value
from ...engine.signature import parse_signature


def _lit(node: ast.AST) -> tuple[bool, Any]:
    try:
        return True, ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return False, None


def _norm(v: Any) -> str:
    return "".join(str(v).split()).replace("'", '"')


def _hashable(v: Any) -> Any:
    return tuple(_hashable(x) for x in v) if isinstance(v, (list, tuple)) else v


def _example_data(examples):
    in_vals: list[Any] = []
    in_norm: set[str] = set()
    arg_tuples: list[tuple] = []
    outs: list[Any] = []
    lens: set[int] = set()
    sums: set[Any] = set()
    for inp, out in examples:
        try:
            args = list(parse_inputs(inp).values())
            outs.append(parse_value(out))
        except ParseError:
            continue
        in_vals += args
        arg_tuples.append(tuple(_hashable(a) for a in args))
        for a in args:
            in_norm.add(_norm(a))
            if isinstance(a, (list, tuple, str)):
                lens.add(len(a))
            if isinstance(a, (list, tuple)) and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in a):
                sums.add(sum(a))
    for inp, _ in examples:
        in_norm.add(_norm(inp))
    return in_vals, in_norm, arg_tuples, outs, lens, sums


def _names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _returns_literal(body: list[ast.stmt]) -> tuple[bool, Any]:
    for st in body:
        if isinstance(st, ast.Return) and st.value is not None:
            return _lit(st.value)
        if isinstance(st, ast.If):
            ok, v = _returns_literal(st.body)
            if ok:
                return ok, v
    return False, None


def _compares(test: ast.expr, params: set[str]):
    """Yield (kind, literal) for every `<param-derived> == <literal>` inside `test` (and/or allowed)."""
    for n in ast.walk(test):
        if not (isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], (ast.Eq, ast.Is))):
            continue
        for a, b in ((n.left, n.comparators[0]), (n.comparators[0], n.left)):
            ok, v = _lit(b)
            if not ok or not (_names(a) & params):
                continue
            if isinstance(a, ast.Call) and isinstance(a.func, ast.Name) and a.func.id == "len":
                yield "len", v
            elif isinstance(a, ast.Call) and isinstance(a.func, ast.Name) and a.func.id == "sum":
                yield "sum", v
            else:
                yield "value", v
            break


def detect(code: str, examples: list[tuple[str, str]]) -> list[str]:
    reasons = list(base.detect(code, examples))
    try:
        reasons += _extra(code, examples)
    except Exception:  # noqa: BLE001  (a detector bug must never fail an analysis)
        pass
    return list(dict.fromkeys(reasons))


def _extra(code: str, examples) -> list[str]:
    sig = parse_signature(code)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    fn = base._entry_fn(tree, sig.entry) if sig.entry else None
    if fn is None:
        return []
    params = set(sig.params)
    in_vals, in_norm, arg_tuples, outs, lens, sums = _example_data(examples)
    reasons: list[str] = []

    # --- dict literals keyed by example inputs (raw, textual, or tuple-of-args)
    for node in ast.walk(fn):
        if isinstance(node, ast.Dict) and len(node.keys) >= 2:
            hits = 0
            for k in node.keys:
                if k is None:
                    continue
                ok, v = _lit(k)
                if ok and (_norm(v) in in_norm or _hashable(v) in arg_tuples
                           or (isinstance(v, (int, str, tuple)) and _hashable(v) in [_hashable(x) for x in in_vals])):
                    hits += 1
            if hits >= 2:
                reasons.append("example_lookup_table")

    # --- literal-vs-parameter branches that return literals
    branch_hits = example_hits = out_hits = sum_hit = 0
    len_values: set[int] = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        cmps = list(_compares(node.test, params))
        if not cmps:
            continue
        ok, ret = _returns_literal(node.body)
        if not ok:
            continue
        branch_hits += 1
        matched = False
        for kind, v in cmps:
            if kind == "len" and isinstance(v, int) and v in lens:
                len_values.add(v)
            elif kind == "sum" and v in sums:
                sum_hit += 1
                matched = True
            elif kind == "value" and (_norm(v) in in_norm or _hashable(v) in [_hashable(x) for x in in_vals]):
                matched = True
        nontrivial = (isinstance(ret, (list, tuple, str, dict)) and len(ret) > 0) or (
            isinstance(ret, (int, float)) and not isinstance(ret, bool) and ret not in (0, 1, -1, 2))
        if matched:
            if nontrivial:  # base cases like `if n == 1: return 1` are legitimate
                example_hits += 1
                if any(_hashable(ret) == _hashable(o) for o in outs):
                    out_hits += 1
    if example_hits >= 2:
        reasons.append("example_if_chain")
    if out_hits >= 1 and example_hits >= 1:
        reasons.append("example_output_return")
    if sum_hit >= 1 or len(len_values) >= 2:
        reasons.append("len_sum_check")
    if branch_hits >= 4:
        reasons.append("literal_if_chain")
    return reasons
