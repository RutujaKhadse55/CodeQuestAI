"""Divergence tracer: run learner and reference on the SAME input under sys.settrace and report the first
point where a shared variable differs. Pure stdlib; also concatenated into the sandbox harness source.

Alignment: a loop "iteration" is counted by backward jumps in line numbers of the entry function's own frame.
states[j] = variable values after pass j (the snapshot at the start of pass j+1). Only the LEARNER's line is
returned. Step cap 2,000 per run; if hit (or nothing comparable) we fall back to final-output comparison.
"""
import copy
import sys

MAX_STEPS = 2000


class _StepCap(BaseException):
    pass


def _code_of(fn):
    f = getattr(fn, "__func__", fn)
    return f.__code__


class _Rec:
    def __init__(self, code, max_steps):
        self.code, self.max = code, max_steps
        self.root = None
        self.steps = 0
        self.it = 0
        self.last_line = 0
        self.prev_line = None
        self.cur, self.changed, self.starts, self.names = {}, {}, {}, []
        self.final = None
        self.value = None
        self.ok = False
        self.capped = False
        self.exc = None
        self.exc_line = None
        self.ret_line = None

    def _snap(self, frame):
        for k, v in list(frame.f_locals.items()):
            if k == "self" or k.startswith("_"):
                continue
            try:
                r = repr(v)[:200]
            except Exception:  # noqa: BLE001
                r = "<unrepr>"
            if self.cur.get(k) != r:
                self.changed[k] = self.prev_line
                self.cur[k] = r
                if k not in self.names:
                    self.names.append(k)

    def _state(self):
        return {k: (self.cur[k], self.changed.get(k)) for k in self.cur}

    def global_trace(self, frame, event, arg):
        if frame.f_code is not self.code or self.root is not None:
            return None
        self.root = frame
        return self.local_trace

    def local_trace(self, frame, event, arg):
        if frame is not self.root:
            return self.local_trace
        if event == "line":
            self.steps += 1
            if self.steps > self.max:
                raise _StepCap()
            ln = frame.f_lineno
            self.prev_line = self.last_line or None
            self._snap(frame)
            if self.last_line and ln <= self.last_line:
                self.it += 1
                self.starts[self.it] = self._state()
            self.last_line = ln
        elif event == "exception":
            self.exc = f"{arg[0].__name__}: {arg[1]}"[:200]
            self.exc_line = frame.f_lineno
            self.prev_line = self.last_line or None
            self._snap(frame)
            self.final = self._state()
        elif event == "return":
            self.prev_line = self.last_line or None
            self._snap(frame)
            self.final = self._state()
            self.ret_line = self.last_line or None
        return self.local_trace


def _record(fn, args, max_steps):
    rec = _Rec(_code_of(fn), max_steps)
    old = sys.gettrace()
    sys.settrace(rec.global_trace)
    try:
        rec.value = fn(*copy.deepcopy(args))
        rec.ok = True
    except _StepCap:
        rec.capped = True
    except Exception as e:  # noqa: BLE001  (BaseException timeouts must propagate)
        if rec.exc is None:
            rec.exc = f"{type(e).__name__}: {e}"[:200]
    finally:
        sys.settrace(old)
    return rec


def _plain(fn, args):
    try:
        return True, fn(*copy.deepcopy(args))
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"[:200]


def _clip(v):
    return repr(v)[:200]


def trace_compare(learner_fn, ref_fn, args, max_steps=MAX_STEPS):
    """Return {"iteration","variable","expected","actual","line"} for the first divergence, or None."""
    L = _record(learner_fn, args, max_steps)
    R = _record(ref_fn, args, max_steps)
    if R.exc is not None and not R.ok:
        return None
    if L.capped or R.capped:
        lo, lv = _plain(learner_fn, args)
        ro, rv = _plain(ref_fn, args)
        if ro and (not lo or _clip(lv) != _clip(rv)):
            return {"iteration": None, "variable": "<return>", "expected": _clip(rv), "actual": _clip(lv),
                    "line": None}
        return None

    shared = [n for n in R.names if n in set(L.names)]
    l_idx = max(L.starts, default=0) + 1
    r_idx = max(R.starts, default=0) + 1
    l_states, r_states = dict(L.starts), dict(R.starts)
    l_states[l_idx], r_states[r_idx] = L.final, R.final
    top = max(l_idx, r_idx)
    for j in range(1, top + 1):
        a, b = l_states.get(j, L.final), r_states.get(j, R.final)
        if a is None or b is None:
            continue
        for v in shared:
            if v in a and v in b and a[v][0] != b[v][0]:
                it = min(j, top - 1)
                return {"iteration": it or None, "variable": v, "expected": b[v][0], "actual": a[v][0],
                        "line": a[v][1]}
    if L.exc is not None and not L.ok:
        return {"iteration": None, "variable": "<exception>", "expected": _clip(R.value), "actual": L.exc,
                "line": L.exc_line}
    if _clip(L.value) != _clip(R.value):
        return {"iteration": None, "variable": "<return>", "expected": _clip(R.value), "actual": _clip(L.value),
                "line": L.ret_line}
    return None
