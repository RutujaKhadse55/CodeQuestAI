// ─── Shadow-DOM Toolbar — content script ──────────────────────────────────
// Shows a floating "🔍 Debug" button on text selection anywhere on the page,
// including the Monaco code editor.
//
// Monaco fix: LeetCode's code editor runs in the page's JS world.
// Content scripts are isolated — window.monaco is undefined here.
// We ask the Service Worker to run chrome.scripting.executeScript({ world:"MAIN" })
// which can access window.monaco directly, bypassing both isolation and CSP.

import { disabledReason } from "./guards";
import { LOGO_DATA_URL } from "../assets/logo";
import { orchestrateDebug } from "./orchestrate";
import { getResultCard, playText } from "./result_card";
import type { ConsentInfo, ConsentStatus } from "../api/types";

// ── Phase 2: paste + timing tracking ──────────────────────────────────────────
/** Running total of pasted characters since page load. Sent in /analyze. */
export let totalPasteChars = 0;
/** Page load time — elapsed_ms = Date.now() - pageLoadTime when Debug clicked. */
export const pageLoadTime = Date.now();

// ── context guard ─────────────────────────────────────────────────────────────

function isContextValid(): boolean {
  try { return !!chrome.runtime?.id; } catch { return false; }
}

/**
 * After the extension is reloaded/updated, content scripts already injected into open tabs lose their connection
 * ("Extension context invalidated"). Remove the dead UI and show one hint instead of throwing errors.
 */
let staleNoticeShown = false;
function onContextInvalidated(): void {
  document.getElementById("codequest-toolbar-host")?.remove();
  document.getElementById("codequest-result-host")?.remove();
  if (staleNoticeShown) return;
  staleNoticeShown = true;
  const n = document.createElement("div");
  n.textContent = "CodeQuest AI was updated — refresh this page to use it again.";
  n.style.cssText = "position:fixed;bottom:16px;right:16px;z-index:2147483647;background:#14141c;color:#fff;border:2px solid #f5c542;"
    + "border-radius:10px;padding:10px 14px;font:13px system-ui,sans-serif;box-shadow:0 4px 20px rgba(0,0,0,.5)";
  document.documentElement.appendChild(n);
  setTimeout(() => n.remove(), 8000);
}
const isInvalidated = (v: unknown): boolean => /context invalidated|Extension context/i.test(String((v as Error)?.message ?? v));
window.addEventListener("unhandledrejection", (e) => { if (isInvalidated(e.reason)) { e.preventDefault(); onContextInvalidated(); } });
window.addEventListener("error", (e) => { if (isInvalidated(e.error ?? e.message)) { e.preventDefault(); onContextInvalidated(); } });

// ── styles ────────────────────────────────────────────────────────────────────

