"""Backend fallback hardcode detector (AI's `ai/diagnose/hardcode.py` replaces it via providers.register_hardcode).

Static, on the learner's entry function only. Reasons returned:
  constant_return        every `return` yields a literal and the function never reads a parameter
  example_branch         an `if` compares a parameter (or len/index of it) with a literal copied from an example input
  example_output_table   a dict/list literal that contains an example input value next to its example output
"""
import ast
from typing import Any

from .examples_parser import ParseError, parse_inputs, parse_value
from .signature import parse_signature


def _is_literal(node: ast.AST) -> bool:
    try:
        ast.literal_eval(node)
        return True
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return False


def _lit(node: ast.AST) -> Any:
    return ast.literal_eval(node)


def _names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _entry_fn(tree: ast.Module, entry: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == entry:
            return node
    return None


def detect(code: str, examples: list[tuple[str, str]]) -> list[str]:
    """examples: [(input_text, output_text)] as shown on the LeetCode page."""
    sig = parse_signature(code)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    fn = _entry_fn(tree, sig.entry) if sig.entry else None
    if fn is None:
        return []
    params = set(sig.params)
    reasons: list[str] = []

    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value is not None]
    uses_params = bool(_names(fn) & params)
    if returns and all(_is_literal(r.value) for r in returns) and not uses_params:
        reasons.append("constant_return")  # never even reads its inputs

    in_values: list[Any] = []
    out_values: list[Any] = []
    for inp, out in examples:
        try:
            in_values += list(parse_inputs(inp).values())
            out_values.append(parse_value(out))
        except ParseError:
            continue

    for node in ast.walk(fn):
        if isinstance(node, ast.Compare):
            sides = [node.left, *node.comparators]
            lits = [s for s in sides if _is_literal(s)]
            others = [s for s in sides if not _is_literal(s)]
            if lits and others and any(_names(o) & params for o in others):
                for lit in lits:
                    v = _lit(lit)
                    if isinstance(v, (list, tuple, str, dict)) and len(v) > 0 and v in in_values:
                        reasons.append("example_branch")
                        break
        elif isinstance(node, ast.Dict):
            try:
                keys = [_lit(k) for k in node.keys if k is not None]
            except (ValueError, TypeError, SyntaxError):
                continue
            if keys and any(k in in_values for k in keys if isinstance(k, (str, int, tuple))) and len(node.keys) >= 2:
                if any(_is_literal(v) and _lit(v) in out_values for v in node.values):
                    reasons.append("example_output_table")
    return list(dict.fromkeys(reasons))
