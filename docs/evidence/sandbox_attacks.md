# Sandbox attack set (Backend, Phase 1)

Run: `GET /admin/attacks` or `pytest backend/app/engine/tests/test_attacks.py`. Sandbox = Docker
(`--network none --memory 256m --cpus 1 --pids-limit 64 --read-only --cap-drop ALL --user 65534`), per-test 2 s timer.

| # | Attack | Blocked by | Result |
|---|---|---|---|
| 1 | file read (`open`) | AST policy: banned_builtin | blocked |
| 2 | `import os; os.system` | AST policy: import_not_allowed | blocked |
| 3 | `import socket` network | AST policy: import_not_allowed | blocked |
| 4 | `import subprocess` | AST policy: import_not_allowed | blocked |
| 5 | `eval` / `__import__` | AST policy: banned_builtin | blocked |
| 6 | dunder escape (`().__class__.__bases__`) | AST policy: dunder_access | blocked |
| 7 | `while True: pass` | sandbox per-test timer | blocked (timeout) |
| 8 | `[0] * 10**10` memory bomb | container memory limit | blocked (killed, reported as runtime_error) |

Block rate: 8/8. Latency (`/analyze`, 3 examples, warm Docker): ~0.7 s per call (3 samples; full table in Phase 4).
Defence in depth (tested): policy-bypass code (`import os`, `open`, `eval`, `getattr`) is stopped inside the harness; a solution that swallows the timeout exception is killed by the runner backstop with no stray containers; a print flood cannot forge result lines.
