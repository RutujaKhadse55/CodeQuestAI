// ─── Service Worker (background) ─────────────────────────────────────────────
// Handles ALL network requests on behalf of content scripts.
// Content scripts send messages; SW does fetch and replies.

import { checkHealth, captureProblem, analyzeProblem, getSettings } from "../api/client";
import type { LCProblem } from "../api/types";
import type { AnalyzeRequest } from "../api/client";

// ── message types ─────────────────────────────────────────────────────────────

type SWMessage =
  | { type: "HEALTH_CHECK" }
  | { type: "CAPTURE_PROBLEM"; problem: LCProblem }
  | { type: "ANALYZE"; req: AnalyzeRequest };

// ── listener ──────────────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener(
  (message: SWMessage, _sender, sendResponse) => {
    // Must return true for async response
    handleMessage(message).then(sendResponse).catch((err) => {
      console.error("[CQ SW] error:", err);
      sendResponse({ error: String(err) });
    });
    return true;
  }
);

async function handleMessage(msg: SWMessage): Promise<unknown> {
  switch (msg.type) {
    case "HEALTH_CHECK": {
      const result = await checkHealth();
      return result;
    }
    case "CAPTURE_PROBLEM": {
      const result = await captureProblem(msg.problem);
      return result;
    }
    case "ANALYZE": {
      const result = await analyzeProblem(msg.req);
      return result;
    }
    default:
      return { error: "Unknown message type" };
  }
}

// ── startup health ping ───────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(async () => {
  console.log("[CQ SW] CodeQuest AI installed / updated.");
  try {
    const health = await checkHealth();
    console.log("[CQ SW] Backend health:", health);
  } catch (err) {
    console.warn("[CQ SW] Backend not reachable on install:", err);
  }
});

// ── context menu ──────────────────────────────────────────────────────────────

chrome.contextMenus.create({
  id: "cq-debug",
  title: "CodeQuest: Debug selected code",
  contexts: ["selection"],
  documentUrlPatterns: ["https://leetcode.com/problems/*"],
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "cq-debug" && tab?.id) {
    chrome.tabs.sendMessage(tab.id, { type: "CONTEXT_MENU_DEBUG" });
  }
});
