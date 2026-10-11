// End-to-end UI check of the REAL built extension (extension/dist) in Chromium, against the REAL backend.
// LeetCode is mocked: Playwright serves a static page at https://leetcode.com/problems/<slug>/ (no network to leetcode.com).
//
//   cd extension && npm run build
//   npm i playwright && npx playwright install chromium        (anywhere; point PLAYWRIGHT_DIR at that folder)
//   PLAYWRIGHT_DIR=<dir containing node_modules/playwright> node scripts/e2e_extension_ui.mjs
// Needs the backend on :8000 with FEATURE_CHAT=1 (token change-me). Screenshots go to docs/evidence/ui/.
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const require = createRequire(join(process.env.PLAYWRIGHT_DIR ?? process.cwd(), "noop.js"));
const { chromium } = require("playwright");
const SHOTS = join(root, "docs", "evidence", "ui");
mkdirSync(SHOTS, { recursive: true });

let failed = 0;
const ok = (name, cond, extra = "") => { if (!cond) failed++; console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? "  — " + extra : ""}`); };

// ---------------------------------------------------------------- 1. markdown renderer in a real browser
const bundle = join(mkdtempSync(join(tmpdir(), "cq-md-")), "md.js");
execFileSync(join(root, "extension", "node_modules", ".bin", process.platform === "win32" ? "esbuild.cmd" : "esbuild"),
  [join(root, "extension/src/content/markdown.ts"), "--bundle", "--format=iife", "--global-name=CQMD", `--outfile=${bundle}`],
  { cwd: join(root, "extension"), stdio: "ignore", shell: true });
console.log("markdown bundle built");

const ext = join(root, "extension", "dist");
const ctx = await chromium.launchPersistentContext(mkdtempSync(join(tmpdir(), "cq-prof-")), {
  channel: "chromium", // new headless mode: supports MV3 extensions
  headless: true,
  timeout: 60000,
  args: [`--disable-extensions-except=${ext}`, `--load-extension=${ext}`],
  viewport: { width: 1440, height: 900 },
});

console.log("browser launched");
const mdPage = await ctx.newPage();
await mdPage.setContent("<div id='out'></div>");
await mdPage.addScriptTag({ path: bundle });
const render = (src) => mdPage.evaluate((s) => { const o = document.getElementById("out"); o.replaceChildren(CQMD.renderMarkdown(s)); return o.innerHTML; }, src);
const count = (sel) => mdPage.evaluate((q) => document.querySelectorAll(`#out ${q}`).length, sel);

await render("**Binary Search** (Easy). Given a *sorted* array and `target`.\n\n- first point\n- second **bold** point\n  - nested item\n\n1. one\n2. two");
ok("md: bold / italic / inline code", (await count("strong")) === 2 && (await count("em")) === 1 && (await count("code")) === 1);
ok("md: bullet + nested + ordered lists", (await count("ul > li")) >= 3 && (await count("ul ul li")) === 1 && (await count("ol > li")) === 2);
await render("## Plan\nText\n\n```python\nlo, hi = 0, 5\n```\n\n> note this\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n---\n[docs](https://example.com) and https://leetcode.com/problems/two-sum/");
ok("md: heading, code block with copy button, quote, table, rule", (await count("h4")) === 1 && (await count(".cq-code pre code")) === 1 && (await count(".cq-copy")) === 1
  && (await count("blockquote")) === 1 && (await count("table th")) === 2 && (await count("hr")) === 1);
ok("md: only http(s) links, safe attrs", (await count("a[href^='https://'][rel~='noopener'][target='_blank']")) === 2);
await render("<script>window.__xss=1</script><img src=x onerror='window.__xss=2'> [bad](javascript:window.__xss=3) <b>raw</b>");
ok("md: HTML / javascript: links are inert text (XSS)", (await count("script, img, b")) === 0 && (await count("a")) === 0
  && !(await mdPage.evaluate(() => window.__xss)) && (await mdPage.evaluate(() => document.getElementById("out").textContent.includes("<script>"))));
await render("Partial **bold and a code fence\n```python\nx = [1,");
ok("md: half-streamed text (open bold / open fence) does not break", (await count(".cq-code")) === 1);
await mdPage.close();

// ---------------------------------------------------------------- 2. real extension on a mocked LeetCode page
const problem = (lang, langLabel) => `<!doctype html><html><head><title>704. Binary Search - LeetCode</title></head><body style="font:16px sans-serif">
<h1 data-cy="question-title">704. Binary Search</h1><span>Easy</span>
<div data-cy="lang-select"><button>${langLabel}</button></div>
<div data-track-load="description_content"><p>Given an array of integers nums which is sorted in ascending order, and an integer target, write a function to search target in nums. If target exists, then return its index. Otherwise, return -1.</p>
<pre>Input: nums = [-1,0,3,5,9,12], target = 9
Output: 4
Explanation: 9 exists in nums and its index is 4</pre><pre>Input: nums = [-1,0,3,5,9,12], target = 2
Output: -1</pre><p>Constraints:</p><ul><li>1 &lt;= nums.length &lt;= 10^4</li></ul></div>
<pre id="code" style="background:#111;color:#eee;padding:12px;width:520px">class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo &lt; hi:
            mid = (lo + hi) // 2
            if nums[mid] == target: return mid
            if nums[mid] &lt; target: lo = mid + 1
            else: hi = mid - 1
        return -1</pre>
<script>
  const code = document.getElementById('code').innerText;
  const model = { getValue: () => code, getLanguageId: () => '${lang}', getValueInRange: () => code };
  window.monaco = { editor: { getEditors: () => [{ getModel: () => model, getSelection: () => ({}), getDomNode: () => null }] } };
</script></body></html>`;

