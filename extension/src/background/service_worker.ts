// ─── Service Worker (background) ─────────────────────────────────────────────
// Handles ALL network requests on behalf of content scripts.
// Also executes scripts in the page's MAIN world (to access window.monaco).

import { checkHealth, captureProblem, analyzeProblem } from "../api/client";
import type { LCProblem } from "../api/types";
import type { AnalyzeRequest } from "../api/client";

// ── message types ─────────────────────────────────────────────────────────────

type SWMessage =
  | { type: "HEALTH_CHECK" }
  | { type: "CAPTURE_PROBLEM"; problem: LCProblem }
  | { type: "ANALYZE"; req: AnalyzeRequest }
  | { type: "GET_MONACO_SELECTION" };

// ── message listener ──────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener(
  (message: SWMessage, sender, sendResponse) => {
    handleMessage(message, sender)
      .then(sendResponse)
      .catch((err: unknown) => sendResponse({ error: String(err) }));
    return true;
  }
);

async function handleMessage(
  msg: SWMessage,
  sender: chrome.runtime.MessageSender
): Promise<unknown> {
  switch (msg.type) {
    case "HEALTH_CHECK":
      return checkHealth();

    case "CAPTURE_PROBLEM":
      return captureProblem(msg.problem);

    case "ANALYZE":
      return analyzeProblem(msg.req);

    // ── Read Monaco selection from the PAGE's main world ──────────────────
    // Content scripts are isolated — window.monaco is undefined there.
    // executeScript with world:"MAIN" runs in the page context and can
    // access LeetCode's Monaco instance directly.
    case "GET_MONACO_SELECTION": {
      const tabId = sender.tab?.id;
      if (!tabId) return null;
      try {
        const results = await chrome.scripting.executeScript({
          target: { tabId },
          world: "MAIN",
          func: getMonacoSelectionInPageWorld,
        });
        return results?.[0]?.result ?? null;
      } catch {
        return null;
      }
    }

    default:
      return { error: "Unknown message type" };
  }
}

/**
 * This function runs in the PAGE's main world (not the extension's isolated world).
 * It can access window.monaco directly.
 * Must be a plain function — no imports, no closures over extension variables.
 */
function getMonacoSelectionInPageWorld(): {
  text: string;
  top: number;
  bottom: number;
  left: number;
  right: number;
} | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any;
    const editors: any[] = w.monaco?.editor?.getEditors?.() ?? [];

    for (const editor of editors) {
      const sel = editor.getSelection?.();
      const model = editor.getModel?.();
      if (!sel || !model) continue;

      const text: string = (model.getValueInRange(sel) ?? "").trim();
      if (!text) continue;

      // Try to find the tightest rect for toolbar positioning
      const node: HTMLElement | null = editor.getDomNode?.() ?? null;
      let top = 100, bottom = 140, left = 400, right = 600;

      if (node) {
        // Prefer the selection highlight element
        const highlight = node.querySelector(".selected-text, .selectionHighlight");
        const cursor = node.querySelector(".cursors-layer .cursor");
        const target = highlight || cursor || node;
        const r = (target as HTMLElement).getBoundingClientRect();
        top = r.top; bottom = r.bottom; left = r.left; right = r.right;
      }

      return { text, top, bottom, left, right };
    }
  } catch (_) { /* Monaco not available */ }
  return null;
}

// ── install / update ──────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  console.info("[CQ SW] Installed / updated.");

  checkHealth()
    .then((h) => console.info("[CQ SW] Backend reachable:", h))
    .catch(() => console.info("[CQ SW] Backend not reachable yet."));

  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "cq-debug",
      title: "CodeQuest: Debug selected code",
      contexts: ["selection"],
      documentUrlPatterns: ["https://leetcode.com/problems/*"],
    });
  });
});

// ── context menu click ────────────────────────────────────────────────────────

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "cq-debug" && tab?.id) {
    chrome.tabs.sendMessage(tab.id, { type: "CONTEXT_MENU_DEBUG" });
  }
});
