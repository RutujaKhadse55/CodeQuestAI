"""AST mutation operators (F-07). Each operator applies ONE small change to a reference solution and yields
(mistake_class, mutated_source). Mistake classes are the contract's MistakeClass values.

Invalid (does not parse/compile) and trivially equivalent (same AST as the reference or an earlier mutant) mutants are
dropped here; behaviourally equivalent ones (identical to the reference on the fixed fuzz set) are dropped by
fingerprint.py once they have been run.
"""
import ast
import copy
from collections.abc import Callable, Iterator

BOUND_NAMES = {"lo", "hi", "low", "high", "left", "right", "l", "r", "i", "j", "k", "mid", "start", "end", "n"}
MAX_PER_CLASS = 8
MAX_MUTANTS = 40

Replacer = Callable[[ast.AST], "list[ast.AST]"]


# ----------------------------------------------------------------------------------------------- helpers
def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}


def _replace(parent: ast.AST, old: ast.AST, new: ast.AST) -> bool:
    for name, value in ast.iter_fields(parent):
        if value is old:
            setattr(parent, name, new)
            return True
        if isinstance(value, list):
            for i, item in enumerate(value):
                if item is old:
                    value[i] = new
                    return True
    return False


def _expr(src: str) -> ast.expr:
    return ast.parse(src, mode="eval").body


def _const_int(node: ast.AST) -> int | None:
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant)
            and type(node.operand.value) is int):
        return -node.operand.value
    return None


def _int_node(v: int) -> ast.expr:
    return _expr(str(v)) if v >= 0 else _expr(f"({v})")


def _is_inf_call(node: ast.AST) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float"
            and len(node.args) == 1 and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in ("inf", "-inf"))


def _mentions_bounds(node: ast.AST) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id in BOUND_NAMES:
            return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "len":
            return True
    return False


def _in_loop_condition(node: ast.AST, parents: dict) -> bool:
    return isinstance(parents.get(node), ast.While)


def _each_site(tree: ast.Module, select: Callable[[ast.AST, dict], bool],
               replacements: Callable[[ast.AST, dict], "list[tuple[str, ast.AST]]"]) -> Iterator[tuple[str, ast.Module]]:
    """For every selected node and every replacement variant, yield a mutated deep copy of the tree."""
    parents = _parent_map(tree)
    sites = [i for i, n in enumerate(ast.walk(tree)) if select(n, parents)]
    for idx in sites:
        probe = list(ast.walk(tree))[idx]
        for v in range(len(replacements(probe, parents))):
            clone = copy.deepcopy(tree)
            cparents = _parent_map(clone)
            node = list(ast.walk(clone))[idx]
            cls, new = replacements(node, cparents)[v]
            if _replace(cparents[node], node, new):
                yield cls, clone


# ----------------------------------------------------------------------------------------------- operators
def op_compare(tree):
    """<= vs <, == vs !=, < vs >, in vs not in. Strict/non-strict flips on bounds are off_by_one_bound."""
    flips = {ast.LtE: [ast.Lt, ast.GtE], ast.Lt: [ast.LtE, ast.Gt], ast.GtE: [ast.Gt, ast.LtE],
             ast.Gt: [ast.GtE, ast.Lt], ast.Eq: [ast.NotEq], ast.NotEq: [ast.Eq], ast.In: [ast.NotIn],
             ast.NotIn: [ast.In]}

    def select(n, p):
        return isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in flips

    def repl(n, p):
        out = []
        old = type(n.ops[0])
        for new in flips[old]:
            boundary = {old, new} in ({ast.Lt, ast.LtE}, {ast.Gt, ast.GtE})
            cls = "off_by_one_bound" if boundary and (_in_loop_condition(n, p) or _mentions_bounds(n)) \
                else "wrong_comparison"
            m = copy.deepcopy(n)
            m.ops = [new()]
            out.append((cls, m))
        return out

    yield from _each_site(tree, select, repl)


def op_off_by_one(tree):
    """x +/- 1 dropped or flipped, range()/slice bounds shifted by one."""
    def select(n, p):
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)) and _const_int(n.right) == 1:
            return True
        par = p.get(n)
        if _const_int(n) is not None and isinstance(par, ast.Slice):
            return True
        if _const_int(n) is not None and isinstance(par, ast.Call) and isinstance(par.func, ast.Name) \
                and par.func.id == "range" and n in par.args:
            return True
        return False

    def repl(n, p):
        if isinstance(n, ast.BinOp):
            flipped = copy.deepcopy(n)
            flipped.op = ast.Sub() if isinstance(n.op, ast.Add) else ast.Add()
            return [("off_by_one_bound", copy.deepcopy(n.left)), ("off_by_one_bound", flipped)]
        v = _const_int(n)
        return [("off_by_one_bound", _int_node(v + 1)), ("off_by_one_bound", _int_node(v - 1))]

    yield from _each_site(tree, select, repl)


