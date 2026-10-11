# CodeQuestAI

AI coding mentor & debugging missions for LeetCode learners (VORTEXA 3.0, PS E-02).
Plan: [docs/CodeQuest_AI_Hackathon_Implementation_Plan_v3.md](docs/CodeQuest_AI_Hackathon_Implementation_Plan_v3.md)

## Backend quick start
1. `pip install -r requirements.txt`
2. `cat env/*.env.part > .env.example && cp .env.example .env` (or `make env`), then set `API_TOKEN`
3. `cd backend && MOCK=1 python -m uvicorn app.main:app --port 8000` (`make mock`) — canned responses; drop `MOCK=1` for real routers (`make run`)

All requests need header `X-API-Token: <API_TOKEN>`. Tests: `cd backend && python -m pytest`. Smoke: `bash scripts/smoke.sh`.
Contract: [openapi.yaml](openapi.yaml) and `backend/app/contracts/`.
Sandbox check: `python scripts/sandbox_check.py` (see [docs/evidence/backend_phase0.md](docs/evidence/backend_phase0.md)).

## Problem chat with profile consent (FEATURE_CHAT=1)
Open chat -> `GET /chat/consent-info` -> learner allows -> `POST /chat/consent {leetcode_username}` (fetches the PUBLIC profile) ->
`POST /chat/threads {problem_slug}` -> `POST /chat/threads/{id}/messages` (JSON or SSE). Try it without the extension:
set `FEATURE_CHAT=1`, `FEATURE_PROFILE_RAG=1`, `FEATURE_DEV_UI=1` in `.env`, then open http://localhost:8000/dev/.
Spec compliance and gaps: [docs/evidence/rag_spec_compliance.md](docs/evidence/rag_spec_compliance.md).

## AI agent crew (FEATURE_CREW=1)
Ported from the `CodeQuest_Agent` CrewAI prototype into `backend/app/crew/` (roles/tasks in `crew/config/*.yaml`).
Set `FEATURE_CREW=1` and `GEMINI_API_KEY` (without a key every agent degrades to deterministic content).

| Endpoint | Agent | Notes |
|---|---|---|
| `POST /crew/explain` | Problem Explainer | structured explanation of statement, constraints, examples, your code |
| `POST /crew/tests` | Test Case Generator | model-written cases, **run in the sandbox** (verified oracle output wins over the model's expected value) |
| `POST /crew/debug` | Debugger | diagnosis, root cause, fix steps in words; corrected full code withheld unless `CREW_ALLOW_FIX_CODE=1` |
| `POST /crew/trace` | Trace Analyst | real line-by-line sandbox trace (`harness.py` `steps` mode); non-Python = labelled static simulation |
| `POST /hint` | Hint Mentor | registered through `providers.register_hint_service`; 4 tiers, Guard-checked, template fallback |

Body: `{problem_slug, code?, language?, selected_code?, response_language: en|hi|mr|hinglish, attempt_id?, input?, expected?}`.
All model text passes the Guard; problem text, learner code and execution output are untrusted `<data>`.
