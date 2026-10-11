// ─── Service Worker (background) ─────────────────────────────────────────────
// Routes ALL network calls. Content scripts send messages; SW does fetch.
// Also manages the offscreen document for audio playback (MV3 requirement).
// Also executes scripts in the page MAIN world (for Monaco/LeetCode access).

import {
  checkHealth, captureProblem, analyzeProblem, getHint, getDashboard, getExplanation,
  chatConsentInfo, chatConsentStatus, chatGrantConsent, chatRevokeConsent, chatSend, chatSendStream, crewCall, ttsSpeak, explainProblem, getContext,
} from "../api/client";
import type { LCProblem, AnalyzeRequest } from "../api/types";

// ── message types ─────────────────────────────────────────────────────────────

type SWMessage =
  | { type: "HEALTH_CHECK" }
  | { type: "CAPTURE_PROBLEM"; problem: LCProblem }
  | { type: "ANALYZE"; req: AnalyzeRequest }
  | { type: "GET_HINT"; slug: string; attemptId: number; level: number }
  | { type: "GET_DASHBOARD" }
  | { type: "GET_EXPLANATION"; attemptId: number; lang?: string }
  | { type: "CHAT_CONSENT_INFO" }
  | { type: "CHAT_STATUS" }
  | { type: "CHAT_GRANT"; username: string }
  | { type: "CHAT_REVOKE" }
  | { type: "GET_CONTEXT" }
  | { type: "EXPLAIN_PROBLEM"; body: Record<string, unknown> }
  | { type: "CREW"; agent: "explain" | "tests" | "debug" | "trace"; body: Record<string, unknown> }
  | { type: "CHAT_SEND"; slug: string; text: string; code?: string; codeLanguage?: string }
  | { type: "GET_MONACO_SELECTION" }
  | { type: "GET_FULL_CODE" }
  | { type: "PLAY_TTS"; text: string; lang?: string }
  | { type: "STOP_TTS" };

// ── streamed chat: content script opens a Port, the SW relays the backend SSE events ──────────────────────

chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "cq-chat") return;
  let open = true;
  port.onDisconnect.addListener(() => { open = false; });
  port.onMessage.addListener(async (m: { slug: string; text: string; code?: string; codeLanguage?: string }) => {
    const send = (e: unknown) => { if (open) { try { port.postMessage(e); } catch { open = false; } } };
    try {
      await chatSendStream(m.slug, m.text, send, { code: m.code, codeLanguage: m.codeLanguage });
    } catch (err) {
      send({ event: "error", data: { message: String(err) } });
    }
    send({ event: "end" });
  });
});

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
  const tabId = sender.tab?.id;

  switch (msg.type) {

    case "HEALTH_CHECK":
      return checkHealth();

    case "CAPTURE_PROBLEM":
      return captureProblem(msg.problem);

    case "ANALYZE":
      return analyzeProblem(msg.req);

    case "GET_HINT":
      return getHint(msg.slug, msg.attemptId, msg.level);

    case "GET_DASHBOARD":
      return getDashboard();

    case "GET_EXPLANATION":
      return getExplanation(msg.attemptId, msg.lang);

    // ── problem chat + profile consent ───────────────────────────────────────
    case "CHAT_CONSENT_INFO":
      return chatConsentInfo();
    case "CHAT_STATUS":
      return chatConsentStatus();
    case "CHAT_GRANT":
      return chatGrantConsent(msg.username);
    case "CHAT_REVOKE":
      return chatRevokeConsent();
    // ── AI crew: explain / generated tests / debug / trace ───────────────────
    case "GET_CONTEXT":
      return getContext();
    case "EXPLAIN_PROBLEM":
      return explainProblem(msg.body);
    case "CREW":
      return crewCall(msg.agent, msg.body);
    case "CHAT_SEND":
      return chatSend(msg.slug, msg.text, { code: msg.code, codeLanguage: msg.codeLanguage });

    // ── Monaco: read selected text ───────────────────────────────────────────
    case "GET_MONACO_SELECTION": {
      if (!tabId) return null;
      try {
        const results = await chrome.scripting.executeScript({
          target: { tabId }, world: "MAIN",
          func: getMonacoSelectionInPageWorld,
        });
        return results?.[0]?.result ?? null;
      } catch { return null; }
    }

    // ── Monaco: read full editor code ────────────────────────────────────────
    case "GET_FULL_CODE": {
      if (!tabId) return null;
      try {
        const results = await chrome.scripting.executeScript({
          target: { tabId }, world: "MAIN",
          func: getFullCodeInPageWorld,
        });
        return results?.[0]?.result ?? null;
      } catch { return null; }
    }

    // ── Audio: play TTS via offscreen document ───────────────────────────────
    case "PLAY_TTS": {
      await ensureOffscreenDocument();
      let audioBase64: string | undefined;
      try {
        const r = await ttsSpeak(msg.text, msg.lang ?? "en");
        audioBase64 = r.audio_base64 || undefined; // undefined => offscreen uses browser speech
      } catch { /* backend offline: browser speech */ }
      await chrome.runtime.sendMessage({ type: "PLAY_TTS", text: msg.text, lang: msg.lang, audioBase64 });
      return { ok: true };
    }

    case "STOP_TTS": {
      try {
        await chrome.runtime.sendMessage({ type: "STOP_TTS" });
      } catch { /* offscreen may not exist */ }
      return { ok: true };
    }

    default:
      return { error: "Unknown message type" };
  }
}