const TOOLBAR_CSS = `
  :host { all: initial; }
  #cq-toolbar {
    position: fixed;
    display: none;
    align-items: center;
    gap: 6px;
    background: #14141c;
    border: 2px solid #f5c542;
    border-radius: 14px;
    padding: 8px 12px;
    box-shadow: 0 6px 28px rgba(0,0,0,0.6);
    pointer-events: all;
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 12px;
    color: #e2e8f0;
    animation: cq-fade-in 0.12s ease;
    z-index: 2147483647;
    max-width: calc(100vw - 16px);
  }
  #cq-toolbar.visible { display: flex; }
  @keyframes cq-fade-in {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .cq-brand { display: flex; align-items: center; gap: 8px; padding-right: 10px; margin-right: 4px; border-right: 1px solid #2d2d3a; }
  .cq-brand img { width: 30px; height: 30px; border-radius: 8px; background: #fff; padding: 2px; box-sizing: border-box; }
  .cq-brand-name { font-weight: 700; font-size: 13px; color: #fff; line-height: 1.15; white-space: nowrap; }
  .cq-brand-sub { font-size: 11px; color: #94a3b8; white-space: nowrap; }
  .cq-act {
    display: flex; flex-direction: column; align-items: center; gap: 3px;
    background: none; border: none; border-radius: 8px; cursor: pointer;
    color: #cbd5e1; font: inherit; font-size: 11px; font-weight: 600;
    padding: 4px 9px; min-width: 52px; transition: background .12s, color .12s;
  }
  .cq-act .ic { font-size: 18px; line-height: 1; }
  .cq-act:hover { background: #26263a; color: #fff; }
  .cq-act:focus-visible { outline: 2px solid #f5c542; }
  #cq-auth { display: none; flex-direction: column; gap: 6px; width: 300px; }
  #cq-toolbar.auth #cq-actions { display: none !important; }
  #cq-toolbar.auth #cq-auth { display: flex; }
  #cq-toolbar.auth .cq-brand { border-right: none; }
  .cq-auth-title { font-weight: 700; font-size: 12px; color: #fff; }
  .cq-auth-text { font-size: 11px; color: #94a3b8; line-height: 1.4; }
  #cq-auth input {
    background: #1f1f2e; border: 1px solid #3a3a52; border-radius: 6px; color: #fff;
    padding: 6px 8px; font: inherit; font-size: 12px; width: 100%; box-sizing: border-box;
  }
  #cq-auth input:focus { outline: 2px solid #f5c542; border-color: transparent; }
  .cq-auth-row { display: flex; gap: 6px; }
  .cq-btn { border: none; border-radius: 6px; padding: 6px 10px; font: inherit; font-size: 12px; font-weight: 600; cursor: pointer; }
  .cq-btn.primary { background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; }
  .cq-btn.ghost { background: #26263a; color: #cbd5e1; }
  .cq-btn[disabled] { opacity: .5; cursor: default; }
  #cq-status { font-size: 11px; color: #94a3b8; min-height: 14px; }
  #cq-status.err { color: #f87171; }
`;

// ── refs ──────────────────────────────────────────────────────────────────────

let toolbarEl: HTMLDivElement | null = null;
let shadowRoot: ShadowRoot | null = null;
let lastSelectedText = "";
let hostEl: HTMLDivElement | null = null;

// ── toolbar init ──────────────────────────────────────────────────────────────

