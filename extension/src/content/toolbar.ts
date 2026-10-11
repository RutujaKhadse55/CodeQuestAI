// ─── Shadow-DOM Toolbar — content script ──────────────────────────────────
// Shows a floating "🔍 Debug" button on text selection anywhere on the page,
// including the Monaco code editor.
//
// Monaco fix: LeetCode's code editor runs in the page's JS world.
// Content scripts are isolated — window.monaco is undefined here.
// We ask the Service Worker to run chrome.scripting.executeScript({ world:"MAIN" })
// which can access window.monaco directly, bypassing both isolation and CSP.

import { disabledReason } from "./guards";

// ── Phase 2: paste + timing tracking ──────────────────────────────────────────
/** Running total of pasted characters since page load. Sent in /analyze. */
export let totalPasteChars = 0;
/** Page load time — elapsed_ms = Date.now() - pageLoadTime when Debug clicked. */
export const pageLoadTime = Date.now();

// ── context guard ─────────────────────────────────────────────────────────────

function isContextValid(): boolean {
  try { return !!chrome.runtime?.id; } catch { return false; }
}

// ── styles ────────────────────────────────────────────────────────────────────

const TOOLBAR_CSS = `
  :host { all: initial; }
  #cq-toolbar {
    position: fixed;
    display: none;
    align-items: center;
    gap: 8px;
    background: #1a1a2e;
    border: 1px solid #2d3a5e;
    border-radius: 8px;
    padding: 6px 14px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.55);
    pointer-events: all;
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 13px;
    color: #e2e8f0;
    animation: cq-fade-in 0.12s ease;
    z-index: 2147483647;
  }
  #cq-toolbar.visible { display: flex; }
  @keyframes cq-fade-in {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  #cq-debug-btn {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 4px 14px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    transition: opacity 0.15s;
    white-space: nowrap;
  }
  #cq-debug-btn:hover { opacity: 0.85; }
  #cq-status {
    font-size: 12px;
    color: #94a3b8;
    white-space: nowrap;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
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
  shadowRoot.appendChild(toolbarEl);

  const btn = document.createElement("button");
  btn.id = "cq-debug-btn";
  btn.textContent = "🔍 Debug";
  btn.title = "CodeQuest AI: Analyze selected code or text";
  btn.addEventListener("mousedown", (e) => e.stopPropagation());
  btn.addEventListener("click", onDebugClick);
  toolbarEl.appendChild(btn);

  const statusEl = document.createElement("span");
  statusEl.id = "cq-status";
  toolbarEl.appendChild(statusEl);

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
      onDebugClick();
    }
  });

  // ── 4. Context menu ───────────────────────────────────────────────────────
  if (isContextValid()) {
    chrome.runtime.onMessage.addListener((msg: { type: string }) => {
      if (msg.type === "CONTEXT_MENU_DEBUG") onDebugClick();
    });
  }

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

function handleMouseUp(): void {
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
  const TH = 42, TW = 160, M = 8;
  let top = rect.top - TH - M;
  if (top < M) top = rect.bottom + M;
  let left = rect.left + rect.width / 2 - TW / 2;
  left = Math.max(M, Math.min(left, window.innerWidth - TW - M));
  toolbarEl.style.top = `${top}px`;
  toolbarEl.style.left = `${left}px`;
  toolbarEl.classList.add("visible");
}

function hideToolbar(): void {
  toolbarEl?.classList.remove("visible");
}

// ── debug click ───────────────────────────────────────────────────────────────

import { orchestrateDebug } from "./orchestrate";
import { getResultCard } from "./result_card";

function onDebugClick(): void {
  if (!isContextValid()) {
    document.getElementById("codequest-toolbar-host")?.remove();
    return;
  }

  const selectedText = window.getSelection()?.toString().trim() || lastSelectedText;
  const card = getResultCard();

  card.showLoading("Capturing problem + analyzing code…");
  hideToolbar();

  orchestrateDebug(selectedText || undefined)
    .then((outcome) => {
      if (outcome.ok) {
        const lang = outcome.data.problem.lang_selected;
        card.showResults(outcome.data.analysis, outcome.data.problem.slug, lang);
      } else {
        card.showError(outcome.error.message, outcome.error.detail);
      }
    })
    .catch((err: unknown) => {
      card.showError("Unexpected error", String(err));
    });
}

function showStatus(text: string): void {
  const el = shadowRoot?.getElementById("cq-status");
  if (!el) return;
  el.textContent = text;
  setTimeout(() => { el.textContent = ""; }, 4000);
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