// ── Offscreen document management ────────────────────────────────────────────

const OFFSCREEN_URL = "src/offscreen/offscreen.html";

async function ensureOffscreenDocument(): Promise<void> {
  const existing = await chrome.offscreen.hasDocument();
  if (!existing) {
    await chrome.offscreen.createDocument({
      url: OFFSCREEN_URL,
      reasons: [chrome.offscreen.Reason.AUDIO_PLAYBACK],
      justification: "Play TTS audio for CodeQuest AI feedback",
    });
  }
}

// ── Page-world functions (run via executeScript, no imports allowed) ──────────

function getMonacoSelectionInPageWorld(): {
  text: string; top: number; bottom: number; left: number; right: number;
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
      const node: HTMLElement | null = editor.getDomNode?.() ?? null;
      let top = 100, bottom = 140, left = 400, right = 600;
      if (node) {
        const highlight = node.querySelector(".selected-text, .selectionHighlight");
        const cursor = node.querySelector(".cursors-layer .cursor");
        const r = ((highlight || cursor || node) as HTMLElement).getBoundingClientRect();
        top = r.top; bottom = r.bottom; left = r.left; right = r.right;
      }
      return { text, top, bottom, left, right };
    }
  } catch { /* Monaco not available */ }
  return null;
}

function getFullCodeInPageWorld(): { code: string; language: string } | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any;
    const editors: any[] = w.monaco?.editor?.getEditors?.() ?? [];
    for (const editor of editors) {
      const model = editor.getModel?.();
      if (!model) continue;
      const code: string = model.getValue?.() ?? "";
      if (!code.trim()) continue;
      const lang: string = model.getLanguageId?.() ?? "python3";
      return { code, language: lang };
    }
    // DOM fallback
    const lines = document.querySelectorAll(".view-lines .view-line");
    if (lines.length > 0) {
      const code = Array.from(lines).map(l => (l as HTMLElement).innerText ?? "").join("\n");
      return { code, language: "unknown" };
    }
  } catch { /* ignore */ }
  return null;
}

// ── install / update ──────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  console.info("[CQ SW] Installed / updated.");
  checkHealth()
    .then((h) => console.info("[CQ SW] Backend:", h))
    .catch(() => console.info("[CQ SW] Backend not reachable."));

  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "cq-debug",
      title: "🔍 CodeQuest: Analyze selected code",
      contexts: ["selection"],
      documentUrlPatterns: ["https://leetcode.com/problems/*"],
    });
    chrome.contextMenus.create({
      id: "cq-debug-all",
      title: "🔍 CodeQuest: Analyze my full solution",
      contexts: ["page"],
      documentUrlPatterns: ["https://leetcode.com/problems/*"],
    });
  });
});

// ── context menu click ────────────────────────────────────────────────────────

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (!tab?.id) return;
  if (info.menuItemId === "cq-debug") {
    chrome.tabs.sendMessage(tab.id, { type: "CONTEXT_MENU_DEBUG" });
  }
  if (info.menuItemId === "cq-debug-all") {
    chrome.tabs.sendMessage(tab.id, { type: "CONTEXT_MENU_DEBUG_ALL" });
  }
});
