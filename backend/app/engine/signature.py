"""Entry-point and parameter discovery from LeetCode starter code or the learner's own code."""
import ast
import re
from typing import NamedTuple


class Signature(NamedTuple):
    entry: str | None
    params: list[str]
    annotations: dict[str, str]  # param name -> annotation text; "return" -> return annotation


def parse_signature(src: str | None) -> Signature:
    """class Solution -> first public method (self dropped); otherwise the first top-level def."""
    if not src:
        return Signature(None, [], {})
    tree = None
    for candidate in (src, src.rstrip() + "\n        pass\n", src.rstrip() + "\n    pass\n"):
        try:
            tree = ast.parse(candidate)
            break
        except SyntaxError:
            continue
    if tree is None:
        return Signature(None, [], {})
    fn = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            fn = next((n for n in node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")), None)
            if fn:
                break
    if fn is None:
        fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef)), None)
    if fn is None:
        return Signature(None, [], {})
    args = [a for a in fn.args.args if a.arg not in ("self", "cls")]
    ann = {a.arg: ast.unparse(a.annotation) for a in args if a.annotation}
    if fn.returns is not None:
        ann["return"] = ast.unparse(fn.returns)
    return Signature(fn.name, [a.arg for a in args], ann)


_ATOM = {"int", "str", "bool", "float"}


def is_supported_type(ann: str) -> bool:
    """Simple types only: int/str/bool/float and (nested) List/list of those."""
    ann = ann.strip().replace(" ", "")
    m = re.fullmatch(r"(?:List|list)\[(.+)\]", ann)
    if m:
        return is_supported_type(m.group(1))
    return ann in _ATOM


def unsupported_reason(sig: Signature) -> str | None:
    for name, ann in sig.annotations.items():
        if not is_supported_type(ann):
            return f"unsupported type for '{name}': {ann}"
    return None
