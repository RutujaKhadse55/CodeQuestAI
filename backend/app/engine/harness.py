"""Sandbox harness. Runs INSIDE the container (Linux), never imported by the API process.

The runner sends shrinker.py + tracer/tracer.py + this file as ONE source, so this file may use the names
`shrink`, `classify_failure` and `trace_compare` without importing them.

Modes (stdin JSON, "mode" key):
  run    {"code","entry","tests":[{"args"}],"timeout_s"}  -> one JSON line per test (+ load_error)
  verify {"code","entry","oracle_code","reference_code","gen_code","comparator","seed","fp_seed","n","fp_n",
          "budget_s"} -> {"verify": {...summary...}}  (differential fuzz vs oracle, shrink, classify, trace).
         Raw fuzz inputs NEVER leave the container: only counts, a 0/1 vector, a failure class and a divergence.
  both   run + verify payload merged: one container start for /analyze
  trace  {"code","reference_code","entry","args"} -> {"trace": divergence|null}
Learner stdout/stderr is captured and discarded so it cannot forge result lines.
"""
import builtins
import copy
import json
import random
import signal
import sys
import time

ALLOWED = {"math", "collections", "heapq", "itertools", "functools", "bisect", "typing"}
BLOCKED_BUILTINS = {"open", "exec", "eval", "compile", "input", "breakpoint", "exit", "quit", "help",
                    "globals", "locals", "vars", "getattr", "setattr", "delattr", "memoryview"}
PRELUDE = (
    "from typing import *\n"
    "import collections, math, heapq, itertools, functools, bisect\n"
    "from collections import deque, defaultdict, Counter, OrderedDict\n"
    "from heapq import heappush, heappop, heapify\n"
    "from bisect import bisect_left, bisect_right\n"
    "from functools import lru_cache, cache\n"
)
MAX_VALUE_CHARS = 10_000
FUZZ_CALL_LIMIT_S = 1.0
MAX_TIMEOUTS = 3
MAX_FAIL_KEEP = 25


class _Timeout(BaseException):  # BaseException so learner `except Exception` cannot swallow it
    pass


class _Sink:
    def write(self, s):
        return len(s)

    def flush(self):
        pass


def _on_alarm(signum, frame):
    raise _Timeout()


_real_import = builtins.__import__
_real_exec, _real_compile = builtins.exec, builtins.compile


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name.split(".")[0] not in ALLOWED:
        raise ImportError(f"import of '{name}' is not allowed")
    return _real_import(name, globals, locals, fromlist, level)


def _load(code):
    """Fresh namespace with restricted builtins; the learner/oracle/reference each get their own."""
    safe = {k: v for k, v in vars(builtins).items() if k not in BLOCKED_BUILTINS}
    safe["__import__"] = _guarded_import
    g = {"__builtins__": safe, "__name__": "solution"}
    _real_exec(_real_compile(PRELUDE, "<prelude>", "exec"), g)
    _real_exec(_real_compile(code, "<solution>", "exec"), g)
    return g


def _resolve(g, entry):
    if "Solution" in g and entry:
        return getattr(g["Solution"](), entry)
    if entry and callable(g.get(entry)):
        return g[entry]
    raise LookupError(f"entry point '{entry}' not found")


def _timed(limit, fn, *a):
    signal.setitimer(signal.ITIMER_REAL, limit)
    try:
        return fn(*a)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def _canon(v):
    return json.loads(json.dumps(v, default=repr))


def _eq(a, b, cmp):
    if cmp == "unordered" and isinstance(a, list) and isinstance(b, list):
        try:
            return sorted(a) == sorted(b)
        except TypeError:
            return a == b
    if cmp == "float_tol" and isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-5
    return a == b


def _judge(fl, fo, args, cmp, limit):
    """-> ("pass"|"fail"|"invalid", kind). Oracle failure => the generated input is invalid, not a learner bug."""
    try:
        exp = _canon(_timed(limit, lambda: fo(*copy.deepcopy(args))))
    except BaseException:  # noqa: BLE001
        return "invalid", None
    try:
        act = _canon(_timed(limit, lambda: fl(*copy.deepcopy(args))))
    except _Timeout:
        return "fail", "timeout"
    except BaseException:  # noqa: BLE001
        return "fail", "runtime_error"
    return ("pass", None) if _eq(act, exp, cmp) else ("fail", "wrong_output")


def _gen(gen, rng):
    args = _timed(1.0, gen, rng)
    if not isinstance(args, (list, tuple)):
        raise TypeError("gen_inputs must return the list of call arguments")
    return list(args)


def _vector(fl, fo, gen, cmp, seed, n):
    """Fixed-seed pass/fail bit-vector (1 = learner failed) used for mutation fingerprints. Contains no inputs."""
    rng, bits, timeouts = random.Random(seed), [], 0
    for _ in range(n):
        try:
            args = _gen(gen, rng)
        except BaseException:  # noqa: BLE001
            bits.append("0")
            continue
        st, kind = _judge(fl, fo, args, cmp, FUZZ_CALL_LIMIT_S)
        bits.append("1" if st == "fail" else "0")
        if kind == "timeout":
            timeouts += 1
            if timeouts >= MAX_TIMEOUTS:
                bits.extend("1" * (n - len(bits)))
                break
    return "".join(bits)