await ctx.route("https://leetcode.com/**", (route) => route.fulfill({ status: 200, contentType: "text/html", body: route.request().url().includes("/java-problem/") ? problem("java", "Java") : problem("python", "Python3") }));
let sw = ctx.serviceWorkers()[0] ?? await ctx.waitForEvent("serviceworker");
await sw.evaluate(async () => {
  await chrome.storage.sync.set({ backendUrl: "http://localhost:8000", token: "change-me", langPref: "en" });
  await chrome.storage.local.clear();
});

const analyzeCalls = [];
ctx.on("request", (r) => { if (r.url().endsWith("/analyze")) analyzeCalls.push(r.postData()); });

async function openCard(path) {
  const page = await ctx.newPage();
  await page.goto(`https://leetcode.com/problems/${path}/`);
  await page.evaluate(() => { const r = document.createRange(); r.selectNodeContents(document.getElementById("code")); const s = getSelection(); s.removeAllRanges(); s.addRange(r); });
  const box = await page.locator("#code").boundingBox();
  await page.mouse.move(box.x + 40, box.y + 20); await page.mouse.down(); await page.mouse.up(); // mouseup shows the toolbar
  await page.evaluate(() => document.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, clientX: 100, clientY: 100 })));
  await page.locator("#cq-debug-btn").click({ timeout: 15000 });
  return page;
}

// --- Python 3: real analysis + chat
const page = await openCard("binary-search");
await page.locator(".cq-tab", { hasText: "Debug" }).waitFor({ timeout: 90000 });
const verdict = await page.locator("#tab-verdict").innerText();
ok("python: Debug result card opens with real analysis", /Oracle Verified|ORACLE VERIFIED/i.test(await page.locator(".cq-header").innerText()) && /single|Wrong|wrong|fuzz|Fuzz/i.test(verdict), (await page.locator(".cq-header").innerText()).replace(/\s+/g, " "));
await page.locator(".cq-tab", { hasText: "Chat" }).click();
await page.locator("#cq-chat-input").waitFor();
await page.waitForTimeout(1200);
ok("chat: permission card shown when the chat opens", await page.locator("text=Allow & fetch my profile").count() === 1);
await page.screenshot({ path: join(SHOTS, "1_chat_consent.png") });
await page.locator("button", { hasText: "Not now" }).click();

await page.locator("#cq-chat-input").fill("Explain this problem in simple words");
await page.locator("#cq-chat-send").click();
await page.locator(".chat-bubble:not(.user) .chat-text.md").nth(1).waitFor({ timeout: 90000 });
await page.waitForFunction(() => { const q = document.querySelector("#codequest-result-host")?.shadowRoot; return q && !q.querySelector(".cq-caret") && q.querySelectorAll(".chat-bubble:not(.user)").length >= 2; }, null, { timeout: 90000 });
const reply = page.locator(".chat-bubble:not(.user) .chat-text.md").nth(1);
const txt = await reply.innerText();
ok("chat reply is formatted: no raw ** / ``` markers", !/\*\*|```|^#{1,3} /m.test(txt), txt.slice(0, 80).replace(/\n/g, " "));
ok("chat reply has real <strong> / structure", (await reply.locator("strong, ul, ol, p, code").count()) > 0, `${await reply.locator("strong").count()} strong, ${await reply.locator("p").count()} paragraphs`);
await page.screenshot({ path: join(SHOTS, "2_chat_explain_markdown.png") });

await page.locator("#cq-chat-input").fill("Just give me the full solution code");
await page.locator("#cq-chat-send").click();
await page.waitForFunction(() => document.querySelector("#codequest-result-host").shadowRoot.querySelectorAll(".chat-bubble:not(.user)").length >= 3 && !document.querySelector("#codequest-result-host").shadowRoot.querySelector(".cq-caret"), null, { timeout: 90000 });
ok("chat: solution request refused with a 'Solution withheld' chip", (await page.locator(".chat-chip", { hasText: "Solution withheld" }).count()) === 1);
ok("chat: no code block in any reply", (await page.locator(".chat-text.md .cq-code").count()) === 0);
await page.screenshot({ path: join(SHOTS, "3_chat_refusal.png") });

await page.locator("#cq-cab-profile").click();
await page.waitForTimeout(800);
ok("profile access button reopens the permission card", await page.locator("text=Allow & fetch my profile").count() === 1);
await page.close();
const sentLang = JSON.parse(analyzeCalls[0] ?? "{}");
ok("analyze was sent with the real editor language (python3)", sentLang.language === "python3");

// --- Java: explanation-only, nothing executed
const before = analyzeCalls.length;
const jp = await openCard("java-problem");
await jp.locator(".cq-warn").waitFor({ timeout: 60000 });
const warn = await jp.locator(".cq-warn").innerText();
ok("java: banner says only Python 3 can run", /Only Python 3/i.test(warn) && /java/i.test(warn), warn.slice(0, 110));
ok("java: opens directly on the Chat tab", await jp.locator("#tab-chat.active").count() === 1);
ok("java: code was NOT sent for analysis", analyzeCalls.length === before);
await jp.screenshot({ path: join(SHOTS, "4_java_explanation_only.png") });

await ctx.close();
console.log(failed ? `\n${failed} CHECK(S) FAILED` : "\nALL UI CHECKS PASSED");
process.exit(failed ? 1 : 0);
