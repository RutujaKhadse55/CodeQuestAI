// ─── Shadow-DOM Toolbar — content script ──────────────────────────────────
// Injected into every https://leetcode.com/problems/* page.
// Shows a floating Debug button when the user selects ANY text on the page.
// Uses Shadow DOM to isolate styles from LeetCode's CSS.

import { disabledReason } from "./guards";

/** Returns false when the extension has been reloaded and this old
 *  content script's context is no longer valid. All chrome.runtime
 *  calls must be guarded by this check. */
function isContextValid(): boolean {
  try {
    return !!chrome.runtime?.id;
  } catch {
    return false;
  }
}

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

  // ── Also watch Monaco editor (loads lazily) ───────────────────────
  watchMonacoEditor();

  // ── Context menu from SW ──────────────────────────────────────────────────
  if (isContextValid()) {
    chrome.runtime.onMessage.addListener((msg: { type: string }) => {
      if (msg.type === "CONTEXT_MENU_DEBUG") onDebugClick();
    });
  }

  console.info("[CQ] Toolbar ready — select any text to debug.");
}

// ── Monaco editor support ─────────────────────────────────────────────────────
// Monaco uses its own virtual DOM — window.getSelection() returns empty there.
// We read the selection via the Monaco global API and attach mouseup directly
// to the editor container so we don't miss events that don't bubble.

interface MonacoSelection { startLineNumber: number; endLineNumber: number; startColumn: number; endColumn: number; }
interface MonacoModel { getValueInRange(sel: MonacoSelection): string; }
interface MonacoEditor { getSelection(): MonacoSelection | null; getModel(): MonacoModel | null; getDomNode(): HTMLElement | null; }
interface MonacoGlobal { editor?: { getEditors?(): MonacoEditor[] } }

let lastMonacoRect: DOMRect | null = null;

/** Read selected text from Monaco if window.getSelection() is empty */
function getMonacoSelectedText(): string {
  try {
    const w = window as unknown as { monaco?: MonacoGlobal };
    const editors = w.monaco?.editor?.getEditors?.() ?? [];
    for (const editor of editors) {
      const sel = editor.getSelection?.();
      const model = editor.getModel?.();
      if (sel && model) {
        const text = model.getValueInRange(sel).trim();
        if (text) return text;
      }
    }
  } catch { /* Monaco not available */ }
  return "";
}

/** Get rect of the Monaco editor cursor/selection for toolbar positioning */
function getMonacoSelectionRect(editorEl: HTMLElement): DOMRect | null {
  const cursor = editorEl.querySelector(".cursor") as HTMLElement | null;
  if (cursor) return cursor.getBoundingClientRect();
  const viewLine = editorEl.querySelector(".selected-text") as HTMLElement | null;
  if (viewLine) return viewLine.getBoundingClientRect();
  return editorEl.getBoundingClientRect();
}

/** Attach mouseup to Monaco editor container (may not bubble to document) */
function attachMonacoListener(editorEl: HTMLElement): void {
  editorEl.addEventListener("mouseup", () => {
    // Delay so Monaco finalises its internal selection
    setTimeout(() => {
      const text = getMonacoSelectedText();
      if (text.length < 2) { hideToolbar(); return; }
      const rect = getMonacoSelectionRect(editorEl);
      lastMonacoRect = rect;
      if (rect) showToolbarAt(rect);
    }, 60);
  });
  console.info("[CQ] Attached to Monaco editor.");
}

/** Watch for Monaco editor appearing in the DOM (it loads lazily) */
function watchMonacoEditor(): void {
  const tryAttach = () => {
    const editors = document.querySelectorAll(".monaco-editor");
    editors.forEach((el) => {
      if (!(el as HTMLElement).dataset.cqAttached) {
        (el as HTMLElement).dataset.cqAttached = "1";
        attachMonacoListener(el as HTMLElement);
      }
    });
  };

  tryAttach(); // immediate attempt

  // Also observe DOM for Monaco appearing later
  const obs = new MutationObserver(tryAttach);
  obs.observe(document.body, { childList: true, subtree: true });
}

// ── selection handling (native + Monaco) ──────────────────────────────────────

function handleMouseUp(): void {
  // Small delay so the selection is finalised
  setTimeout(() => {
    // 1. Try native browser selection (description, constraints, examples)
    const sel = window.getSelection();
    const nativeText = sel?.toString().trim() ?? "";

    if (nativeText.length >= 2 && sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      if (rect.width > 0 || rect.height > 0) {
        showToolbarAt(rect);
        return;
      }
    }

    // 2. Try Monaco editor selection (code panel)
    const monacoText = getMonacoSelectedText();
    if (monacoText.length >= 2) {
      // Monaco fires its own mouseup listener; we just ensure we're covered
      // if the event does bubble up to document.
      const monacoEl = document.querySelector(".monaco-editor") as HTMLElement | null;
      const rect = monacoEl ? getMonacoSelectionRect(monacoEl) : lastMonacoRect;
      if (rect) showToolbarAt(rect);
      return;
    }

    hideToolbar();
  }, 30);
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
  if (!isContextValid()) {
    // Extension was reloaded — remove the stale toolbar
    document.getElementById("codequest-toolbar-host")?.remove();
    return;
  }

  // Try native selection first, then Monaco
  const selectedText =
    window.getSelection()?.toString().trim() ||
    getMonacoSelectedText();

  if (!selectedText) {
    showStatus("Select some code or text first!");
    return;
  }

  showStatus("Checking backend…");

  chrome.runtime
    .sendMessage({ type: "HEALTH_CHECK" })
    .then((res: { error?: string; version?: string } | undefined) => {
      if (res?.error) {
        showStatus("⚠️ Backend offline — start the server");
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