function initToolbar(): void {
  hostEl = document.createElement("div");
  hostEl.id = "codequest-toolbar-host";
  hostEl.style.cssText =
    "position:fixed;top:0;left:0;width:0;height:0;z-index:2147483647;pointer-events:none;";
  document.documentElement.appendChild(hostEl);

  shadowRoot = hostEl.attachShadow({ mode: "open" });

  const style = document.createElement("style");
  style.textContent = TOOLBAR_CSS;
  shadowRoot.appendChild(style);

  toolbarEl = document.createElement("div");
  toolbarEl.id = "cq-toolbar";
  toolbarEl.setAttribute("role", "toolbar");
  toolbarEl.setAttribute("aria-label", "CodeQuest AI");
  toolbarEl.addEventListener("mousedown", (e) => e.stopPropagation());
  shadowRoot.appendChild(toolbarEl);

  const brand = document.createElement("div");
  brand.className = "cq-brand";
  const logo = document.createElement("img");
  logo.src = LOGO_DATA_URL; logo.alt = "";
  const names = document.createElement("div");
  const nm = document.createElement("div"); nm.className = "cq-brand-name"; nm.textContent = "CodeQuest AI";
  const sub = document.createElement("div"); sub.className = "cq-brand-sub"; sub.id = "cq-brand-sub"; sub.textContent = "Analyze selection";
  names.append(nm, sub); brand.append(logo, names);
  toolbarEl.appendChild(brand);

  // Action row: each button opens the matching tab of the sidebar panel.
  const actions = document.createElement("div");
  actions.id = "cq-actions"; actions.style.cssText = "display:flex;gap:2px;";
  for (const a of ACTIONS) {
    const b = document.createElement("button");
    b.className = "cq-act"; b.dataset.action = a.id; b.title = a.title;
    const ic = document.createElement("span"); ic.className = "ic"; ic.textContent = a.icon;
    const lb = document.createElement("span"); lb.textContent = a.label;
    b.append(ic, lb);
    b.addEventListener("click", () => runAction(a.id));
    actions.appendChild(b);
  }
  toolbarEl.appendChild(actions);

  // Authorization step (shown instead of the actions until the learner decides).
  const auth = document.createElement("div");
  auth.id = "cq-auth";
  const aTitle = document.createElement("div"); aTitle.className = "cq-auth-title"; aTitle.id = "cq-auth-title";
  const aText = document.createElement("div"); aText.className = "cq-auth-text"; aText.id = "cq-auth-text";
  const aUser = document.createElement("input"); aUser.id = "cq-auth-user"; aUser.placeholder = "Your public LeetCode username";
  aUser.autocomplete = "off"; aUser.spellcheck = false;
  const aRow = document.createElement("div"); aRow.className = "cq-auth-row";
  const aAllow = document.createElement("button"); aAllow.className = "cq-btn primary"; aAllow.id = "cq-auth-allow"; aAllow.textContent = "Allow & continue";
  const aSkip = document.createElement("button"); aSkip.className = "cq-btn ghost"; aSkip.id = "cq-auth-skip"; aSkip.textContent = "Not now";
  aRow.append(aAllow, aSkip);
  const statusEl = document.createElement("div"); statusEl.id = "cq-status";
  auth.append(aTitle, aText, aUser, aRow, statusEl);
  toolbarEl.appendChild(auth);
  aAllow.addEventListener("click", () => { void submitAuth(); });
  aSkip.addEventListener("click", skipAuth);
  aUser.addEventListener("keydown", (e) => { e.stopPropagation(); if (e.key === "Enter") void submitAuth(); });
  aUser.addEventListener("keyup", (e) => e.stopPropagation());

  // ── 1. Native selection (problem description, constraints, examples) ──────
  document.addEventListener("mouseup", handleMouseUp);

  // ── 2. Monaco selection (code editor) ────────────────────────────────────
  watchForMonacoEditor();

  // ── 3. Hide on outside click ──────────────────────────────────────────────
  document.addEventListener("mousedown", (e) => {
    if (!e.composedPath().includes(hostEl!)) hideToolbar();
  });

  // ── 4. Paste detection (Phase 2) ─────────────────────────────────────────
  //    LeetCode's editor fires paste on the hidden textarea inside Monaco.
  document.addEventListener("paste", (e) => {
    const pasted = e.clipboardData?.getData("text") ?? "";
    totalPasteChars += pasted.length;
  }, true);

  // ── 5. Context menu messages from SW ──────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg: { type: string }) => {
    if (msg.type === "CONTEXT_MENU_DEBUG" || msg.type === "CONTEXT_MENU_DEBUG_ALL") {
      runAction("debug");
    }
  });

  console.info("[CQ] Toolbar ready.");
}

// ── Monaco editor watcher ─────────────────────────────────────────────────────

function watchForMonacoEditor(): void {
  const attach = (el: HTMLElement) => {
    if ((el as HTMLElement & { _cqDone?: boolean })._cqDone) return;
    (el as HTMLElement & { _cqDone?: boolean })._cqDone = true;

    el.addEventListener("mouseup", () => {
      // Give Monaco ~100ms to finalise its internal selection state
      setTimeout(askSwForMonacoSelection, 100);
    });
    console.info("[CQ] Attached mouseup to Monaco editor container.");
  };

  const scan = () =>
    document.querySelectorAll<HTMLElement>(".monaco-editor").forEach(attach);

  scan(); // immediate
  const obs = new MutationObserver(scan);
  obs.observe(document.body, { childList: true, subtree: true });
}

async function askSwForMonacoSelection(): Promise<void> {
  if (!isContextValid()) return;
  try {
    const result = await chrome.runtime.sendMessage({ type: "GET_MONACO_SELECTION" }) as {
      text: string;
      top: number; bottom: number; left: number; right: number;
    } | null;

    if (result?.text && result.text.length >= 1) {
      lastSelectedText = result.text;
      // Build a DOMRect from the returned values for toolbar positioning
      const rect = new DOMRect(
        result.left,
        result.top,
        result.right - result.left,
        result.bottom - result.top
      );
      showToolbarAt(rect);
    }
  } catch {
    // SW not available — ignore silently
  }
}

// ── native mouse-up handler ───────────────────────────────────────────────────

