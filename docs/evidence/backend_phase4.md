# Backend Phase 4 — security review, bug bash, hardening, evidence

## 1. Security review (plan §6 Phase 4 item 4)
| Checklist item | Status | Evidence |
|---|---|---|
| `python -I`, empty environment, temp cwd | yes (native + docker + sandbox service) | `runner.py`; in-container probe shows the child sees only `LC_CTYPE` |
| Output truncation | yes: 10 KB per result value, learner stdout/stderr discarded, 1 MB stdout cap, 8 MB request cap on the sandbox service, 2 MB on the API | `test_bugbash.py` (huge output, print flood) |
| Orphan process / container cleanup | yes: `docker kill` on timeout, `killpg` natively; 0 `cq-sbx-*` containers after the suite; 2 processes in the sandbox container after the attack set | `test_timeout_backstop_*`, `test_no_stray_sandbox_containers_left` |
| No hidden data in responses | yes: fuzz rows carry outcome + failure class only; `FuzzResult` has no input fields; seed stored, never returned | `test_analyze.py`, `test_bugbash.py::test_fuzz_result_carries_no_input_data` |
| API token compare | **fixed**: constant-time `hmac.compare_digest` (was `!=`) | `deps.py` |
| Oversized bodies | **added**: 413 before parsing (> 2 MB) | `test_shell.py` |
| Default secrets | **added** startup warnings for `API_TOKEN=change-me` and the default `SANDBOX_TOKEN` | `main.py` |
| SQL / filter injection | parameter-bound everywhere (SQLModel, Chroma `where`); usernames validated | profile-RAG tests |
| SSRF | only the fixed LeetCode GraphQL URL is fetched; username regex `^[A-Za-z0-9_-]{1,40}$` | `client.py` |

### Finding 1 (HIGH, fixed): interpreter escape through frame attributes
With the AST policy bypassed, a running generator gave access to the harness frame chain
(`gen.gi_frame.f_back.f_globals`), whose globals hold the real `builtins` module. None of these names are dunder, so
the old policy did not reject them. **Fix:** `BANNED_ATTRS` (`gi_frame`, `f_back`, `f_globals`, `f_builtins`,
`tb_frame`, `tb_next`, `mro`, ...) and format-string attribute/index traversal (`"{0.gi_frame}"`, `"{0[0]}"`) are now
rejected. 20 escape payloads, including a full-width-Unicode `eval`, are tested.
**In-process restriction is not a sandbox**, so the real boundary was moved out of process (finding 2).

### Finding 2 (MEDIUM, fixed): production sandbox had no network isolation and shared the backend's secrets
The Phase 3 production image ran user code inside the backend container: same environment (API token, Gemini key),
and outbound network access. **Fix:** a separate `sandbox` service (`backend/Dockerfile.sandbox`,
`engine/sandbox/server.py`), `SANDBOX_MODE=remote`:
- on an `internal: true` compose network: **no route to the internet**; only the backend can reach it;
- **no API keys** in its environment (only its own shared token); read-only filesystem, tmpfs `/tmp`, all capabilities dropped, non-root (uid 10002), pid/memory/cpu limits;
- each run is an rlimit'd child process, 3 concurrent runs.

Proof (compose stack running): from inside the sandbox container, with the policy **bypassed** and the frame-chain
escape used to reach the real `builtins`, `os` and `socket`: environment variables = `LC_CTYPE` only, `connect(8.8.8.8:53)` ->
`OSError`, file write -> `OSError` (read-only FS); direct probes: no egress to 8.8.8.8 / 1.1.1.1 / https://example.com.
A full escape therefore finds no secret and has no way out.

### Residual risks (accepted / open)
- An escaped learner process can still read the **oracle / reference / generator code** (they run in the same sandbox process) — hidden-test *secrecy* rests on the AST policy; the data it can reach contains no keys.
- The sandbox container is reachable from the backend and vice-versa on `sandbox_net`; the backend requires the API token on every route, which the sandbox does not have.
- Docker-mode (dev laptops) pulls `python:3.11-slim` unpinned at run time; pin a digest before the demo.
- One shared API token (any holder can read/delete any `user_id`).
- Hindi/Marathi error strings are unreviewed.

## 2. Bug bash (item 3) — 21 sandbox/fuzz cases in `test_bugbash.py`
Huge output, infinite and deep-but-legal recursion, non-JSON returns (set / NaN / inf / None / tuple), 10^5-digit ints,
5 MB print flood, Unicode in and out, 60 small + 4 large (10^5-element) inputs per call, per-test input copies, missing entry
point / failing `__init__` / failing class body, timeout budget with many slow tests, broken generator, always-raising
oracle, crashing learner, input-mutating learner. **Bugs found and fixed:**
1. A learner returning `NaN`/`inf` crashed the host comparator (`int(nan)`) -> API 500. Fixed in `service._canon`.
2. The sandbox service's 2 MB body cap rejected LeetCode-sized (10^5 element) inputs; raised to 8 MB.
3. A syntax error returned a 422 "no function found"; it is now a normal 200 result with `SyntaxError: ... (line N)` and flag `syntax_error`.

## 3. Hardcode and copy flags (item 1)
`/analyze` surfaces flags: `hardcode_suspected` (static detector in `engine/hardcode.py`: constant return that never reads
a parameter; `if` on a literal copied from an example input; dict keyed by example inputs mapping to example outputs),
`copy_suspected` (Phase 2). A hardcode hit sets the diagnosis to `hardcoded_output` (confidence 0.9). AI's detector replaces it via
`providers.register_hardcode`; a broken detector never fails an analysis. On the labelled Two Sum set only the hardcoded file is
flagged; legitimate solutions (hash map, contains-duplicate loop) are not.

## 4. Evidence (item 2) — `python scripts/run_evidence.py`
| Metric | Result |
|---|---|
| Attack block rate | **8/8**, in Docker mode, native-in-container mode and the remote sandbox service |
| `/analyze` latency (Docker mode, laptop) | p50 0.67 s, p95 0.85 s, max 0.88 s, 30 samples (target p95 < 6 s) |
| `/analyze` latency (production path: backend -> sandbox service) | p50 0.18 s, p95 0.19 s, 15 samples |
| Detection rate on 10 labelled buggy Two Sum files | **10/10** |
| Mistake-class accuracy (Backend rules + hardcode detector only) | **2/10 (20 %)** — below the 50 % go/no-go bar; needs AI's fingerprint matcher / AST rules |
| Tests | **183 passed** (full backend suite, incl. Docker-backed tests) |

## 5. What is not done
- Labelled sets for the other three developers (Contains Duplicate, Valid Anagram, Best Time to Buy, Maximum Subarray, Binary Search, Climbing Stairs, Missing Number) and the labelled-set accuracy target depend on their files and on AI's matcher.
- `agent_safety_report.md`, `hint_leak_report.md`, `multilingual_eval.md` are AI/Agents deliverables (their eval modules show as pending).
- The extension still only calls `/health`; the real end-to-end flow from the browser is untested.
