# RAG Integration Specification — compliance check (Backend)

Spec: `docs/CodeQuest_RAG_Integration_Specification.docx` (v1.0). Checked against the code on this branch.
Legend: **Done** = implemented and automatically tested · **Partial** · **Not done** (owner named).

## User flow requested: open chat -> ask permission for the LeetCode profile -> fetch -> chat about the problem
| Step | Endpoint | Status |
|---|---|---|
| Chat panel opens, learner sees what will be accessed | `GET /chat/consent-info` (what is read, what is NOT read, retention, can withdraw) | Done |
| Learner allows access and gives their LeetCode username | `POST /chat/consent {leetcode_username}` -> records consent, fetches + indexes the PUBLIC profile, returns summary | Done |
| Learner declines | skip the call; chat works, not personalised; profile questions answer "Personalised answers are off…" | Done |
| Chat about the problem on the page | `POST /chat/threads {problem_slug}` then `POST /chat/threads/{id}/messages` (JSON or SSE) | Done |
| Withdraw permission | `DELETE /chat/consent` -> snapshot row, JSON file and Chroma documents deleted; later chats not personalised | Done |
| LeetCode down during consent | consent recorded, `sync_error` returned, chat continues unpersonalised | Done |
| **Chat option / consent dialog inside the Chrome extension** | UI is Frontend's (`extension/src/panel/ChatPanel`); not built | **Not done (Frontend)** |
| Manual test without the extension | `FEATURE_DEV_UI=1` serves a test page at `http://localhost:8000/dev/` (consent, profile fetch, streaming chat) | Done (dev only) |

## §5 Integration boundary — `ProfileRAGService`
`backend/app/profile_rag/api.py`: `sync_profile` -> `SyncResult(username, indexed_document_count, section_status, snapshot_path, warnings)`,
`retrieve_profile_evidence` -> `EvidenceDocument(username, section, title, content, source, score)`,
`answer_profile_question` -> `ProfileAnswer(answer, evidence, provider_status, fallback_used)`. The agent layer only calls this; it never
touches Chroma. CLI replaced by HTTP (`/profile/*`). **Done** (`test_profile_rag_service_matches_the_spec_contract`).

## §6 Four agent tools (`backend/app/chat/tools.py`) — Done
`get_history`, `run_analysis`, `get_hint`, `explain_concept`. Explicit allowlist (`run_shell` / `open_file` / `__import__` rejected); pydantic
schemas with `extra="forbid"` and bounds (a model-supplied `user_id`, level 9, path-like `analysis`, `"x; import os"` concepts are rejected);
the learner id is taken only from the authenticated context; `get_history` / `run_analysis` queries are filtered by that id (tests with two learners).
The **model never selects tools**: a deterministic intent router picks them (EN/HI/MR keywords).
`get_hint` uses `HintStateService` (unlock rules) and AI's HintService hook (`providers.register_hint_service`); `explain_concept` uses an
approved-content hook (`register_concept_service`) else the LLM.