function handleMouseUp(e: MouseEvent): void {
  if (hostEl && e.composedPath().includes(hostEl)) return; // clicks inside the toolbar must not re-trigger it
  setTimeout(() => {
    const sel = window.getSelection();
    const text = sel?.toString().trim() ?? "";

    if (text.length >= 2 && sel && sel.rangeCount > 0) {
      const rect = sel.getRangeAt(0).getBoundingClientRect();
      if (rect.width > 0 || rect.height > 0) {
        lastSelectedText = text;
        showToolbarAt(rect);
        return;
      }
    }
    // If no native selection and Monaco didn't fire, hide
    // (Monaco fires its own listener above — don't hide here)
  }, 30);
}

// ── positioning ───────────────────────────────────────────────────────────────

function showToolbarAt(rect: DOMRect): void {
  if (!toolbarEl) return;
  lastRect = rect;
  void prepareAuth().then(() => positionToolbar());
}

function positionToolbar(): void {
  if (!toolbarEl || !lastRect) return;
  const M = 8;
  toolbarEl.classList.add("visible"); // visible first so its real size can be measured
  const TH = toolbarEl.offsetHeight || 64, TW = toolbarEl.offsetWidth || 440;
  let top = lastRect.top - TH - M;
  if (top < M) top = lastRect.bottom + M;
  top = Math.max(M, Math.min(top, window.innerHeight - TH - M));
  let left = lastRect.left + lastRect.width / 2 - TW / 2;
  left = Math.max(M, Math.min(left, window.innerWidth - TW - M));
  toolbarEl.style.top = `${top}px`;
  toolbarEl.style.left = `${left}px`;
}

function hideToolbar(): void {
  toolbarEl?.classList.remove("visible");
}

// ── authorization (profile consent) at selection time ─────────────────────────

type AuthState = "unknown" | "ok" | "needed";
let authState: AuthState = "unknown";
let lastRect: DOMRect | null = null;
let consentInfo: ConsentInfo | null = null;

function call<T>(m: object): Promise<(T & { error?: string }) | null> {
  try {
    return (chrome.runtime.sendMessage(m) as Promise<(T & { error?: string }) | null>).catch(() => null);
  } catch { return Promise.resolve(null); }
}

function setStatus(text: string, isErr = false): void {
  const el = shadowRoot?.getElementById("cq-status");
  if (!el) return;
  el.textContent = text;
  el.className = isErr ? "err" : "";
}

function showAuthView(on: boolean): void {
  toolbarEl?.classList.toggle("auth", on);
  const sub = shadowRoot?.getElementById("cq-brand-sub");
  if (sub) sub.textContent = on ? "Authorize to continue" : "Analyze selection";
}

/** Decide whether to show the actions or the authorization step. Backend offline / chat disabled → just show actions. */
async function prepareAuth(): Promise<void> {
  if (!isContextValid()) return;
  if (authState === "unknown") {
    const st = await call<ConsentStatus>({ type: "CHAT_STATUS" });
    if (!st || st.error || st.granted) authState = "ok";
    else {
      const asked = (await chrome.storage.local.get("cqConsentAsked")).cqConsentAsked;
      authState = asked ? "ok" : "needed";
    }
  }
  if (authState === "needed") {
    if (!consentInfo) {
      const info = await call<ConsentInfo>({ type: "CHAT_CONSENT_INFO" });
      if (!info || info.error) authState = "ok"; else consentInfo = info;
    }
    if (consentInfo) {
      const t = shadowRoot?.getElementById("cq-auth-title"), x = shadowRoot?.getElementById("cq-auth-text");
      if (t) t.textContent = consentInfo.title;
      if (x) x.textContent = consentInfo.text;
    }
  }
  showAuthView(authState === "needed");
}

