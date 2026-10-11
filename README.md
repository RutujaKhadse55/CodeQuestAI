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