def op_operator(tree):
    """Arithmetic/logical operator swaps, swapped operands, max<->min."""
    swaps = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add, ast.FloorDiv: ast.Mult}

    def select(n, p):
        if isinstance(n, ast.BinOp) and type(n.op) in swaps:
            return True
        if isinstance(n, ast.BoolOp):
            return True
        if isinstance(n, ast.AugAssign) and type(n.op) in swaps:
            return True
        return isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("max", "min")

    def repl(n, p):
        out = []
        if isinstance(n, ast.BinOp):
            a = copy.deepcopy(n)
            a.op = swaps[type(n.op)]()
            out.append(("wrong_operator", a))
            if isinstance(n.op, (ast.Sub, ast.FloorDiv)):  # swapped operands
                b = copy.deepcopy(n)
                b.left, b.right = b.right, b.left
                out.append(("wrong_operator", b))
        elif isinstance(n, ast.BoolOp):
            a = copy.deepcopy(n)
            a.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
            out.append(("wrong_operator", a))
        elif isinstance(n, ast.AugAssign):
            a = copy.deepcopy(n)
            a.op = swaps[type(n.op)]()
            out.append(("wrong_operator", a))
        else:
            a = copy.deepcopy(n)
            a.func = ast.Name(id="min" if n.func.id == "max" else "max", ctx=ast.Load())
            out.append(("wrong_operator", a))
        return out

    yield from _each_site(tree, select, repl)


def op_init(tree):
    """Wrong initial value: 0 vs -inf vs 1, nums[0] -> 0, inf swapped."""
    def select(n, p):
        par = p.get(n)
        in_assign = isinstance(par, (ast.Assign, ast.AnnAssign)) and getattr(par, "value", None) is n
        in_tuple = isinstance(par, ast.Tuple) and isinstance(p.get(par), ast.Assign) and p[par].value is par
        if not (in_assign or in_tuple):
            return False
        if _const_int(n) in (0, 1) or _is_inf_call(n):
            return True
        return (isinstance(n, ast.Subscript) and _const_int(n.slice) == 0 and isinstance(n.value, ast.Name))

    def repl(n, p):
        v = _const_int(n)
        if v == 0:
            return [("wrong_init", _expr("float('-inf')")), ("wrong_init", _int_node(1))]
        if v == 1:
            return [("wrong_init", _int_node(0)), ("wrong_init", _int_node(2))]
        if _is_inf_call(n):
            return [("wrong_init", _int_node(0))]
        return [("wrong_init", _int_node(0)), ("wrong_init", _expr("float('-inf')"))]

    yield from _each_site(tree, select, repl)

    # seed taken from nums[0] AND the loop then restarted at index 0: the common "best = 0; for n in nums" shape
    for init in ("0", "float('-inf')"):
        clone = copy.deepcopy(tree)
        changed = False
        for n in list(ast.walk(clone)):
            if (isinstance(n, ast.Assign) and isinstance(n.value, ast.Subscript) and _const_int(n.value.slice) == 0
                    and isinstance(n.value.value, ast.Name)):
                n.value = _expr(init)
                changed = True
        for n in ast.walk(clone):
            if isinstance(n, ast.Slice) and _const_int(n.lower) == 1 and n.upper is None:
                n.lower = None
        if changed:
            yield "wrong_init", clone


def _is_simple_init(stmt: ast.stmt) -> bool:
    if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)):
        return False
    v = stmt.value
    return (isinstance(v, (ast.Constant, ast.Dict, ast.List, ast.Set)) and not getattr(v, "elts", None)
            and not getattr(v, "keys", None)) or _const_int(v) is not None or _is_inf_call(v)


def op_accumulator(tree):
    """Accumulator initialised inside the loop instead of before it; `+=` degraded to `=`; max/min dropped."""
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for body in [b for n in ast.walk(fn) for b in [getattr(n, "body", None)] if isinstance(b, list)]:
            for i, stmt in enumerate(body):
                if not _is_simple_init(stmt):
                    continue
                nxt = next((j for j in range(i + 1, len(body)) if isinstance(body[j], (ast.For, ast.While))), None)
                if nxt is None:
                    continue
                clone = copy.deepcopy(tree)
                cfn = next(n for n in ast.walk(clone) if isinstance(n, ast.FunctionDef) and n.name == fn.name
                           and n.lineno == fn.lineno)
                cbodies = [b for n in ast.walk(cfn) for b in [getattr(n, "body", None)] if isinstance(b, list)]
                cbody = next((b for b in cbodies if len(b) == len(body) and ast.dump(b[i]) == ast.dump(stmt)), None)
                if cbody is None:
                    continue
                init = cbody.pop(i)
                cbody[nxt - 1].body.insert(0, init)
                yield "accumulator_reset", clone

    def sel_aug(n, p):
        return isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name)

    def rep_aug(n, p):
        return [("accumulator_reset", ast.Assign(targets=[copy.deepcopy(n.target)], value=copy.deepcopy(n.value),
                                                 lineno=n.lineno))]

    yield from _each_site(tree, sel_aug, rep_aug)

    def sel_mm(n, p):
        return (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("max", "min")
                and len(n.args) == 2 and isinstance(p.get(n), ast.Assign))

    def rep_mm(n, p):
        return [("accumulator_reset", copy.deepcopy(n.args[0])), ("accumulator_reset", copy.deepcopy(n.args[1]))]

    yield from _each_site(tree, sel_mm, rep_mm)


