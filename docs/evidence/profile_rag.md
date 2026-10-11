# LeetCode profile RAG — what was ported and where it lives

Source: `E:\aa\codequest_leetcode_rag\codequest_leetcode_rag\` (`leetcode_client.py`, `rag_store.py`, `answerer.py`,
`config.py`, `app.py`, `README.md`). Not copied: `.env` (secrets), `data/` (a real person's profile snapshot),
`.venv`, `__pycache__`. `app.py` (CLI) is replaced by HTTP endpoints.

## Where it goes in the plan (§2, §4, §5)
The plan has no LeetCode-profile feature, so this is a new, Backend-owned package that touches no path owned by AI,
Agents or Frontend. It reuses the plan's own seams: the vector-memory idea (Agents' `agents/memory/`), the LLM client
(AI's `ai/llm/client.py`) and the dashboard/personalisation data (Backend `/dashboard`, AI `learner/`).

| Original | New location | Owner | Notes |
|---|---|---|---|
| `leetcode_client.py` | `backend/app/profile_rag/client.py` | Backend | >= 1 s between calls, username validation, injectable session, 20 recent items |
| `rag_store.py` (documents, question->section map) | `backend/app/profile_rag/documents.py` | Backend | pure functions, no Chroma; plus `summarize()` for the dashboard |
| `rag_store.py` (`ProfileVectorStore`) | `backend/app/profile_rag/store.py` | Backend | Chroma + MiniLM, **lazy import**, keyed by CodeQuest `user_id`, new `delete_user()` |
| `answerer.py` | `backend/app/profile_rag/answerer.py` | Backend | LLM is a hook (`providers.register_llm`) so AI's client can replace Gemini; injection-safe prompt |
| `config.py` | `backend/app/config.py` | Backend | same env names; `.env` now auto-loaded; flag `FEATURE_PROFILE_RAG` (default off) |
| `app.py sync/ask/chat` | `backend/app/routers/profile_rag.py` + `profile_rag/service.py` | Backend | `POST /profile/sync`, `POST /profile/ask`, `GET/DELETE /profile/{user_id}` |
| `requirements.txt` | `requirements/profile_rag.txt` (+ `requests`, `python-dotenv` in base) | Backend | included by the root `requirements.txt` and the Docker `EXTRAS` |
| `data/profile_<name>.json` snapshot | table `leetcode_profile_snapshots` | Backend | wiped by delete-all |

Integration: `/dashboard/{id}` returns `leetcode` (solved by difficulty, top languages, contest rating, streak) when a
profile is synced; `DELETE /users/{id}/data` removes the snapshot row **and** the Chroma documents.

## Changes vs the original (and why)
- **Per-learner index** (`user_id` metadata) instead of per-LeetCode-username: one learner cannot read another's index; delete-all works.
- **Rate limit 0.35 s -> 1 s** and a **10-minute cache** per learner/username (`PROFILE_SYNC_MIN_INTERVAL_S`): plan §1.6 says user-triggered, single-profile, >= 1 s between calls.
- **Prompt-injection defence**: profile text (aboutMe, skill tags) is user-written, so it is wrapped in `<data>`, rules come first, the model is told never to follow instructions inside it and never to write solution code (plan §5.4).
- **No secrets in responses**: LLM failures return the exception type only (the original printed the exception text, which can contain a key). A test proves a leaked key string is not echoed.
- **Honest modes**: `llm | evidence_only | llm_failed | no_data` in every answer; `sources` lists the sections used.
- **Heavy deps optional**: without chromadb/sentence-transformers the API answers `UPSTREAM_FAILED` with a clear message and delete-all still works.

## Verified
- 25 new tests (`backend/app/profile_rag/tests/`), full suite 124 passed. They use a fake LeetCode GraphQL session (no network), real **ChromaDB 1.5.9** with a deterministic fake embedder, and the real FastAPI app: partial-section failure, missing profile, username validation, document coverage and stable ids, calendar summary, section routing, persistence across store instances, replace-on-resync, per-user isolation, cache/force, evidence-only vs LLM, injection wrapper, error-text redaction, dashboard summary, delete-all across SQL + Chroma, RAG-unavailable path.

## NOT verified / open
- **No live LeetCode call was made** and the **real Gemini call was not run** (no key used). LeetCode's GraphQL is unofficial: field names and terms can change [VERIFY].
- The real **MiniLM embedder (sentence-transformers/torch) was not installed or run** here; tests used a fake embedder. First real run downloads the model.
- **Compliance [NEEDS VERIFICATION]**: plan §1.6 asks organisers whether live third-party reads are acceptable. This feature fetches a *username's public profile from our server* (the plan's capture runs in the learner's browser). The API cannot prove the username belongs to the learner. Keep it behind the flag until organisers confirm; replay (a stored snapshot) is the fallback.
- Overlap to reconcile after AI/Agents merge: Agents' `agents/memory/vector_store.py` (could share one Chroma client/embedder via `store.set_store`) and AI's `llm/client.py` (call `providers.register_llm`).
- Not done: sending the profile summary into AI's learner model / personalisation; Hindi/Marathi answers (the LLM is asked in the question's language only if the model chooses to).

## Enable it
1. `pip install -r requirements/profile_rag.txt`
2. In your untracked `.env` (repo root): `FEATURE_PROFILE_RAG=1`, `GEMINI_API_KEY=<your key>` (optional; without it answers show the retrieved evidence).
3. Restart the backend, then:
```bash
curl -H "X-API-Token: change-me" -H "content-type: application/json" -XPOST localhost:8000/profile/sync -d '{"user_id":"u1","username":"Sahil-memane"}'
curl -H "X-API-Token: change-me" -H "content-type: application/json" -XPOST localhost:8000/profile/ask  -d '{"user_id":"u1","question":"Which languages has this user solved problems in?"}'
```
