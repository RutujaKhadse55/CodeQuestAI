"""Parse LeetCode example text into Python values without executing anything.

  input_text : 'nums = [2,7,11,15], target = 9'  (or multi-line 'nums = [..]\\ntarget = 9')
  output_text: '[0,1]'
Uses a bracket/quote-aware tokenizer and ast.literal_eval only.
"""
import ast
import re
from typing import Any

_IDENT_EQ = re.compile(r"([A-Za-z_]\w*)\s*=(?!=)\s*")
_PREFIX = re.compile(r"^\s*(?:Input|Output|Expected)\s*:\s*", re.I)
_JSON_WORDS = {"true": "True", "false": "False", "null": "None"}


class ParseError(ValueError):
    pass


def _scan(text: str):
    """Yield (index, char, depth, in_str) for every char."""
    depth, quote, esc = 0, None, False
    for i, ch in enumerate(text):
        in_str = quote is not None
        yield i, ch, depth, in_str
        if quote:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "[({":
            depth += 1
        elif ch in "])}":
            depth -= 1


def _normalize(text: str) -> str:
    """true/false/null -> True/False/None outside string literals."""
    out, i = [], 0
    chars = list(_scan(text))
    n = len(text)
    while i < n:
        _, ch, _, in_str = chars[i]
        if not in_str and ch.isalpha():
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            word = text[i:j]
            out.append(_JSON_WORDS.get(word, word))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def parse_value(text: str) -> Any:
    t = _normalize(_PREFIX.sub("", text).strip())
    try:
        return ast.literal_eval(t)
    except (ValueError, SyntaxError) as e:
        raise ParseError(f"cannot parse value: {text[:60]!r}") from e


def parse_inputs(text: str) -> dict[str, Any]:
    """'a = 1, b = [1,2]' -> {'a': 1, 'b': [1, 2]} (insertion order = appearance order)."""
    text = _PREFIX.sub("", text).strip()
    starts: list[tuple[int, int, str]] = []  # (name_start, value_start, name)
    depth_at = {i: (d, s) for i, _, d, s in _scan(text)}
    for m in _IDENT_EQ.finditer(text):
        d, s = depth_at.get(m.start(), (0, False))
        gap = text[:m.start()]
        prev = gap.rstrip()
        if d == 0 and not s and (not prev or prev[-1] in ",;" or "\n" in gap[len(prev):]):
            starts.append((m.start(), m.end(), m.group(1)))
    if not starts:
        raise ParseError(f"no 'name = value' pairs in {text[:60]!r}")
    out: dict[str, Any] = {}
    for k, (_, vstart, name) in enumerate(starts):
        vend = starts[k + 1][0] if k + 1 < len(starts) else len(text)
        raw = text[vstart:vend].strip().rstrip(",;").strip()
        out[name] = parse_value(raw)
    return out


def args_for(params: list[str], parsed: dict[str, Any]) -> list[Any]:
    """Order parsed inputs by the signature's parameter names (positional fallback if counts match)."""
    if params and all(p in parsed for p in params):
        return [parsed[p] for p in params]
    if not params or len(parsed) == len(params):
        return list(parsed.values())
    raise ParseError(f"inputs {list(parsed)} do not match parameters {params}")