def _empty_test(test: ast.expr) -> bool:
    src = ast.unparse(test)
    return (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)) or any(
        s in src for s in ("== 0", "< 1", "<= 0", "is None"))


def op_guards(tree):
    """Removed edge-case guard, injected early return on small input, missing/early return."""
    # 1. remove top-level guard `if <cond>: return ...`
    def sel_guard(n, p):
        par = p.get(n)
        return (isinstance(n, ast.If) and not n.orelse and len(n.body) == 1 and isinstance(n.body[0], ast.Return)
                and isinstance(par, ast.FunctionDef))

    def rep_guard(n, p):
        cls = "missing_empty_case" if _empty_test(n.test) else "missing_edge_single"
        return [(cls, ast.Pass())]

    yield from _each_site(tree, sel_guard, rep_guard)

    # 2. injected early return when the input is small (default = the function's last return value)
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        params = [a.arg for a in fn.args.args if a.arg != "self"]
        rets = [n for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value is not None]
        if not params or not rets:
            continue
        p0 = next((p for p in params if f"len({p})" in ast.unparse(fn)), None)
        if p0 is None:
            continue
        default = ast.unparse(rets[-1].value)
        for k in (2, 3):
            clone = copy.deepcopy(tree)
            cfn = next(n for n in ast.walk(clone) if isinstance(n, ast.FunctionDef) and n.name == fn.name
                       and n.lineno == fn.lineno)
            guard = ast.parse(f"if len({p0}) < {k}:\n    return {default}").body[0]
            cfn.body.insert(0, guard)
            yield "missing_edge_single", clone

    # 3. return inside a loop replaced by `pass` (falls through), final `return x` made bare
    def sel_ret(n, p):
        if not (isinstance(n, ast.Return) and n.value is not None):
            return False
        cur, in_loop = p.get(n), False
        while cur is not None and not isinstance(cur, ast.FunctionDef):
            in_loop |= isinstance(cur, (ast.For, ast.While))
            cur = p.get(cur)
        return in_loop or isinstance(p.get(n), ast.FunctionDef)

    def rep_ret(n, p):
        in_loop = not isinstance(p.get(n), ast.FunctionDef)
        return [("missing_edge_single", ast.Pass() if in_loop else ast.Return(value=None))]

    yield from _each_site(tree, sel_ret, rep_ret)


OPERATORS = (op_compare, op_off_by_one, op_init, op_operator, op_accumulator, op_guards)


# ----------------------------------------------------------------------------------------------- public API
def _valid_source(tree: ast.Module) -> str | None:
    try:
        ast.fix_missing_locations(tree)
        src = ast.unparse(tree)
        compile(ast.parse(src), "<mutant>", "exec")
    except (SyntaxError, ValueError, TypeError, RecursionError):
        return None
    return src


def generate_mutants(reference_code: str, max_total: int = MAX_MUTANTS,
                     max_per_class: int = MAX_PER_CLASS) -> list[tuple[str, str]]:
    """[(mistake_class, mutated_source)], deduplicated, capped, interleaved across classes."""
    try:
        tree = ast.parse(reference_code)
    except SyntaxError:
        return []
    base = _valid_source(copy.deepcopy(tree))
    seen = {base}
    by_class: dict[str, list[str]] = {}
    for op in OPERATORS:
        try:
            for cls, mutated in op(tree):
                src = _valid_source(mutated)
                if src is None or src in seen:  # invalid or equivalent to reference / duplicate
                    continue
                seen.add(src)
                by_class.setdefault(cls, []).append(src)
        except Exception:  # noqa: BLE001  (one broken operator must not lose the others)
            continue
    picked: dict[str, list[str]] = {}
    for cls, srcs in by_class.items():
        step = max(1, len(srcs) // max_per_class)
        picked[cls] = srcs[::step][:max_per_class]
    out: list[tuple[str, str]] = []
    depth = 0
    while len(out) < max_total and any(depth < len(v) for v in picked.values()):
        for cls in sorted(picked):
            if depth < len(picked[cls]) and len(out) < max_total:
                out.append((cls, picked[cls][depth]))
        depth += 1
    return out
