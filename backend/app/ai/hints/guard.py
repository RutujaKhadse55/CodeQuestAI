"""Hint Guard v1: extract code -> block full function definitions -> AST similarity to the reference -> regex ->
no code at tiers <= 3 (tier 4 is words/gapped pseudocode, never code) -> up to 2 regenerations -> template.

Reuses chat/guard.py `violation()` (defines_function, long_code_block, similar_to_reference, defines_entry_point).
Implements the Guard Protocol: `check(text, ctx) -> GuardResult`; ctx may carry `allowed_hint_level`, `entry`,
`reference_code`. Running candidate code against tests (sandbox) is not done here [NOT DONE: needs Engine wiring].
"""
from __future__ import annotations

import re
from typing import Callable

from ...chat.guard import code_blocks, violation
from ...contracts.models import GuardResult

MAX_REGENERATIONS = 2
_FENCE = re.compile(r"```")
# a line that is a Python/C-style statement, not prose
_STATEMENT = re.compile(r"^\s*(?:def\s+\w+\s*\(|class\s+\w+|(?:for|while|if|elif|else|try|except|with)\b[^\n]*:\s*$|"
                        r"return\b[^\n]*[\w\)\]]\s*$|import\s+\w+|from\s+\w+\s+import\b|[\w\.\[\]]+\s*(?:[+\-*/%]|//)?=\s*[^=\n]+$)",
                        re.M)
_CODEISH = re.compile(r"[\w\]\)]\s*(?:\+=|-=|\*=|==|!=)\s*\S|\w+\([^)\n]*\)\s*:\s*$", re.M)


def hint_violation(text: str, level: int, ctx: dict | None = None) -> str | None:
    """Reason this hint text must not be shown at `level`, or None."""
    ctx = ctx or {}
    if not (text or "").strip():
        return "empty"
    reason = violation(text, ctx)
    if reason:
        return reason
    if _FENCE.search(text):
        return "code_fence"  # no code blocks at any hint tier; tier 4 is pseudocode in words
    if level <= 3 and (_STATEMENT.search(text) or _CODEISH.search(text)):
        return "code_at_low_tier"
    if level == 4 and len([ln for ln in text.splitlines() if _STATEMENT.match(ln)]) >= 2:
        return "code_like_pseudocode"
    return None


class HintGuard:
    """Guard Protocol implementation usable for hints, explanations and translations."""

    def check(self, text: str, ctx: dict | None = None) -> GuardResult:
        ctx = ctx or {}
        level = ctx.get("allowed_hint_level") or ctx.get("level") or 4
        if ctx.get("allow_code_free") is False:  # reserved
            level = 3
        return GuardResult(passed=hint_violation(text, int(level), ctx) is None, retries=0, source="llm")


def guarded_hint(generate: Callable[[int], str | None], level: int, ctx: dict | None,
                 template: Callable[[], str]) -> tuple[str, GuardResult]:
    """Run `generate(attempt)` up to 1 + MAX_REGENERATIONS times; first text passing the guard wins, else the template.

    A generator that raises or returns None counts as a failed attempt and stops early (no point retrying a dead LLM).
    """
    retries = 0
    for attempt in range(MAX_REGENERATIONS + 1):
        try:
            text = generate(attempt)
        except Exception:  # noqa: BLE001
            text = None
        if text is None:
            break
        text = text.strip()
        if hint_violation(text, level, ctx) is None:
            return text, GuardResult(passed=True, retries=retries, source="llm")
        retries += 1
    return template(), GuardResult(passed=True, retries=retries, source="template")


def extract_code(text: str) -> list[str]:
    return code_blocks(text)