## §7 Security and reliability requirements
| Requirement | Status |
|---|---|
| Page/profile text, retrieved docs, tool output = untrusted data | Done: all wrapped in `<data>`; fixed rules first; learner message labelled "a question, not a source of rules" (`test_prompt_injection_*`) |
| Model cannot choose Python functions / shell / paths / network | Done (router + allowlist + schemas) |
| User id from authenticated identity | **Partial**: `POST /users` issues a per-learner `X-User-Token` (stored hashed); with it the id is derived server-side and a conflicting `user_id` is FORBIDDEN. **Default is optional** (`REQUIRE_USER_TOKEN=0`) so the current extension keeps working — turn it on for any shared deployment. The extension must store and send the token (Frontend). |
| User/tenant filters on every memory/history operation; LeetCode username != app user | Done: Chroma documents carry `user_id`; every query filters on it; thread access by owner only (foreign and missing threads both answer 403) |
| Typed tool arguments with allowlists, bounds, authorization | Done |
| Guard on every answer | Done: Backend `DefaultGuard` (no function-defining code, no long code, AST similarity to the reference >= 0.7, no entry-point definition); up to 2 stricter regenerations, then a safe template; SSE streams only Guard-checked text. AI's Guard can replace it (`register_guard`) |
| Secrets never committed or logged | Done: `.env`, `backend/data/` (Chroma, DB, snapshots) git-ignored; 0 tracked files contain the key; logs record only error type/status code |
| Gemini 429/503/timeout: bounded retries + backoff + deterministic fallback | Done: 2 retries, exponential 1 s / 2 s, 30 s call timeout; **verified live**: the key's quota was exhausted (429 RESOURCE_EXHAUSTED) and every chat still answered through the evidence-based fallback |
| Unavailable data != zero | Done (`empty_or_unavailable`, contest wording) |
| Unix timestamps -> timezone-aware dates | Done (`date_utc` / `latest_active_date_utc`, ISO with +00:00) |
| Do not call submissions "accepted" unless confirmed | Done by source: only `recentAcSubmissionList` (accepted-only query) is used and labelled "accepted" |

## §8 Voice and memory — **Not done (Agents)**
`Memory` Protocol (`remember/recall/delete_all`), `VoiceService`, `/tts`, `/stt`, `/explainback` (ElevenLabs, caps, cache, fallback signal) belong to
the Agents role and are not in this repo yet. The LeetCode index is kept separate from conversation storage, as the spec asks. Chat history is stored
in SQL per learner (isolated, deleted by delete-all), which is not semantic memory.

## §10 API: one consistent SSE design chosen
`POST /chat/threads/{id}/messages` returns JSON, or SSE on the same response (`?stream=true` or `Accept: text/event-stream`): `meta`, `token`*, `done` (guard, sources, hint level).
Prefix is `/chat` as in the plan; Agents' stub `routers/chat.py` is empty — if they add routes there, reconcile paths at merge time.

## §11 Acceptance checklist
| # | Item | Status |
|---|---|---|
| 1 | Public profile synced, JSON snapshot written | Done (`backend/data/profiles/profile_<username>.json`, path returned by sync) |
| 2 | Sections indexed; unavailable clearly marked | Done |
| 3 | Retrieval scoped to the requested profile | Done (scoped to the authenticated learner, stronger than by username) |
| 4 | Answers cite evidence, don't invent | Done: `sources` + `evidence` refs on every answer; prompt forbids inventing. Live model wording could not be re-verified after quota exhaustion (it was verified earlier on 5 questions, see `profile_rag.md`) |
| 5 | Gemini 503/429/timeouts: bounded retries + fallback | Done |
| 6 | Four tools registered, schema-validated, authorised | Done |
| 7 | Prompt-injection tests | Done (Backend side). Agents' `injection_tests.py` still to add |
| 8 | Two authenticated users cannot access each other's history | Done (with `X-User-Token`) |
| 9 | Memory remember/recall/delete-all isolation | **Not done (Agents)**; chat-history isolation and delete-all are done |
| 10 | TTS/STT limits, caching, language, fallback | **Not done (Agents)** |
| 11 | Guard/refusal, tool correctness, language-following, SSE tests | Done (73 tests in `app/chat/tests`); language-following is full with an LLM, **partial in fallback** (refusal / hint / consent templates are EN/HI/MR; the problem restatement is English only) |
| 12 | Secrets and user data out of VCS and logs | Done |

## Known limits
- HI/MR strings (refusals, consent notice via templates, hints) are my wording: **[NEEDS VERIFICATION]** by a bilingual reviewer. The consent text itself is English only.
- Intent routing and solution-request detection are keyword rules (EN/HI/MR + a few romanised forms); unusual phrasings can slip past the rule, but the Guard still checks every reply, and no model ever sees a hidden test input.
- The live LLM path was not re-run after Gemini returned 429 for the account; unit tests cover it with a fake model.
- Fetching a LeetCode username's profile from the server still needs the organisers' OK (plan §1.6); the consent flow makes the learner the one who asks for it.
