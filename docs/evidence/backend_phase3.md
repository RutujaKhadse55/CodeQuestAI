# Backend Phase 3 — dashboard v2, recommend, delete-all, i18n errors, perf, ops

| Item | What exists | Verified by |
|---|---|---|
| `/dashboard/{id}` v2 | mastery per concept, mistakes, **heatmap** (problem x mistake class), recent diagnoses, verified breakdown, learner **profile** (paste rate, edge-case miss rate, attempts to pass; Backend-basic until AI's LearnerModel is registered), **credits** (null until Agents registers a meter) | `test_phase3.py` |
| `/recommend/{id}` | weakest concept first from `mastery/curated_problems.json` (8 demo problems + LeetCode links), skips solved, deterministic; no history -> first unsolved | `test_phase3.py` (3 cases) |
| `DELETE /users/{id}/data` | deletes every SQL row of the learner (11 tables), then runs registered hooks (`providers.register_deletion_hook`: Agents' Chroma memory / TTS cache, AI profiles); a failing hook is reported, never aborts; idempotent; other users untouched | `test_phase3.py` |
| Localised errors | every error body adds `message_key` (`errors.<CODE>`) and `localized` (EN/HI/MR via `X-Lang` or `Accept-Language`). **HI/MR wording is [NEEDS VERIFICATION] by a bilingual reviewer** | `test_phase3.py` |
| Limits | 60 req/min per token+client (429 `RATE_LIMITED`); per-user daily `/analyze` cap (default 300, `DAILY_ANALYZE_CAP`) | `test_shell.py`, `test_phase3.py` |
| Performance | examples + fuzz + shrink + trace in ONE container start; ReferenceBundle cached per content_hash | `docs/evidence/latency.md` |
| Evidence harness | `python scripts/run_evidence.py` writes sandbox_attacks.md, diagnosis_accuracy.md, latency.md, ai_agents_evals.md | run on this laptop |
| Prod image | `backend/Dockerfile`: non-root uid 10001, optional baked MiniLM (`--build-arg BAKE_MINILM=1`), `SANDBOX_MODE=native` inside the container, healthcheck; compose: read-only FS, tmpfs /tmp, cap_drop ALL, no-new-privileges, pids/memory limits | built + run; smoke OK; attacks 8/8 in-container |

## Measured
- `/analyze` (examples + fuzz 200 + shrink + trace): p50 0.59 s, p95 0.74 s, max 0.77 s over 30 samples, host Docker mode, warm (was ~1.1 s with two container starts).
- Attack set: 8/8 blocked, on the host (Docker mode) and inside the production image (native mode, non-root, read-only FS).
- Diagnosis baseline (Backend rule fallback only): detection 10/10, mistake-class accuracy 1/10 — **below the 50 % go/no-go bar**; needs AI's fingerprint matcher / AST rules. See `diagnosis_accuracy.md`.

## Known limits
- Native sandbox (production image) has rlimits and the import guard but **no network namespace**; docker mode has `--network none`. Residual risk until Phase 4 hardening review.
- One shared API token: any token holder can read or delete any `user_id`.
- `latency.md` was measured in Docker mode on the host, not in the production image.
- AI/Agents eval modules have no `run()` yet (shown as pending).
