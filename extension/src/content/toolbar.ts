// ─── Shadow-DOM Toolbar — content script ──────────────────────────────────
// Shows a floating selection toolbar on text/code selection.
// Matches the reference screenshot: dark pill, amber border glow,
// logo + "Analyze selection" on left, icon action buttons on right.

import { disabledReason } from "./guards";
import { LOGO_DATA_URL } from "../assets/logo";

// ── Phase 2: paste + timing tracking ──────────────────────────────────────────
export let totalPasteChars = 0;
export const pageLoadTime = Date.now();

function isContextValid(): boolean {
  try { return !!chrome.runtime?.id; } catch { return false; }
}

// ── styles ────────────────────────────────────────────────────────────────────

const TOOLBAR_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:host { all: initial; font-family: 'Inter', system-ui, sans-serif; }
* { box-sizing: border-box; margin: 0; padding: 0; }

#cq-toolbar {
  position: fixed;
  display: none;
  align-items: center;
  gap: 0;
  background: #17191f;
  border: 1.5px solid #c89b3c;
  border-radius: 14px;
  padding: 0;
  box-shadow:
    0 0 0 3px rgba(200,155,60,0.12),
    0 8px 32px rgba(0,0,0,0.55),
    0 2px 8px rgba(0,0,0,0.4);
  pointer-events: all;
  font-family: 'Inter', system-ui, sans-serif;
  color: #e2e8f0;
  animation: cq-pop 0.15s cubic-bezier(0.34,1.56,0.64,1);
  z-index: 2147483647;
  overflow: hidden;
  white-space: nowrap;
  min-width: 420px;
}
#cq-toolbar.visible { display: flex; }

@keyframes cq-pop {
  from { opacity: 0; transform: translateY(6px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0)  scale(1); }
}

