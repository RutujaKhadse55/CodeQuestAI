"""Static AST policy: first line of sandbox defence (the container is the second).

Allowlist imports; reject dangerous builtins, dunder access and process/file/network modules.
"""
import ast
import re
from typing import NamedTuple

ALLOWED_MODULES = frozenset({"math", "collections", "heapq", "itertools", "functools", "bisect", "typing"})
BANNED_NAMES = frozenset({
    "open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "exit", "quit", "help", "memoryview",
})
ALLOWED_DUNDER_ATTRS = frozenset({"__init__"})
# Frame / code / generator / traceback internals are NOT dunder but reach interpreter state
# (e.g. gen.gi_frame.f_back.f_globals -> the harness globals -> real builtins). Rejected outright.
BANNED_ATTRS = frozenset({
    "gi_frame", "gi_code", "gi_yieldfrom", "gi_running", "cr_frame", "cr_code", "cr_await", "ag_frame", "ag_code",
    "f_back", "f_globals", "f_locals", "f_builtins", "f_code", "f_trace", "tb_frame", "tb_next", "tb_lasti",
    "func_globals", "func_code", "co_code", "co_consts", "co_names", "mro",
})
MAX_CODE_CHARS = 20_000
_DUNDER = re.compile(r"^__\w+__$")
_FORMAT_TRAVERSAL = re.compile(r"\{[A-Za-z0-9_]*(?:[.\[]|[^}]*__)")  # "{0.__class__}" / "{0.gi_frame}" / "{0[x]}"


class Violation(NamedTuple):
    line: int
    rule: str
    detail: str

    def as_dict(self) -> dict:
        return {"line": self.line, "rule": self.rule, "detail": self.detail}


def check(code: str) -> list[Violation]:
    """Return violations (empty list = allowed). Syntax errors are left to the harness to report."""
    if len(code) > MAX_CODE_CHARS:
        return [Violation(1, "too_long", f"code exceeds {MAX_CODE_CHARS} characters")]
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return []
    out: list[Violation] = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_MODULES:
                    out.append(Violation(line, "import_not_allowed", a.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] not in ALLOWED_MODULES:
                out.append(Violation(line, "import_not_allowed", node.module or "."))
        elif isinstance(node, ast.Name):
            if node.id in BANNED_NAMES:
                out.append(Violation(line, "banned_builtin", node.id))
            elif _DUNDER.match(node.id):
                out.append(Violation(line, "dunder_access", node.id))
        elif isinstance(node, ast.Attribute):
            if _DUNDER.match(node.attr) and node.attr not in ALLOWED_DUNDER_ATTRS:
                out.append(Violation(line, "dunder_access", node.attr))
            elif node.attr in BANNED_ATTRS:
                out.append(Violation(line, "frame_access", node.attr))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _FORMAT_TRAVERSAL.search(node.value):
                out.append(Violation(line, "format_attribute_traversal", "attribute/index access inside a format string"))
    return out
