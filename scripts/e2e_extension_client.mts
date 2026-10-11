// Runs the extension's REAL api/client.ts against the live backend with an in-memory chrome.storage mock.
// Run (backend up, FEATURE_CHAT=1, FEATURE_PROFILE_RAG=1):  cd extension && npx tsx ../scripts/e2e_extension_client.mts
import { readFileSync } from "node:fs";

const mem = (store: Record<string, unknown>) => ({
  get: (keys: unknown, cb?: (r: Record<string, unknown>) => void) => {
    let out: Record<string, unknown> = {};
    if (keys === null || keys === undefined) out = { ...store };
    else if (typeof keys === "string") out = keys in store ? { [keys]: store[keys] } : {};
    else if (Array.isArray(keys)) keys.forEach((k) => { if (k in store) out[k] = store[k]; });
    else Object.entries(keys as Record<string, unknown>).forEach(([k, d]) => { out[k] = k in store ? store[k] : d; });
    if (cb) { cb(out); return undefined; }
    return Promise.resolve(out);
  },
  set: (o: Record<string, unknown>) => { Object.assign(store, o); return Promise.resolve(); },
  remove: (ks: string[]) => { ks.forEach((k) => delete store[k]); return Promise.resolve(); },
});
const sync: Record<string, unknown> = { token: "change-me", langPref: "en" }; // what the Options page would save
const local: Record<string, unknown> = {};
(globalThis as any).chrome = { storage: { sync: mem(sync), local: mem(local) } };

const c = await import("../extension/src/api/client.ts");
const ok = (name: string, cond: boolean, extra = "") => console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? "  — " + extra : ""}`);

const h = await c.checkHealth();
ok("health with options-page token", h.status === "ok");

const fx = JSON.parse(readFileSync(new URL("../fixtures/lc/binary-search/problem.json", import.meta.url), "utf-8"));
const cap = await c.captureProblem(fx);
ok("capture", cap.supported === true && cap.slug === "binary-search");

const learner = await c.ensureLearner();
ok("learner created + token stored", !!learner.userId && !!learner.userToken && local.cqUserToken === learner.userToken);

const bug = "class Solution:\n    def search(self, nums, target):\n        lo, hi = 0, len(nums) - 1\n        while lo < hi:\n            mid = (lo + hi) // 2\n            if nums[mid] == target: return mid\n            if nums[mid] < target: lo = mid + 1\n            else: hi = mid - 1\n        return -1\n";
const a = await c.analyzeProblem({ problem_slug: "binary-search", code: bug, language: "python3", paste_chars: 0, elapsed_ms: 1000 } as any);
ok("analyze stored under the SAME learner; fuzz caught the bug", a.results.some((r) => r.kind === "fuzz" && r.outcome === "wrong_output"), `class=${a.diagnosis?.failure_class} hint_level=${a.allowed_hint_level}`);

const hint = await c.getHint("binary-search", a.attempt_id, 1);
ok("hint level 1 (token-authenticated)", hint.locked === false && hint.text.length > 10, hint.text.slice(0, 70));
const locked = await c.getHint("binary-search", a.attempt_id, 4);
ok("hint level 4 is locked", locked.locked === true, String(locked.requirements));
const ex = await c.getExplanation(a.attempt_id, "en");
ok("explanation", /single element/.test(ex.text), ex.text.slice(0, 90));

const info = await c.chatConsentInfo();
ok("consent info", info.can_revoke === true && info.data_accessed.length > 3);
let st = await c.chatConsentStatus();
ok("consent status before: not granted", st.granted === false);

const t0 = Date.now();
st = await c.chatGrantConsent("Sahil-memane");
ok("allow -> profile fetched", st.granted && st.profile_synced, `solved=${st.summary?.solved?.All} streak=${st.summary?.streak} (${Math.round((Date.now() - t0) / 1000)}s)`);

const r1 = await c.chatSend("binary-search", "Explain this problem to me in simple words.");
ok("chat: explain problem", r1.reply.personalized === true && r1.reply.content.length > 40 && /search|sorted|target/i.test(r1.reply.content), `mode=${r1.reply.mode}`);
console.log("      >>", r1.reply.content.split(String.fromCharCode(10)).join(" ").slice(0, 400));
const r2 = await c.chatSend("binary-search", "why does my code fail?");
console.log("      >>", r2.reply.mode, r2.reply.content.split(String.fromCharCode(10)).join(" ").slice(0, 400));
ok("chat: why failing uses my attempt", /single|one element|one-element|1 element|lo|hi/i.test(r2.reply.content) && r2.thread_id === r1.thread_id, `thread reused=${r2.thread_id === r1.thread_id}`);
const r3 = await c.chatSend("binary-search", "Just give me the full solution code");
ok("chat: solution refused, no model", r3.reply.mode === "refusal" && !/def |class Solution/.test(r3.reply.content));
const r4 = await c.chatSend("binary-search", "what are my strengths and which languages do I use?");
ok("chat: personalised profile answer", r4.reply.personalized === true && /231|C\+\+/.test(r4.reply.content), r4.reply.content.slice(0, 80));

const rev = await c.chatRevokeConsent();
ok("withdraw permission", rev.granted === false);
const r5 = await c.chatSend("binary-search", "what are my strengths?");
ok("after withdrawal: not personalised", r5.reply.personalized === false && r5.reply.mode === "not_personalised");

// backend forgot us (DB reset / bad token): client must re-register and continue
local.cqUserToken = "stale-token";
const r6 = await c.chatSend("binary-search", "explain this problem");
ok("stale token -> auto re-register", !!r6.reply.content && local.cqUserToken !== "stale-token");
const dash = await c.getDashboard();
ok("dashboard for current learner", (dash as any).user_id === local.cqUserId);
