// ─── Service Worker (background) ─────────────────────────────────────────────
// Handles ALL network requests on behalf of content scripts.
// Content scripts send messages; SW does fetch and replies.

import { checkHealth, captureProblem, analyzeProblem } from "../api/client";
import type { LCProblem } from "../api/types";
import type { AnalyzeRequest } from "../api/client";

// ── message types ─────────────────────────────────────────────────────────────

type SWMessage =
  | { type: "HEALTH_CHECK" }
  | { type: "CAPTURE_PROBLEM"; problem: LCProblem }
  | { type: "ANALYZE"; req: AnalyzeRequest };

// ── message listener ──────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener(
  (message: SWMessage, _sender, sendResponse) => {
    handleMessage(message)
      .then(sendResponse)
      .catch((err: unknown) => {
        // Return error to caller — never let it become an unhandled rejection
        sendResponse({ error: String(err) });
      });
    return true; // keep channel open for async response
  }
);

async function handleMessage(msg: SWMessage): Promise<unknown> {
  switch (msg.type) {
    case "HEALTH_CHECK":
      return checkHealth();
    case "CAPTURE_PROBLEM":
      return captureProblem(msg.problem);
    case "ANALYZE":
      return analyzeProblem(msg.req);
    default:
      return { error: "Unknown message type" };
  }
}

// ── install / update ──────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  console.info("[CQ SW] Installed / updated.");

  // Soft health ping — failure is expected when backend isn't running yet
  // Do NOT await; do NOT let it surface as an uncaught rejection
  checkHealth()
    .then((h) => console.info("[CQ SW] Backend reachable:", h))
    .catch(() => console.info("[CQ SW] Backend not reachable yet — start it when ready."));

  // Register context menu (remove first to avoid duplicate errors on reload)
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
