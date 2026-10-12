# CodeQuest AI

**AI coding mentor & debugging missions for LeetCode learners** — built for VORTEXA 3.0 (PS E-02).

> Plan: [docs/CodeQuest_AI_Hackathon_Implementation_Plan_v3.md](docs/CodeQuest_AI_Hackathon_Implementation_Plan_v3.md)
> Contract: [openapi.yaml](openapi.yaml) - DB models: [backend/app/db/models_core.py](backend/app/db/models_core.py) - Contracts: [backend/app/contracts/](backend/app/contracts/)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Quick Start](#quick-start)
4. [Environment and Feature Flags](#environment-and-feature-flags)
5. [API Endpoints](#api-endpoints)
6. [Execution Flow](#execution-flow)
7. [AI Agent Crew](#ai-agent-crew-feature_crew1)
8. [LLM Integration](#llm-integration)
9. [Sandbox and Security](#sandbox-and-security)
10. [Problem Chat](#problem-chat-feature_chat1)
11. [LeetCode Profile RAG](#leetcode-profile-rag-feature_profile_rag1)
12. [Mastery and ELO System](#mastery-and-elo-system)
13. [Chrome Extension](#chrome-extension)
14. [Internationalisation](#internationalisation-i18n)
15. [Docker Deployment](#docker-deployment)
16. [Testing and Smoke Tests](#testing-and-smoke-tests)
17. [Makefile Targets](#makefile-targets)

---

## Architecture Overview

```
Chrome Extension (MV3 - TypeScript + React)
  content/toolbar -> service_worker -> result_card
         | HTTPS / chrome.runtime.sendMessage
         v
FastAPI Backend (Python 3.12)
  Routers           Crew Agents       Chat Agent
  /analyze          explain           Guard
  /hint             tests             LLM
  /crew/*           debug             RAG
  /chat/*           trace
  /profile/*        hint-mentor
         |
  Sandbox Engine (Docker container / native)
  run | verify (fuzz+shrink+trace) | steps
         |
  SQLite (SQLModel)   ChromaDB (RAG)
         |
  Gemini API (google-genai)
```

**Authentication:**
- Backend: X-API-Token: <API_TOKEN> header (also Authorization: Bearer <token>)
- Per-learner: X-User-Token issued by POST /users (required when REQUIRE_USER_TOKEN=1)

---

## Repository Structure

```
CodeQuestAI/
+-- backend/
|   +-- Dockerfile                  # Production backend image
|   +-- Dockerfile.sandbox          # Isolated sandbox service image
|   +-- app/
|       +-- main.py                 # FastAPI app, lifespan, middleware, router autoload
|       +-- config.py               # All env vars and feature flags
|       +-- auth.py                 # Token auth + per-learner user resolution
|       +-- deps.py                 # FastAPI deps: session, rate limiter, require_token
|       +-- errors.py               # ApiError + global error handler
|       +-- i18n_errors.py          # Localised error messages (EN/HI/MR)
|       +-- lcfetch.py              # LeetCode GraphQL problem fetcher
|       +-- providers.py            # Service locator (engine, guard, diagnoser, LLM, etc.)
|       +-- wiring.py               # register_all(): wires real implementations at startup
|       +-- routers/                # Auto-loaded FastAPI routers
|       |   +-- analyze.py          # POST /analyze (core verification + diagnosis pipeline)
|       |   +-- hint.py             # POST /hint + GET /hint-state/{user_id}/{problem_slug}
|       |   +-- crew.py             # POST /crew/{explain,tests,debug,trace}
|       |   +-- problem_chat.py     # GET|POST|DELETE /chat/* endpoints
|       |   +-- problems.py         # POST /problems/capture
|       |   +-- users.py            # POST /users, DELETE /users/{id}/data
|       |   +-- dashboard.py        # GET /dashboard/{user_id}
|       |   +-- attempts.py         # GET /attempts/{user_id}
|       |   +-- recommend.py        # GET /recommend/{user_id}
|       |   +-- profile_rag.py      # POST /profile/sync, POST /profile/ask, etc.
|       |   +-- explain.py          # POST /explain (URL-based explainer)
|       |   +-- explainback.py      # POST /explainback (copy-flag flow)
|       |   +-- voice.py            # POST /tts
|       |   +-- nudge.py            # POST /nudge
|       |   +-- i18n.py             # GET /i18n
|       |   +-- health.py           # GET /health
|       |   +-- admin_attacks.py    # GET /admin/attacks (sandbox attack evidence)
|       |   +-- zz_fallbacks.py     # Catch-all fallbacks (mounted last)
|       +-- crew/                   # AI agent crew
|       |   +-- service.py          # explain / generate_tests / debug / trace / hint
|       |   +-- llm.py              # complete_json(): structured Gemini / provider LLM calls
|       |   +-- runtime.py          # Crew-specific sandbox helpers
|       |   +-- models.py           # Pydantic output models for each agent
|       |   +-- config/
|       |       +-- agents.yaml     # Agent roles, goals, backstories
|       |       +-- tasks.yaml      # Task descriptions and expected output schemas
|       +-- chat/                   # Problem-understanding chat agent
|       |   +-- agent.py            # respond(): intent -> tools -> LLM -> guard
|       |   +-- service.py          # Consent, threads, messages (DB layer)
|       |   +-- guard.py            # Solution-leak guard for chat replies
|       |   +-- lang.py             # Language detection, intent classification
|       |   +-- rules.py            # why_failing() fallback, policy rules
|       |   +-- tools.py            # Tool registry: run_analysis, get_history, etc.
|       +-- engine/                 # Code execution and analysis
|       |   +-- service.py          # SandboxEngine: sandbox_run, run_and_fuzz, fuzz, trace, step_trace
|       |   +-- harness.py          # Harness executed INSIDE the sandbox container
|       |   +-- ast_policy.py       # AST allow-list (banned builtins, imports)
|       |   +-- hardcode.py         # Hardcode detector (regex + AST patterns)
|       |   +-- copy_detector.py    # Paste ratio + timing -> copy flag
|       |   +-- hint_state.py       # HintStateService: unlock tiers by attempts/time
|       |   +-- shrinker.py         # Delta-shrink failing fuzz inputs
|       |   +-- signature.py        # Parse function/class entry point + param names
|       |   +-- examples_parser.py  # Parse LeetCode example I/O strings
|       |   +-- sandbox/runner.py   # HTTP runner: calls the sandbox service
|       |   +-- tracer/             # Step-by-step variable tracer (sys.settrace)
|       +-- ai/                     # Standalone AI helpers
|       |   +-- hints/              # generate_hint(), hint_violation guard, tier templates
|       |   +-- llm/                # Shared LLM client
|       |   +-- diagnose/           # Diagnosis models
|       |   +-- explain/            # URL-based problem explainer
|       |   +-- evals/              # Eval harnesses
|       +-- profile_rag/            # LeetCode public-profile RAG
|       |   +-- client.py           # GraphQL profile fetcher (all public endpoints)
|       |   +-- documents.py        # Document chunking for ChromaDB
|       |   +-- store.py            # ChromaDB upsert/query
|       |   +-- answerer.py         # Retrieval -> Gemini -> answer
|       |   +-- service.py          # sync / delete / snapshot_summary
|       |   +-- api.py              # /profile/* router helpers
|       +-- mastery/
|       |   +-- service.py          # MasteryService: ELO updates per concept + mistake counts
|       |   +-- elo.py              # ELO formula (base 1000, K=32)
|       |   +-- recommender.py      # Weakest-concept problem recommender
|       |   +-- curated_problems.json
|       +-- agents/
|       |   +-- mentor/             # MentorAgent
|       |   +-- nudge/              # NudgeAgent
|       |   +-- voice/              # VoiceAgent (TTS)
|       +-- db/
|       |   +-- __init__.py         # SQLite engine init (create_all; no migrations)
|       |   +-- models_core.py      # SQLModel tables: User, Attempt, TestResultRow,
|       |                           #   DiagnosisRow, ConceptMastery, UserMistakeCount,
|       |                           #   HabitEvent, LCProblemRow, ChatThread, ChatMessage,
|       |                           #   ProfileConsent, LeetCodeProfileSnapshot, LearnerContext
|       +-- contracts/
|       |   +-- models.py           # Pydantic request/response models
|       |   +-- enums.py            # ErrorCode enum
|       +-- mock/                   # MOCK=1 canned responses
|       +-- static/                 # dev_chat.html (FEATURE_DEV_UI=1 -> /dev/)
+-- extension/                      # Chrome Extension (MV3)
|   +-- manifest.json               # Permissions, content scripts, service worker
|   +-- vite.config.ts
|   +-- tsconfig.json
|   +-- src/
|       +-- background/
|       |   +-- service_worker.ts   # All network calls; Monaco bridge; SSE relay; TTS offscreen
|       +-- content/
|       |   +-- toolbar.ts          # Shadow-DOM floating toolbar (selection-aware)
|       |   +-- orchestrate.ts      # Capture -> /problems/capture -> /analyze pipeline
|       |   +-- result_card.ts      # Shadow-DOM side panel (tabs: Verdict/Trace/Hints/Chat/Voice)
|       |   +-- guards.ts           # Extension context validity guards
|       |   +-- markdown.ts         # Markdown renderer for panel content
|       |   +-- selectors.config.ts # LeetCode DOM selectors
|       |   +-- capture/
|       |       +-- dom.ts          # Problem text from DOM (Source A)
|       |       +-- graphql.ts      # Problem metadata via LeetCode GraphQL (Source B)
|       |       +-- runpanel.ts     # Run result capture from LeetCode UI (Source C)
|       +-- popup/
|       |   +-- popup.tsx           # Browser-action: health indicator + dashboard summary
|       +-- options/
|       |   +-- index.html          # Backend URL, API token, language settings
|       +-- api/
|       |   +-- client.ts           # Typed fetch wrappers for all backend endpoints
|       |   +-- types.ts            # TypeScript types mirroring openapi.yaml schemas
|       +-- i18n/                   # Extension i18n (EN/HI/MR)
|       +-- offscreen/              # Offscreen document for TTS audio (MV3 restriction)
|       +-- replay/                 # Session replay (stub)
+-- shared/
|   +-- locales/
|       +-- en/ui.json
|       +-- hi/ui.json
|       +-- mr/ui.json              # Marathi UI translations
+-- data/                           # Runtime data (git-ignored)
+-- fixtures/lc/                    # Sample problem payloads (for /dev/ UI)
+-- scripts/
|   +-- smoke.sh                    # End-to-end smoke test
|   +-- sandbox_check.py            # Sandbox attack evidence
|   +-- build_extension_zip.sh      # Package extension for Chrome Web Store
+-- docs/                           # Evidence, compliance notes, implementation plan
+-- requirements/                   # Split requirement files: base, ai, agents, profile_rag
+-- requirements.txt                # Umbrella requirements
+-- openapi.yaml                    # Full API contract
+-- docker-compose.yml              # Backend + sandbox services
+-- Makefile                        # Common dev targets
```

---

## Quick Start

### Backend (local / mock)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env  (or: make env)
cat env/*.env.part > .env && cp .env .env.example   # then set API_TOKEN

# 3a. Mock server - canned responses, no LLM, no sandbox needed
make mock   # MOCK=1 uvicorn app.main:app --reload --port 8000

# 3b. Real server
make run    # uvicorn app.main:app --reload --port 8000
```

All requests require `X-API-Token: <API_TOKEN>`. Tests: `make test`. Smoke: `make smoke`.

### Extension (Chrome)

```bash
cd extension
npm install
npm run build   # outputs to extension/dist/
```

Load `extension/dist/` as an unpacked extension (`chrome://extensions` -> Developer mode -> Load unpacked).
Set the Backend URL and API token in the extension **Options** page.

### Docker (backend + sandbox)

```bash
API_TOKEN=<secret> SANDBOX_TOKEN=<secret> docker compose up --build
```

---

## Environment and Feature Flags

| Variable | Default | Description |
|---|---|---|
| `API_TOKEN` | `change-me` | Shared token for all API requests |
| `MOCK` | `0` | `1` = serve canned example responses |
| `DATABASE_URL` | `sqlite:///./data/codequest.db` | SQLAlchemy DB URL |
| `SANDBOX_MODE` | `auto` | `docker` / `native` / `remote` / `auto` |
| `SANDBOX_URL` | `http://sandbox:9000` | Remote sandbox address |
| `SANDBOX_TOKEN` | `sandbox-dev-token` | Shared secret with sandbox |
| `DAILY_ANALYZE_CAP` | `300` | Max `/analyze` calls per user per UTC day |
| `RATE_LIMIT_PER_MIN` | `60` | Per-IP rate limit |
| `CORS_ORIGINS` | _(empty)_ | Comma-separated allowed origins |
| `CORS_ORIGIN_REGEX` | `^chrome-extension://[a-p]{32}$` | Extension origin pattern |
| `GEMINI_API_KEY` | _(empty)_ | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model ID used for all LLM calls |
| `CHROMA_PATH` | `./data/chroma` | ChromaDB persistence directory |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model for profile RAG |
| `PROFILE_SYNC_MIN_INTERVAL_S` | `600` | Min seconds between profile re-syncs |
| `PROFILE_SNAPSHOT_DIR` | `./data/profiles` | JSON profile snapshot directory |
| `REQUIRE_USER_TOKEN` | `0` | Enforce per-learner `X-User-Token` on chat/profile routes |
| **Feature flags** | | |
| `FEATURE_CHAT` | `0` | Problem-understanding chat (`/chat/*`) |
| `FEATURE_PROFILE_RAG` | `0` | LeetCode profile RAG (`/profile/*`) |
| `FEATURE_CREW` | `0` | AI agent crew (`/crew/*`, LLM hints) |
| `CREW_ALLOW_FIX_CODE` | `0` | Debugger may return corrected full code |
| `FEATURE_DEV_UI` | `0` | Serve `backend/app/static/` at `/dev/` |
| `FEATURE_MEMORY` | `0` | Long-term learner memory (stub) |
| `FEATURE_VOICE_AGENT` | `0` | Real TTS via voice agent |

---

## API Endpoints

All endpoints require `X-API-Token`. Errors use `ErrorBody`: `{code, message?, message_key, localized}`.

### Core

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check - `{status, version}` |
| `POST` | `/users` | Create anonymous learner - returns `{user_id, user_token}` (shown once) |
| `DELETE` | `/users/{user_id}/data` | GDPR delete all SQL rows + registered hooks (Chroma, caches). Idempotent. |

### Problem Capture

| Method | Path | Description |
|---|---|---|
| `POST` | `/problems/capture` | Store a LeetCode problem (idempotent by `content_hash`). `supported=false` means explanation-only mode. |

Body (`LCProblem`): `{slug, title, difficulty, tags, statement_text, examples, constraints_text, starter_python?, lang_selected, content_hash, run_capture?}`

### Analysis Pipeline

| Method | Path | Description |
|---|---|---|
| `POST` | `/analyze` | Run the full verification + diagnosis pipeline |
| `GET` | `/attempts/{user_id}` | Recent attempts (no code, no fuzz seed exposed) |

Request: `{problem_slug, code, language?, run_capture?, paste_chars?, elapsed_ms?, user_id?}`
Aliases: `slug -> problem_slug`, `lang -> language`.

Response: `{attempt_id, verified, results[], diagnosis?, flags[], allowed_hint_level?}`

| Field | Values |
|---|---|
| `verified` | `oracle-verified` (fuzz ran vs oracle) or `unverified` (examples only) |
| `flags` | `copy_suspected`, `hardcode_suspected`, `syntax_error`, `no_reference_bundle`, `fuzz_budget_hit`, `no_runnable_tests`, `bundle_rejected` |

### Hints

| Method | Path | Description |
|---|---|---|
| `POST` | `/hint` | Next allowed hint (level 1-4, Guard-checked, template fallback). Returns `{level, text, locked, requirements, guard}`. |
| `GET` | `/hint-state/{user_id}/{problem_slug}` | Which tier is unlocked based on attempts/elapsed time (copy-flagged excluded) |

Hint tiers:

| Level | Content |
|---|---|
| 1 | Gentle observation - no technique named, no code |
| 2 | Data structure / technique to consider |
| 3 | Algorithm in plain words, step by step (no code) |
| 4 | Plain-language pseudocode + time and space complexity |

### Dashboard and Recommendations

| Method | Path | Description |
|---|---|---|
| `GET` | `/dashboard/{user_id}` | Mastery ELO per concept, mistake heatmap, habit profile, recent diagnoses, credits |
| `GET` | `/recommend/{user_id}` | Next curated problem by weakest concept rating (deterministic; skips solved) |

### AI Crew (FEATURE_CREW=1)

| Method | Path | Agent | Notes |
|---|---|---|---|
| `POST` | `/crew/explain` | Problem Explainer | Structured explanation: statement / constraints / examples walkthrough / code relation |
| `POST` | `/crew/tests` | Test Case Generator | LLM-written cases **run in the sandbox**; oracle output overrides model expected value |
| `POST` | `/crew/debug` | Debugger | Diagnosis, root cause, fix steps in words; `corrected_code` withheld unless `CREW_ALLOW_FIX_CODE=1` |
| `POST` | `/crew/trace` | Trace Analyst | Real line-by-line sandbox trace (Python); labelled static simulation (other languages) |
| `POST` | `/hint` | Hint Mentor | Registered via `providers.register_hint_service`; 4 tiers, Guard-checked |

Body: `{problem_slug?, code?, language?, selected_code?, response_language: en/hi/mr/hinglish, attempt_id?, input?, expected?}`
Response: `{agent, result, llm_used, executed, notes[]}`

### Problem Chat (FEATURE_CHAT=1)

| Method | Path | Description |
|---|---|---|
| `GET` | `/chat/consent-info` | Consent dialog text (scope, data accessed, retention policy) |
| `GET` | `/chat/consent` | Current consent status + profile summary |
| `POST` | `/chat/consent` | Grant consent, fetch and index PUBLIC LeetCode profile |
| `DELETE` | `/chat/consent` | Revoke: deletes snapshot row + JSON file + Chroma index |
| `POST` | `/chat/threads` | Start a chat thread for a captured problem |
| `GET` | `/chat/threads` | List the learner's own threads |
| `GET` | `/chat/threads/{thread_id}` | Thread with full message history (owner only; foreign/missing -> 403) |
| `DELETE` | `/chat/threads/{thread_id}` | Delete thread and all its messages |
| `POST` | `/chat/threads/{thread_id}/messages` | Send message -> JSON or SSE stream (`?stream=true` / `Accept: text/event-stream`) |

SSE events: `meta`, `token` (repeated), `done`.
Solution requests are refused **without calling any model**.

### Profile RAG (FEATURE_PROFILE_RAG=1)

| Method | Path | Description |
|---|---|---|
| `POST` | `/profile/sync` | Fetch learner's PUBLIC LeetCode profile, index in ChromaDB, keep snapshot. Rate-limited to `PROFILE_SYNC_MIN_INTERVAL_S`. Use `force=true` to bypass. |
| `POST` | `/profile/ask` | RAG query. Returns `{answer, mode, sources[], username}`. mode = `llm`/`evidence_only`/`llm_failed`/`no_data` |
| `GET` | `/profile/{user_id}` | Sync status + structured summary |
| `DELETE` | `/profile/{user_id}` | Delete snapshot + Chroma documents |

### Explain and Other

| Method | Path | Description |
|---|---|---|
| `POST` | `/explain` | Explain a problem by slug/URL (fetches via LeetCode GraphQL) |
| `POST` | `/explainback` | Explain-back flow: resolves copy flag, releases deferred mastery ELO update |
| `POST` | `/tts` | Text-to-speech (mock returns `{fallback: "browser_tts"}`) |
| `POST` | `/nudge` | Nudge agent (stub) |
| `GET` | `/i18n` | Locale string bundle for the requested language |
| `GET` | `/admin/attacks` | Run sandbox attack set - every entry must have `blocked: true` |

---

## Execution Flow

### `/analyze` pipeline

```
POST /analyze
  |
  +-- 1. Daily cap check (DAILY_ANALYZE_CAP per user per UTC day) -> 429 if exceeded
  +-- 2. Problem lookup (LCProblemRow) -> 422 UNSUPPORTED_PROBLEM if not captured
  +-- 3. Language check -> only python3 executed (other langs -> 422 UNSUPPORTED_LANGUAGE)
  +-- 4. AST policy check (banned builtins / imports) -> 400 CODE_REJECTED if violations
  +-- 5. Signature parse (entry point + param names from learner code or problem starter)
  +-- 6. Build test cases
  |     +-- Problem examples (up to 10)
  |     +-- run_capture (learner's own Run result with LeetCode's judged output) if provided
  |
  +-- 7. Sandbox execution
  |     +-- [has verified oracle bundle] run_and_fuzz() - ONE container start:
  |     |     +-- mode=both: examples + differential fuzz simultaneously
  |     |     +-- Fuzz: oracle_code vs learner_code, fresh random seed, up to N=200 inputs
  |     |     +-- Shrinker: delta-minimise failing input -> failure_class label
  |     |     +-- Trace: variable divergence on first failing input
  |     +-- [no verified bundle] sandbox_run(): examples only
  |
  +-- 8. Hardcode detector (regex + AST patterns on code vs example outputs)
  +-- 9. Copy detector (paste_chars / code_len ratio + elapsed_ms heuristics)
  |
  +-- 10. Persist to SQLite
  |       +-- Attempt row (code, fuzz_seed, flags, copy_flagged, mastery_pending)
  |       +-- TestResultRow[] (one per result; fuzz kind has no input/expected/actual)
  |       +-- DiagnosisRow (mistake_class, confidence, fuzz_vector, divergence_json)
  |       +-- HabitEvent[] (paste, run)
  |
  +-- 11. Mastery update (ELO per LeetCode concept tag; deferred if copy_flagged)
  +-- 12. HintState check -> allowed_hint_level
  |
  +-- Response: AnalyzeResponse
        {attempt_id, verified, results[], diagnosis?, flags[], allowed_hint_level?}
```

### Extension orchestration flow (Debug button)

```
User clicks the "Debug" button in the toolbar
  |
  +-- 1. capture/dom.ts       -> problem text, examples, constraints from LeetCode DOM
  +-- 2. capture/graphql.ts   -> slug, title, difficulty, tags via LeetCode GraphQL API
  +-- 3. capture/runpanel.ts  -> run result panel (verdict, input, output, expected)
  +-- 4. SW: GET_FULL_CODE    -> Monaco editor code + language (page-world script injection)
  |
  +-- POST /problems/capture  -> register problem with backend, get {problem_id, supported}
  +-- POST /analyze           -> full pipeline (code + run_capture + paste_chars + elapsed_ms)
  |
  +-- result_card.ts          -> 462px Shadow-DOM side panel slides in from the right
        +-- Tab: Verdict  (test results, fuzz outcome, diagnosis, flags)
        +-- Tab: Trace    (line-by-line variable trace from sandbox)
        +-- Tab: Hints    (4-tier progressive hints, unlock-gated)
        +-- Tab: Chat     (problem-understanding chat, SSE streaming)
        +-- Tab: Voice    (TTS playback via offscreen document)
```

---

## AI Agent Crew (FEATURE_CREW=1)

Ported from the `CodeQuest_Agent` CrewAI prototype into `backend/app/crew/`.

### Agents (from `crew/config/agents.yaml`)

| Agent key | Role |
|---|---|
| `problem_explainer` | Coding Problem Explanation Specialist |
| `test_case_generator` | Generated Test Case Analyst |
| `debugger` | Code Debugging Expert |
| `trace_analyst` | Execution Flow Tracer |
| `hint_mentor` | Progressive Coding Hint Mentor |

### Key design decisions vs the CrewAI prototype

- **Tools run by backend code, not the model.** Learner code only ever runs in the sandbox; real results are passed as `<data name="execution_evidence">` - the model cannot invent a run.
- **Guard on every model-written field.** A recursive `scrub()` function replaces any string that works as a full solution with `[withheld: this contained solution code]`.
- **Debugger corrected code withheld** unless `CREW_ALLOW_FIX_CODE=1`.
- **Hint level 5 ("near-complete guidance") is intentionally not offered** - the product caps at 4 tiers.
- **Graceful degradation.** Without an LLM every agent falls back to deterministic content (sandbox results, parsed examples, template hints).
- **Prompt injection hardening.** Problem text, learner code and execution output are wrapped in `<data name="...">` tags; instructions inside them are explicitly ignored.

---

## LLM Integration

### `crew/llm.py` - `complete_json(system, prompt, Model)`

1. Appends the Pydantic model's JSON schema to the prompt.
2. Calls `providers.llm()` hook if registered, else calls **Gemini** directly (`google-genai`, `temperature=0.2`, `response_mime_type=application/json`).
3. Strips markdown fences, extracts `{...}` JSON, validates against `Model`.
4. One repair retry with "Your previous reply was not valid JSON for the schema".
5. Returns `None` on failure - all callers produce deterministic fallback content.
6. Handles `429 PerDay` (daily quota): fast-fails for 10 min to avoid burning retries.
7. Transient errors (`429`, `5xx`, `TimeoutError`): exponential backoff, up to 2 retries.

### Chat agent LLM path (`chat/agent.py`)

1. **Intent classification** (deterministic regex/keyword rules) - the model is never called for routing.
2. Solution requests are refused without calling any model.
3. Allowlisted tool calls run with the authenticated user id.
4. LLM is called via `profile_rag/answerer.py` for profile questions or directly for general chat.
5. **Guard** on every reply - up to 2 stricter regenerations (adds STRICT system text: "no code blocks, no function definitions"), then a safe template.

### Profile RAG (`profile_rag/answerer.py`)

1. ChromaDB similarity search over the learner's indexed profile documents.
2. Retrieved evidence chunks + question -> Gemini prompt.
3. `mode` = `llm` / `evidence_only` / `llm_failed` / `no_data`.

---

## Sandbox and Security

The sandbox harness (`engine/harness.py`) runs **inside** the sandbox container and supports five modes:

| Mode | Payload keys | Output |
|---|---|---|
| `run` | `code, entry, tests[], timeout_s` | One JSON line per test + `load_error` |
| `verify` | `code, oracle_code, reference_code, gen_code, comparator, seed, n, budget_s, ...` | `{verify: {run, failures, first_kind, failure_class, vector, divergence, budget_hit}}` |
| `both` | run + verify merged | Both outputs; ONE container start per /analyze (saves ~0.5s) |
| `trace` | `code, reference_code, entry, args` | `{trace: divergence or null}` |
| `steps` | `code, entry, args, max_steps` | `{steps: {steps[], result, error, truncated}}` |

**Security controls:**

- **Allowed imports:** `math, collections, heapq, itertools, functools, bisect, typing`
- **Blocked builtins:** `open, exec, eval, compile, input, breakpoint, exit, quit, help, globals, locals, vars, getattr, setattr, delattr, memoryview`
- Learner stdout/stderr captured and discarded - cannot forge result lines
- `SIGALRM`-based per-call timeout raised as `BaseException` (learner `except Exception` cannot swallow it)
- **Raw fuzz inputs never leave the container** - only counts, a 0/1 pass-fail vector, a `failure_class` label, and a divergence object are returned
- Docker: `internal: true` network (no internet egress), read-only FS, `cap_drop: ALL`, `no-new-privileges`, PID/memory limits

Run `GET /admin/attacks` to verify all attack patterns are blocked.

---

## Problem Chat (FEATURE_CHAT=1)

**Setup flow:**
1. `GET /chat/consent-info` -> show the permission dialog in the extension panel
2. User enters LeetCode username -> `POST /chat/consent {leetcode_username}` -> backend fetches PUBLIC profile, indexes in ChromaDB, records consent
3. `POST /chat/threads {problem_slug}` -> create thread (`personalized: true` when profile is synced)
4. `POST /chat/threads/{id}/messages {content}` -> send message (JSON or SSE stream)

**Per-message handling:**
1. Language detection (EN/HI/MR) + intent classification (deterministic, no model call)
2. Policy check: solution request detected -> refuse without calling any model + offer next hint
3. Tool dispatch: `run_analysis`, `get_history`, `profile_lookup`, etc.
4. LLM call: problem + code + profile evidence + history all wrapped as untrusted `<data>`
5. Guard -> up to `MAX_GUARD_RETRIES=2` stricter regenerations -> safe template fallback

**Try it without the extension:**
Set `FEATURE_CHAT=1 FEATURE_PROFILE_RAG=1 FEATURE_DEV_UI=1` in `.env`, then open http://localhost:8000/dev/

---

## LeetCode Profile RAG (FEATURE_PROFILE_RAG=1)

**Extra requirements:** `pip install -r requirements/profile_rag.txt` (adds `sentence-transformers`, `chromadb`)

**Data fetched from LeetCode's public APIs (no login required):**
- Profile overview: name, location, reputation, ranking, contribution points
- Solved statistics: All / Easy / Medium / Hard
- Language breakdown
- Topic/skill tags
- Activity and streak
- Recent accepted submissions (last 20)
- Badges
- Contest rating and history

**ChromaDB document types indexed:** `profile_overview`, `solved_stats`, `languages`, `topics`, `streak`, `recent_submissions`, `badges`, `contest_rating`, `topic_stats`

**Rate limit:** minimum 600 s between re-syncs per username. Override with `force=true`.

---

## Mastery and ELO System

`mastery/service.py` implements `MasteryService`:

- **Per-concept ELO rating** (base 1000, K=32) mapped to LeetCode topic tags from captured problems
- **Opponent ratings:** Easy=900, Medium=1000, Hard=1100
- **Mistake counts** tracked per `mistake_class` (e.g. `missing_edge_single`, `hardcoded_output`, `off_by_one`)
- **Copy-flagged attempts** have `mastery_pending=True` - ELO update deferred until the learner completes the explain-back flow (`POST /explainback`)
- `GET /recommend/{user_id}` returns the curated problem whose concept has the lowest ELO rating (skips already-solved problems)
- `GET /dashboard/{user_id}` exposes the full mastery map, mistake heatmap, and habit profile

---

## Chrome Extension

| Component | Key file | Purpose |
|---|---|---|
| Service Worker | `background/service_worker.ts` | Routes all network calls; injects page-world scripts for Monaco access; relays SSE via `chrome.runtime.Port`; manages TTS offscreen document |
| Toolbar | `content/toolbar.ts` | Shadow-DOM floating pill (dark bg, amber border glow); appears on text/code selection; buttons: Debug, Explain, Hint, Chat |
| Orchestrator | `content/orchestrate.ts` | Capture (DOM + GraphQL + run panel) -> POST /problems/capture -> POST /analyze |
| Result Card | `content/result_card.ts` | 462px shadow-DOM side panel; slides in from right; minimises to circular FAB; tabs: Verdict / Trace / Hints / Chat / Voice |
| Popup | `popup/popup.tsx` | Browser-action popup: backend health indicator + dashboard summary (attempts, solved, top mistake) |
| Options | `options/index.html` | Backend URL, API token, mentor language, save/reset |
| DOM Capture | `content/capture/dom.ts` | Multi-selector LeetCode problem text extraction (Source A) |
| GraphQL Capture | `content/capture/graphql.ts` | LeetCode GraphQL: slug, title, difficulty, tags (Source B) |
| Run Panel | `content/capture/runpanel.ts` | Intercept LeetCode run/submit verdicts (Source C) |
| i18n | `i18n/setup.ts` | Load locale strings for toolbar/panel/options (EN/HI/MR) |
| Offscreen | `offscreen/offscreen.ts` | Audio context for TTS playback (MV3 Web Audio restriction) |

**Permissions:** `storage`, `contextMenus`, `offscreen`, `scripting`, `tabs`
**Host permissions:** `https://leetcode.com/*`, `http://localhost:8000/*`, `https://localhost:8000/*`

---

## Internationalisation (i18n)

| Layer | Mechanism |
|---|---|
| Backend API responses | `X-Lang` / `Accept-Language` header; `response_language: en/hi/mr/hinglish` in crew and chat request bodies |
| Backend error messages | `i18n_errors.py` provides the `localized` field in every `ErrorBody` |
| Extension UI | `shared/locales/{en,hi,mr}/ui.json`; loaded at runtime by `i18n/setup.ts` |
| LLM output language | Crew agents receive `{language}` in their `RULES` block; code identifiers and error names unchanged; only natural language prose changes |

**Supported languages:** English (`en`), Hindi (`hi`), Marathi (`mr`), Hinglish (`hinglish`)

---

## Docker Deployment

```bash
# Backend + sandbox
API_TOKEN=<secret> SANDBOX_TOKEN=<secret> docker compose up --build

# With heavy profile_rag extras (adds sentence-transformers / torch)
EXTRAS="ai agents profile_rag" docker compose up --build
```

**Container isolation:**

| Container | Network | Secrets | Resource limits |
|---|---|---|---|
| `backend` | `default` + `sandbox_net` | `API_TOKEN`, `GEMINI_API_KEY`, ... | 1 GB RAM, 256 PIDs, read-only FS |
| `sandbox` | `sandbox_net` only (no internet egress) | `SANDBOX_TOKEN` only | 768 MB RAM, 2 CPUs, 256 PIDs, read-only FS |

Both: `cap_drop: ALL`, `security_opt: no-new-privileges:true`, `tmpfs: /tmp:size=64m`.

The extension is loaded unpacked in Chrome - it is **not** part of the compose stack.

---

## Testing and Smoke Tests

```bash
# Unit + integration tests
make test          # python -m pytest backend/

# End-to-end smoke test (requires a running server)
make smoke         # bash scripts/smoke.sh

# Sandbox security evidence (every attack must be blocked)
python scripts/sandbox_check.py
```

Evidence docs:
- `docs/evidence/backend_phase0.md` - Phase 0 sandbox check output
- `docs/evidence/rag_spec_compliance.md` - Profile RAG spec compliance gaps

Evidence endpoint: `GET /admin/attacks` returns `{total, blocked, results[{name, blocked, by, detail}]}`.

---

## Makefile Targets

| Target | Command |
|---|---|
| `make setup` | `pip install -r requirements.txt` |
| `make env` | Concatenate `env/*.env.part` to `.env.example` |
| `make run` | `uvicorn app.main:app --reload --port 8000` |
| `make mock` | `MOCK=1 uvicorn app.main:app --reload --port 8000` |
| `make test` | `pytest backend/` |
| `make smoke` | `bash scripts/smoke.sh` |
| `make zip` | `bash scripts/build_extension_zip.sh` |