async function submitAuth(): Promise<void> {
  const input = shadowRoot?.getElementById("cq-auth-user") as HTMLInputElement | null;
  const allow = shadowRoot?.getElementById("cq-auth-allow") as HTMLButtonElement | null;
  const skip = shadowRoot?.getElementById("cq-auth-skip") as HTMLButtonElement | null;
  const name = input?.value.trim() ?? "";
  if (!name) { setStatus("Enter your LeetCode username first.", true); return; }
  if (allow) allow.disabled = true;
  if (skip) skip.disabled = true;
  setStatus("Fetching your public profile… (this can take ~30 s)");
  const st = await call<ConsentStatus>({ type: "CHAT_GRANT", username: name });
  if (allow) allow.disabled = false;
  if (skip) skip.disabled = false;
  if (!st || st.error) { setStatus("Could not save permission: " + (st?.error ?? "backend unreachable"), true); return; }
  try { await chrome.storage.local.set({ cqConsentAsked: true }); } catch { /* ignore */ }
  authState = "ok";
  setStatus("");
  showAuthView(false);
  positionToolbar();
}

function skipAuth(): void {
  try { void chrome.storage.local.set({ cqConsentAsked: true }); } catch { /* ignore */ }
  authState = "ok";
  setStatus("");
  showAuthView(false);
  positionToolbar();
}

// ── actions: each opens the matching tab of the sidebar ───────────────────────

type ActionId = "debug" | "explain" | "hint" | "concept" | "listen" | "chat";
const ACTIONS: Array<{ id: ActionId; icon: string; label: string; title: string }> = [
  { id: "debug",   icon: "🪲", label: "Debug",   title: "Run your code and diagnose it (Debug tab)" },
  { id: "explain", icon: "📄", label: "Explain", title: "Explain the problem (and your selection) from its link (Explain tab)" },
  { id: "hint",    icon: "💡", label: "Hint",    title: "Tiered hints, no full solution (Hints tab)" },
  { id: "concept", icon: "🎓", label: "Concept", title: "The idea or pattern behind the selection (Chat tab)" },
  { id: "listen",  icon: "🔊", label: "Listen",  title: "Read the selection aloud" },
  { id: "chat",    icon: "💬", label: "Chat",    title: "Ask about the selection (Chat tab)" },
];

function currentSlug(): string {
  return location.pathname.match(/\/problems\/([^/?#]+)/)?.[1] ?? "unknown";
}

function runAction(id: ActionId): void {
  if (!isContextValid()) {
    document.getElementById("codequest-toolbar-host")?.remove();
    return;
  }
  const selected = window.getSelection()?.toString().trim() || lastSelectedText;
  const snippet = selected.length > 1500 ? selected.slice(0, 1500) + "…" : selected;
  const card = getResultCard();
  hideToolbar();

  switch (id) {
    case "debug": return runAnalysis(selected, "verdict");
    case "hint":  return runAnalysis(selected, "hints");
    case "listen":
      playText(selected);
      return;
    case "explain":
      return card.openExplain(snippet || undefined);
    case "concept":
      return card.openChat(currentSlug(), snippet
        ? `What concept or pattern is behind this part? Explain the idea without giving the full solution:\n"${snippet}"`
        : "What concept or pattern is behind this problem? Explain the idea without giving the full solution.", true);
    case "chat":
      return card.openChat(currentSlug(), snippet ? `About this: "${snippet}"\n` : undefined, false);
  }
}

/** Capture + analyze, then open the panel on the requested tab. */
function runAnalysis(selectedText: string, tab: "verdict" | "hints"): void {
  const card = getResultCard();
  card.showLoading("Capturing problem + analyzing code…");
  orchestrateDebug(selectedText || undefined)
    .then((outcome) => {
      if (outcome.ok) {
        const lang = outcome.data.problem.lang_selected;
        card.setReviewCode(outcome.data.code, lang);
        card.showResults(outcome.data.analysis, outcome.data.problem.slug, lang, outcome.data.explanationOnly, outcome.data.explanationOnly ? undefined : tab);
      } else {
        card.showError(outcome.error.message, outcome.error.detail);
      }
    })
    .catch((err: unknown) => {
      card.showError("Unexpected error", String(err));
    });
}

// ── entry point ───────────────────────────────────────────────────────────────

function main(): void {
  const reason = disabledReason();
  if (reason) { console.info(`[CQ] ${reason}`); return; }
  initToolbar();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", main);
} else {
  main();
}