/* ── Left identity section ──────────────────────────────────────────────── */
.cq-tb-identity {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px 10px 12px;
  border-right: 1px solid #2a2d38;
  flex-shrink: 0;
}
.cq-tb-logo {
  width: 32px; height: 32px;
  background: #22c55e;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.cq-tb-logo img { width: 100%; height: 100%; object-fit: contain; }
.cq-tb-name  { font-size: 0.78rem; font-weight: 700; color: #f1f5f9; line-height: 1.2; }
.cq-tb-sub   { font-size: 0.65rem; color: #94a3b8; line-height: 1.2; margin-top: 1px; }

/* ── Action buttons ──────────────────────────────────────────────────────── */
.cq-tb-actions {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 6px 6px;
}
.cq-tb-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  background: none;
  border: none;
  border-radius: 9px;
  padding: 7px 11px;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.12s;
  min-width: 52px;
}
.cq-tb-btn:hover { background: #22273a; }
.cq-tb-btn:active { background: #2d3347; transform: scale(0.96); }
.cq-tb-btn-icon { font-size: 1.05rem; line-height: 1; }
.cq-tb-btn-label {
  font-size: 0.62rem; font-weight: 600; color: #94a3b8;
  line-height: 1; letter-spacing: 0.02em;
}
/* Debug button is the primary CTA — highlight it */
.cq-tb-btn.primary .cq-tb-btn-icon { font-size: 1.1rem; }
.cq-tb-btn.primary .cq-tb-btn-label { color: #e2e8f0; }

/* Divider between groups */
.cq-tb-divider {
  width: 1px; height: 28px;
  background: #2a2d38;
  flex-shrink: 0;
  margin: 0 3px;
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

  toolbarEl.innerHTML = buildToolbarHTML();

  // Attach listeners to each action button
  shadowRoot.getElementById("cq-tb-debug")?.addEventListener("mousedown", (e) => e.stopPropagation());
  shadowRoot.getElementById("cq-tb-debug")?.addEventListener("click", () => onActionClick("debug"));
  shadowRoot.getElementById("cq-tb-explain")?.addEventListener("click", () => onActionClick("explain"));
  shadowRoot.getElementById("cq-tb-hint")?.addEventListener("click", () => onActionClick("hint"));
  shadowRoot.getElementById("cq-tb-concept")?.addEventListener("click", () => onActionClick("concept"));
  shadowRoot.getElementById("cq-tb-listen")?.addEventListener("click", () => onActionClick("listen"));
  shadowRoot.getElementById("cq-tb-chat")?.addEventListener("click", () => onActionClick("chat"));

  // ── 1. Native selection
  document.addEventListener("mouseup", handleMouseUp);

  // ── 2. Monaco editor selection
  watchForMonacoEditor();

  // ── 3. Hide on outside click
  document.addEventListener("mousedown", (e) => {
    if (!e.composedPath().includes(hostEl!)) hideToolbar();
  });

  // ── 4. Paste detection (Phase 2)
  document.addEventListener("paste", (e) => {
    const pasted = e.clipboardData?.getData("text") ?? "";
    totalPasteChars += pasted.length;
  }, true);

  // ── 5. Context menu messages from SW
  chrome.runtime.onMessage.addListener((msg: { type: string }) => {
    if (msg.type === "CONTEXT_MENU_DEBUG" || msg.type === "CONTEXT_MENU_DEBUG_ALL") {
      onActionClick("debug");
    }
  });

  console.info("[CQ] Toolbar ready.");
}

function buildToolbarHTML(): string {
  const actions = [
    { id: "cq-tb-debug",   icon: "🐛",  label: "Debug",   primary: true },
    { id: "cq-tb-explain", icon: "📄",  label: "Explain", primary: false },
    { id: "cq-tb-hint",    icon: "💡",  label: "Hint",    primary: false },
    { id: "cq-tb-concept", icon: "🎓",  label: "Concept", primary: false },
    { id: "cq-tb-listen",  icon: "🔊",  label: "Listen",  primary: false },
    { id: "cq-tb-chat",    icon: "💬",  label: "Chat",    primary: false },
  ];

  const btnHtml = actions.map((a) =>
    `<button class="cq-tb-btn${a.primary ? " primary" : ""}" id="${a.id}" title="${a.label}">
       <span class="cq-tb-btn-icon">${a.icon}</span>
       <span class="cq-tb-btn-label">${a.label}</span>
     </button>`
  ).join("");

  return `
    <div class="cq-tb-identity">
      <div class="cq-tb-logo">
        <img src="${LOGO_DATA_URL}" alt="CQ" />
      </div>
      <div>
        <div class="cq-tb-name">CodeQuest AI</div>
        <div class="cq-tb-sub">Analyze selection</div>
      </div>
    </div>
    <div class="cq-tb-actions">
      ${btnHtml}
    </div>`;
}

// ── Monaco editor watcher ─────────────────────────────────────────────────────

function watchForMonacoEditor(): void {
  const attach = (el: HTMLElement) => {
    if ((el as HTMLElement & { _cqDone?: boolean })._cqDone) return;
    (el as HTMLElement & { _cqDone?: boolean })._cqDone = true;
    el.addEventListener("mouseup", () => {
      setTimeout(askSwForMonacoSelection, 100);
    });
  };
  const scan = () =>
    document.querySelectorAll<HTMLElement>(".monaco-editor").forEach(attach);
  scan();
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
      const rect = new DOMRect(
        result.left, result.top,
        result.right - result.left,
        result.bottom - result.top
      );
      showToolbarAt(rect);
    }
  } catch { /* SW not available */ }
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
  }, 30);
}

// ── positioning ───────────────────────────────────────────────────────────────

function showToolbarAt(rect: DOMRect): void {
  if (!toolbarEl) return;
  const TH = 56, TW = 440, M = 10;
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

// ── action click handler ──────────────────────────────────────────────────────

import { orchestrateDebug } from "./orchestrate";
import { getResultCard } from "./result_card";

function onActionClick(action: string): void {
  if (!isContextValid()) {
    document.getElementById("codequest-toolbar-host")?.remove();
    return;
  }

  const selectedText = window.getSelection()?.toString().trim() || lastSelectedText;
  const card = getResultCard();
  hideToolbar();

  if (action === "chat") {
    // Open panel on Chat tab
    card.showResults(
      { results: [], flags: [], verified: null, attempt_id: 0 } as never,
      window.location.pathname.split("/problems/")[1]?.split("/")[0] ?? "problem"
    );
    return;
  }

  if (action === "listen") {
    const text = selectedText || document.title;
    chrome.runtime.sendMessage({ type: "PLAY_TTS", text, lang: "en" }).catch(() => {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text); u.rate = 0.92; speechSynthesis.speak(u);
    });
    return;
  }

  // Debug / Explain / Hint / Concept all trigger analysis + open the panel
  card.showLoading(
    action === "hint"    ? "Fetching hint…" :
    action === "explain" ? "Generating explanation…" :
    action === "concept" ? "Analyzing concept…" :
    "Capturing problem + analyzing code…"
  );

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