def _do_verify(req, emit):
    fl = _resolve(_load(req["code"]), req["entry"])
    fo = _resolve(_load(req["oracle_code"]), req["entry"])
    gen = _load(req["gen_code"])["gen_inputs"]
    ref = None
    if req.get("reference_code"):
        try:
            ref = _resolve(_load(req["reference_code"]), req["entry"])
        except BaseException:  # noqa: BLE001
            ref = None
    cmp, n = req.get("comparator", "exact"), int(req.get("n", 200))
    budget, t0 = float(req.get("budget_s", 15.0)), time.monotonic()

    rng = random.Random(req["seed"])
    fails, counts = [], {"run": 0, "invalid": 0, "gen_errors": 0, "fail": 0, "timeout": 0, "runtime_error": 0,
                         "wrong_output": 0}
    budget_hit = False
    for _ in range(n):
        if time.monotonic() - t0 > budget:
            budget_hit = True
            break
        try:
            args = _gen(gen, rng)
        except BaseException:  # noqa: BLE001
            counts["gen_errors"] += 1
            continue
        st, kind = _judge(fl, fo, args, cmp, FUZZ_CALL_LIMIT_S)
        if st == "invalid":
            counts["invalid"] += 1
            continue
        counts["run"] += 1
        if st == "fail":
            counts["fail"] += 1
            counts[kind] += 1
            if len(fails) < MAX_FAIL_KEEP:
                fails.append((args, kind))
            if counts["timeout"] >= MAX_TIMEOUTS:
                break

    failure_class = divergence = first_kind = None
    if fails:
        args0, first_kind = min(fails, key=lambda f: len(json.dumps(f[0], default=repr)))
        small = shrink(args0, lambda a: _judge(fl, fo, a, cmp, FUZZ_CALL_LIMIT_S)[0] == "fail")
        failure_class = classify_failure(small)
        if ref is not None:
            try:
                divergence = _timed(5.0, trace_compare, fl, ref, small)
            except BaseException:  # noqa: BLE001
                divergence = None
    vector = _vector(fl, fo, gen, cmp, req.get("fp_seed", 12345), int(req.get("fp_n", 64)))
    emit({"verify": {"run": counts["run"], "invalid": counts["invalid"], "gen_errors": counts["gen_errors"],
                     "failures": counts["fail"], "timeouts": counts["timeout"],
                     "runtime_errors": counts["runtime_error"], "wrong_outputs": counts["wrong_output"],
                     "first_kind": first_kind, "failure_class": failure_class, "divergence": divergence,
                     "vector": vector, "budget_hit": budget_hit}})


def _do_trace(req, emit):
    fl = _resolve(_load(req["code"]), req["entry"])
    fr = _resolve(_load(req["reference_code"]), req["entry"])
    emit({"trace": _timed(5.0, trace_compare, fl, fr, req["args"])})


def _do_run(req, emit):
    g = _load(req["code"])
    fn = _resolve(g, req.get("entry"))
    limit = float(req.get("timeout_s", 2.0))
    for i, t in enumerate(req["tests"]):
        try:
            value = _timed(limit, lambda: fn(*t["args"]))
            text = json.dumps(value, default=repr)
            if len(text) > MAX_VALUE_CHARS:
                emit({"i": i, "status": "error", "error": "OutputTooLarge: result exceeds limit"})
            else:
                emit({"i": i, "status": "ok", "value": json.loads(text)})
        except _Timeout:
            emit({"i": i, "status": "timeout"})
        except RecursionError:
            emit({"i": i, "status": "error", "error": "RecursionError: maximum recursion depth exceeded"})
        except MemoryError:
            emit({"i": i, "status": "error", "error": "MemoryError"})
        except BaseException as e:  # noqa: BLE001
            emit({"i": i, "status": "error", "error": f"{type(e).__name__}: {e}"[:300]})


def main() -> None:
    real_out = sys.stdout
    req = json.loads(sys.stdin.read())

    def emit(obj):
        real_out.write(json.dumps(obj) + "\n")
        real_out.flush()

    sys.stdout = sys.stderr = _Sink()
    signal.signal(signal.SIGALRM, _on_alarm)
    mode = req.get("mode", "run")
    try:
        if mode == "both":  # examples then differential fuzz, one container start
            _do_run(req, emit)
            _do_verify(req, emit)
        else:
            {"run": _do_run, "verify": _do_verify, "trace": _do_trace}[mode](req, emit)
    except BaseException as e:  # noqa: BLE001
        emit({"load_error": f"{type(e).__name__}: {e}"[:500]})


if __name__ == "__main__":
    main()
