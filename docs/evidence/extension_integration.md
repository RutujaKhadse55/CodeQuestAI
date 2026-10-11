# Extension <-> backend integration (after Sahil's "UI updations", e8f48f3)

## What the teammate's UI already had
Debug button -> result card with tabs Debug / Trace / Hints / Hidden / **Chat**; calls `/problems/capture`, `/analyze`, `/hint`, `/explain`;
TTS via an offscreen document. The Chat tab was a **canned local reply** (`chatReply()`), not connected to the backend chat, and there was no consent dialog.

## Mismatches found and how each was closed
| # | Problem | Fix | Where |
|---|---|---|---|
| 1 | Options page saves the API token as `token`, `client.ts` read `backendToken` (default `"dev"`): a token typed in Options was **ignored** and every call got 401 | `getConfig()` now prefers `token`, falls back to `backendToken`; default is `change-me` (the backend's default) | `extension/src/api/client.ts` |
| 2 | `/hint` and `/explain` are AI-owned and not implemented in the real backend (mock only) -> Hints tab and explanation would 404 | Backend fallbacks `routers/zz_fallbacks.py`: 4 tiers of Socratic hints from the stored diagnosis, locked by attempts/time; plain-language explanation. AI's real routers win automatically when merged (they load first) | backend |
| 3 | Attempts were saved as `user_id="local-user"` while chat acts as the authenticated learner, so chat could not see "my attempt" | `analyzeProblem` now sends the learner id from `POST /users`; hints/explain/chat use the same learner (`X-User-Token`) | `client.ts` |
| 4 | Chat tab not connected; no permission step | Chat tab now calls the backend (`CHAT_SEND`), shows the consent card when the chat opens, has a **Profile access** button (allow / withdraw), falls back to the old local replies with an "Offline mode" note if the backend or chat is unavailable | `result_card.ts`, `service_worker.ts`, `client.ts`, `types.ts` |
| 5 | TS type error (`res.divergence`) | added optional `divergence` to the `AnalyzeResponse` type; `npm run typecheck` is clean | `types.ts` |

Changes in the Frontend files are small and localised (marked in code); expect to merge them with Sahil's next edits of `result_card.ts` / `client.ts`.

## Verified (automatically)
`scripts/e2e_extension_client.mts` runs the extension's **real `api/client.ts`** (chrome.storage mocked) against the live backend: **18/18 pass** —
health with the Options token, capture, learner creation, analyze under the same learner (fuzz catches an example-passing bug), hint 1 (text) and hint 4 (locked),
explanation, consent info/status, **allow -> real LeetCode profile fetched (231 solved, streak 45)**, chat (explain, why-failing uses my attempt, solution refused without a model,
personalised profile answer), **withdraw permission**, not personalised afterwards, stale token -> automatic re-registration, dashboard for the learner.
`npm run typecheck` and `npm run build` pass. **Not verified:** the actual Chrome UI (clicks, styling, TTS) — nobody drove a real browser here.

## Steps to check it in Chrome
1. `.env` (repo root, untracked) must contain: `FEATURE_CHAT=1`, `FEATURE_PROFILE_RAG=1`, optionally `GEMINI_API_KEY=...` (without it the chat answers from facts only). Start Docker Desktop (the sandbox runs code in it).
2. Start the backend: `cd backend && python -m uvicorn app.main:app --port 8000` and check `http://localhost:8000/health` with header `X-API-Token: change-me`.
3. Build the extension: `cd extension && npm ci && npm run build`. In `chrome://extensions` (Developer mode) **Load unpacked -> `extension/dist`**; if already loaded click the reload icon, then refresh the LeetCode tab.
4. Extension **Options**: backend URL `http://localhost:8000`, token `change-me`, save.
5. Open a LeetCode problem (e.g. Binary Search, **editor language Python 3**), select some code, click **Debug**. Check: result card opens; Debug tab shows per-test results + "oracle-verified" for Two Sum / Binary Search / Maximum Subarray (other problems show "unverified").
6. Check **Hints** tab: level 1 text appears; level 4 is locked ("Unlocks after 4 attempts or 10 minutes"). Run Debug again a few times to unlock more.
7. Open the **Chat** tab:
   - The **permission card** appears ("Allow CodeQuest AI to use your public LeetCode profile?"). Enter your LeetCode username and press **Allow & fetch my profile** (takes ~10-35 s). A note confirms "Profile loaded … N solved".
   - Ask: "Explain this problem in simple words", "Why does my code fail?", "What are my strengths and which languages do I use?" (personalised, shows "🔒 personalised").
   - Ask "Just give me the full solution" -> refusal + hint offer (shows "solution withheld"). Also try a Hindi/Marathi sentence.
   - Press **🔒 Profile access** -> permission withdrawn, profile data deleted; ask about your strengths again -> "Personalised answers are off…".
   - **Not now** on the card: chat still works without personalisation (the card is not shown again; use 🔒 Profile access to change it).
8. If something looks wrong: service worker console (`chrome://extensions` -> CodeQuest -> *service worker*), backend log `backend_server.err.log`, and `GET /chat/consent-info` (502 "chat is disabled" means `FEATURE_CHAT` is off).

## Known issues (Frontend side, not changed)
- `orchestrate.ts` always sends `lang_selected: "python3"` even when the editor is Java/C++, so non-Python code is executed as Python and fails with a SyntaxError. The language must be sent honestly (the backend then answers `UNSUPPORTED_LANGUAGE` / explanation-only).
- Chat replies are not streamed in the UI (the SW uses the JSON reply); the backend SSE is ready if they want streaming.
- The consent text is English only; HI/MR strings are unreviewed.
- With `REQUIRE_USER_TOKEN=0` (default) the backend also accepts anonymous `user_id`s; set it to 1 for shared use (the extension already sends the token).
