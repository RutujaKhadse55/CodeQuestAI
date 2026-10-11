# Sandbox attack set (generated 2026-10-11 15:54)

Sandbox = Docker (`--network none --memory 256m --cpus 1 --pids-limit 64 --read-only --cap-drop ALL`), AST policy first, per-test timer second.

| # | Attack | Blocked by | Detail | Blocked |
|---|---|---|---|---|
| 1 | file_read | policy | banned_builtin | yes |
| 2 | os_system | policy | import_not_allowed | yes |
| 3 | network_socket | policy | import_not_allowed | yes |
| 4 | subprocess | policy | import_not_allowed | yes |
| 5 | eval_exec | policy | banned_builtin | yes |
| 6 | dunder_escape | policy | dunder_access | yes |
| 7 | infinite_loop | sandbox | timeout | yes |
| 8 | memory_bomb | sandbox | runtime_error | yes |

**Block rate: 8/8 (100%)**

Defence in depth is covered by `backend/app/engine/tests/test_attacks.py`: policy-bypass code is stopped by the harness import guard / removed builtins, a solution that swallows the timeout is killed by the runner backstop (no stray containers), and a print flood cannot forge result lines.
The same 8/8 was reproduced with `SANDBOX_MODE=native` inside the production image (non-root, read-only filesystem).
