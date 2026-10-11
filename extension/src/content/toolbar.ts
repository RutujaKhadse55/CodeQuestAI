// ─── Shadow-DOM Toolbar — content script ──────────────────────────────────
// Injected into every https://leetcode.com/problems/* page.
// Shows a floating Debug button on text selection; uses Shadow DOM to
// isolate styles from LeetCode's CSS.

import { disabledReason } from "./guards";

// ── styles — declared FIRST to avoid TDZ errors in Rollup output ─────────────

const TOOLBAR_CSS = `
  :host { all: initial; }
  #cq-toolbar {
    position: absolute;
    display: flex;
    align-items: center;
    gap: 8px;
    background: #1a1a2e;
    border: 1px solid #16213e;
    border-radius: 8px;
    padding: 6px 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    pointer-events: all;
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 13px;
    color: #e2e8f0;
    animation: cq-fade-in 0.15s ease;
  }
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
  }
  #cq-debug-btn:hover { opacity: 0.85; }
  #cq-status {
    font-size: 12px;
    color: #94a3b8;
    white-space: nowrap;
  }
`;

// ── toolbar setup ─────────────────────────────────────────────────────────────

function initToolbar(): void {
  // Create host element (invisible wrapper)
  const host = document.createElement("div");
  host.id = "codequest-toolbar-host";
  host.style.cssText =
    "position:absolute;z-index:2147483647;pointer-events:none;top:0;left:0;width:0;height:0;";
  document.documentElement.appendChild(host);

  // Shadow root isolates our styles
  const shadow = host.attachShadow({ mode: "open" });

  // Inject toolbar styles
  const style = document.createElement("style");
  style.textContent = TOOLBAR_CSS;
  shadow.appendChild(style);

  // Toolbar container
  const toolbar = document.createElement("div");
  toolbar.id = "cq-toolbar";
  toolbar.setAttribute("role", "toolbar");
  toolbar.setAttribute("aria-label", "CodeQuest AI");
  toolbar.style.display = "none";
  shadow.appendChild(toolbar);

  // Debug button
  const btn = document.createElement("button");
  btn.id = "cq-debug-btn";
  btn.textContent = "🔍 Debug";
  btn.title = "CodeQuest: Analyze selected code";
  btn.addEventListener("click", onDebugClick);
  toolbar.appendChild(btn);

  // Status text (shows "Analyzing…" etc.)
  const status = document.createElement("span");
  status.id = "cq-status";
  toolbar.appendChild(status);

  // Show/hide toolbar on selection change
  document.addEventListener("selectionchange", () => {
    const sel = window.getSelection();
    const text = sel?.toString().trim() ?? "";
    if (text.length > 10) {
      positionToolbar(toolbar, sel!);
      toolbar.style.display = "flex";
    } else {
      toolbar.style.display = "none";
    }
  });

  // Listen for context-menu message from service worker
  chrome.runtime.onMessage.addListener((msg: { type: string }) => {
    if (msg.type === "CONTEXT_MENU_DEBUG") {
      onDebugClick();
    }
  });

  console.info("[CQ] Toolbar initialised.");
}

// ── positioning ───────────────────────────────────────────────────────────────

function positionToolbar(toolbar: HTMLDivElement, sel: Selection): void {
  const range = sel.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  const top = rect.top + window.scrollY - 48; // above selection
  const left = Math.max(8, rect.left + window.scrollX);
  toolbar.style.cssText = `display:flex;position:absolute;top:${top}px;left:${left}px;`;
}

// ── debug action ──────────────────────────────────────────────────────────────

function onDebugClick(): void {
  const selectedCode = window.getSelection()?.toString().trim() ?? "";
  if (!selectedCode) {
    showStatus("Select your code first!");
    return;
  }

  showStatus("Analyzing…");

  // Phase 0: health check ping
  chrome.runtime
    .sendMessage({ type: "HEALTH_CHECK" })
    .then((response: { error?: string; version?: string } | undefined) => {
      if (response?.error) {
        showStatus("Backend offline — check options");
      } else {
        showStatus(`Backend ✅ v${response?.version ?? "?"}`);
      }
    })
    .catch((err: unknown) => {
      showStatus("Error: " + String(err));
    });
}

function showStatus(text: string): void {
  const host = document.getElementById("codequest-toolbar-host");
  if (!host?.shadowRoot) return;
  const status = host.shadowRoot.getElementById("cq-status");
  if (status) {
    status.textContent = text;
    setTimeout(() => { status.textContent = ""; }, 4000);
  }
}

// ── entry point — run after DOM is ready ─────────────────────────────────────

function main(): void {
  const reason = disabledReason();
  if (reason) {
    console.info(`[CQ] ${reason} — toolbar disabled.`);
    return;
  }
  initToolbar();
}

// Defer slightly so the page DOM is settled
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", main);
} else {
  main();
}
