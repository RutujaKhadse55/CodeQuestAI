// ─── Shadow-DOM Toolbar — content script ──────────────────────────────────
// Injected into every https://leetcode.com/problems/* page.
// Shows a floating Debug button when the user selects ANY text on the page.
// Uses Shadow DOM to isolate styles from LeetCode's CSS.

import { disabledReason } from "./guards";

// ── styles — declared FIRST to avoid TDZ errors ───────────────────────────────

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
    padding: 6px 12px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5);
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
    padding: 4px 12px;
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
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
`;

// ── refs ──────────────────────────────────────────────────────────────────────

let toolbarEl: HTMLDivElement | null = null;
let shadowRoot: ShadowRoot | null = null;

// ── toolbar setup ─────────────────────────────────────────────────────────────

function initToolbar(): void {
  // Host sits at fixed position 0,0 — the toolbar inside is `position:fixed`
  const host = document.createElement("div");
  host.id = "codequest-toolbar-host";
  host.style.cssText =
    "position:fixed;top:0;left:0;width:0;height:0;z-index:2147483647;pointer-events:none;";
  document.documentElement.appendChild(host);

  shadowRoot = host.attachShadow({ mode: "open" });

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

  const status = document.createElement("span");
  status.id = "cq-status";
  toolbarEl.appendChild(status);

  // ── Show toolbar on any text selection (mouseup is most reliable) ─────────
  document.addEventListener("mouseup", handleMouseUp);

  // ── Hide when clicking elsewhere ─────────────────────────────────────────
  document.addEventListener("mousedown", (e) => {
    // Don't hide if the click is inside our shadow toolbar
    if (!toolbarEl) return;
    const path = e.composedPath();
    if (!path.includes(host)) {
      hideToolbar();
    }
  });

  // ── Context menu from SW ──────────────────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg: { type: string }) => {
    if (msg.type === "CONTEXT_MENU_DEBUG") onDebugClick();
  });

  console.info("[CQ] Toolbar ready — select any text to debug.");
}

// ── selection handling ────────────────────────────────────────────────────────

function handleMouseUp(): void {
  // Small delay so the selection is finalised
  setTimeout(() => {
    const sel = window.getSelection();
    const text = sel?.toString().trim() ?? "";

    if (text.length < 3 || !sel || sel.rangeCount === 0) {
      hideToolbar();
      return;
    }

    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // Don't show if selection has no visible area
    if (rect.width === 0 && rect.height === 0) {
      hideToolbar();
      return;
    }

    showToolbarAt(rect);
  }, 10);
}

function showToolbarAt(rect: DOMRect): void {
  if (!toolbarEl) return;

  // Position: above the selection, horizontally centred
  const TOOLBAR_HEIGHT = 40;
  const TOOLBAR_WIDTH = 140; // approximate
  const MARGIN = 8;

  let top = rect.top - TOOLBAR_HEIGHT - MARGIN;
  // If not enough room above, show below
  if (top < MARGIN) top = rect.bottom + MARGIN;

  let left = rect.left + rect.width / 2 - TOOLBAR_WIDTH / 2;
  left = Math.max(MARGIN, Math.min(left, window.innerWidth - TOOLBAR_WIDTH - MARGIN));

  toolbarEl.style.top = `${top}px`;
  toolbarEl.style.left = `${left}px`;
  toolbarEl.classList.add("visible");
}

function hideToolbar(): void {
  toolbarEl?.classList.remove("visible");
}

// ── debug action ──────────────────────────────────────────────────────────────

function onDebugClick(): void {
  const selectedText = window.getSelection()?.toString().trim() ?? "";
  if (!selectedText) {
    showStatus("Select some code or text first!");
    return;
  }

  showStatus("Checking backend…");

  chrome.runtime
    .sendMessage({ type: "HEALTH_CHECK" })
    .then((res: { error?: string; version?: string } | undefined) => {
      if (res?.error) {
        showStatus("⚠️ Backend offline");
      } else {
        showStatus(`✅ Backend OK`);
        setTimeout(() => hideToolbar(), 1500);
      }
    })
    .catch(() => {
      showStatus("⚠️ Backend not reachable");
    });
}

function showStatus(text: string): void {
  const status = shadowRoot?.getElementById("cq-status");
  if (!status) return;
  status.textContent = text;
  setTimeout(() => { status.textContent = ""; }, 4000);
}

// ── entry point ───────────────────────────────────────────────────────────────

function main(): void {
  const reason = disabledReason();
  if (reason) {
    console.info(`[CQ] ${reason} — toolbar disabled.`);
    return;
  }
  initToolbar();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", main);
} else {
  main();
}
