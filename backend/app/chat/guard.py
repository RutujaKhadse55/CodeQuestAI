"""Default output Guard for the problem chat (AI's Guard replaces it via providers.register_guard).

Blocks anything that works as a solution: a code block that defines the solution function/class, a long code block,
or code structurally close to the reference solution (identifier/constant-normalised AST similarity >= 0.7).
Short 1-3 line snippets used to explain one idea are allowed.
"""
from __future__ import annotations

import ast
import difflib
import re

from ..contracts.models import GuardResult

MAX_FREE_CODE_LINES = 3
SIMILARITY_BLOCK = 0.7
_FENCE = re.compile(r"```[a-zA-Z0-9_+-]*\n?(.*?)```", re.S)
_DEF = re.compile(r"^\s*(?:class\s+Solution\b|def\s+\w+\s*\(|(?:public|private)?\s*(?:static\s+)?\w[\w<>\[\],]*\s+\w+\s*\([^)]*\)\s*\{)", re.M)


class _Norm(ast.NodeTransformer):
    def visit_Name(self, n):  # noqa: N802
        return ast.copy_location(ast.Name(id="v", ctx=n.ctx), n)

    def visit_arg(self, n):  # noqa: N802
        n.arg = "v"
        n.annotation = None
        return n

    def visit_Constant(self, n):  # noqa: N802
        return ast.copy_location(ast.Constant(value=type(n.value).__name__), n)

    def visit_FunctionDef(self, n):  # noqa: N802
        n.name = "f"
        self.generic_visit(n)
        return n

    def visit_Attribute(self, n):  # noqa: N802
        self.generic_visit(n)
        n.attr = "a"
        return n


def _normalised(code: str) -> str | None:
    try:
        return ast.dump(_Norm().visit(ast.parse(code)))
    except (SyntaxError, ValueError, RecursionError):
        return None


def similarity(code: str, reference: str) -> float:
    a, b = _normalised(code), _normalised(reference)
    return difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def code_blocks(text: str) -> list[str]:
    blocks = [m.group(1) for m in _FENCE.finditer(text)]
    rest = _FENCE.sub("", text)
    if _DEF.search(rest):  # unfenced code that defines a function
        blocks.append(rest)
    return blocks


def violation(text: str, ctx: dict) -> str | None:
    """Reason the text must not be shown, or None."""
    entry, reference = ctx.get("entry"), ctx.get("reference_code") or ""
    for block in code_blocks(text):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if _DEF.search(block) and len(lines) >= 2:
            return "defines_function"
        if len(lines) > MAX_FREE_CODE_LINES:
            return "long_code_block"
        if reference and len(lines) >= 2 and similarity(block, reference) >= SIMILARITY_BLOCK:
            return "similar_to_reference"
    if entry and re.search(r"\bdef\s+" + re.escape(entry) + r"\s*\(", text):
        return "defines_entry_point"
    return None


class DefaultGuard:
    """Implements the Guard Protocol: check(text, ctx) -> GuardResult."""

    def check(self, text: str, ctx: dict) -> GuardResult:
        return GuardResult(passed=violation(text, ctx) is None, retries=0, source="llm")
