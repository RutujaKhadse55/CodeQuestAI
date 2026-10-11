"""Sandbox harness. Runs INSIDE the container (Linux), never imported by the API process.

stdin : {"code": str, "entry": str|null, "tests": [{"args": [...]}], "timeout_s": float}
stdout: one JSON line per test, flushed as it finishes:
        {"i": n, "status": "ok"|"error"|"timeout", "value": any, "error": str}
        or a single {"load_error": "..."} line when the code cannot be loaded.
Learner stdout/stderr is captured and discarded, so it can never forge a result line.
Supports `class Solution` methods (LeetCode) and plain functions.
"""
import builtins
import json
import signal
import sys

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


class _Timeout(BaseException):  # BaseException so learner `except Exception` cannot swallow it
    pass


class _Sink:
    def __init__(self):
        self.n = 0

    def write(self, s):
        self.n += len(s)
        return len(s)

    def flush(self):
        pass


def _on_alarm(signum, frame):
    raise _Timeout()


def main() -> None:
    real_out = sys.stdout
    req = json.loads(sys.stdin.read())
    real_import = builtins.__import__
    real_exec, real_compile = builtins.exec, builtins.compile

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level or name.split(".")[0] not in ALLOWED:
            raise ImportError(f"import of '{name}' is not allowed")
        return real_import(name, globals, locals, fromlist, level)

    safe = {k: v for k, v in vars(builtins).items() if k not in BLOCKED_BUILTINS}
    safe["__import__"] = guarded_import
    g = {"__builtins__": safe, "__name__": "solution"}

    def emit(obj):
        real_out.write(json.dumps(obj) + "\n")
        real_out.flush()

    sys.stdout = sys.stderr = _Sink()
    try:
        real_exec(real_compile(PRELUDE, "<prelude>", "exec"), g)
        real_exec(real_compile(req["code"], "<solution>", "exec"), g)
    except BaseException as e:  # noqa: BLE001
        emit({"load_error": f"{type(e).__name__}: {e}"[:500]})
        return

    entry = req.get("entry")
    fn = None
    if "Solution" in g and entry:
        try:
            fn = getattr(g["Solution"](), entry)
        except BaseException as e:  # noqa: BLE001
            emit({"load_error": f"{type(e).__name__}: {e}"[:500]})
            return
    elif entry and callable(g.get(entry)):
        fn = g[entry]
    if fn is None:
        emit({"load_error": f"entry point '{entry}' not found"})
        return

    signal.signal(signal.SIGALRM, _on_alarm)
    limit = float(req.get("timeout_s", 2.0))
    for i, t in enumerate(req["tests"]):
        try:
            signal.setitimer(signal.ITIMER_REAL, limit)
            try:
                value = fn(*t["args"])
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
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


if __name__ == "__main__":
    main()
