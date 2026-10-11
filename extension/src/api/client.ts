// ─── Typed API Client ─────────────────────────────────────────────────────────
// All network calls go through the Service Worker (see service_worker.ts).
// This module is used directly by the SW — never by content scripts.

import type {
  AnalyzeRequest,
  AnalyzeResponse,
  CaptureResponse,
  ChatSendResponse,
  ChatStreamEvent,
  ConsentInfo,
  ConsentStatus,
  HealthResponse,
  HintResult,
  LCProblem,
} from "./types";

// ── config ────────────────────────────────────────────────────────────────────

interface StorageItems {
  backendUrl: string;
  backendToken: string;
  langPref: string;
}

async function getConfig(): Promise<StorageItems> {
  return new Promise((resolve) => {
    // The options page saves the API token under `token`; older code read `backendToken`. Accept both.
    chrome.storage.sync.get(
      { backendUrl: "http://localhost:8000", backendToken: "change-me", token: "", langPref: "en" },
      (items) => resolve({
        backendUrl: items.backendUrl,
        backendToken: (items.token as string) || (items.backendToken as string),
        langPref: items.langPref as string,
      })
    );
  });
}

// ── learner identity (per-learner token issued by POST /users) ───────────────

export interface Learner { userId: string; userToken: string }

async function storedLearner(): Promise<Learner | null> {
  const r = await chrome.storage.local.get(["cqUserId", "cqUserToken"]);
  return r.cqUserId && r.cqUserToken ? { userId: r.cqUserId as string, userToken: r.cqUserToken as string } : null;
}

/** The learner this browser acts as. Created once via POST /users; the token is kept in chrome.storage.local. */
export async function ensureLearner(forceNew = false): Promise<Learner> {
  if (!forceNew) {
    const have = await storedLearner();
    if (have) return have;
  }
  const r = await apiFetch<{ user_id: string; user_token?: string }>("/users", { method: "POST" });
  const learner = { userId: r.user_id, userToken: r.user_token ?? "" };
  await chrome.storage.local.set({ cqUserId: learner.userId, cqUserToken: learner.userToken });
  await chrome.storage.local.remove(Object.keys(await chrome.storage.local.get(null)).filter((k) => k.startsWith("cqThread:")));
  return learner;
}

/** apiFetch as the authenticated learner (X-User-Token). Re-registers once if the backend no longer knows the token. */
async function learnerFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  let learner = await ensureLearner();
  for (let attempt = 0; ; attempt++) {
    try {
      return await apiFetch<T>(path, {
        ...options,
        headers: { ...(options.headers as Record<string, string> ?? {}), "X-User-Token": learner.userToken },
      });
    } catch (err) {
      if (attempt === 0 && /^401\b/.test(String((err as Error).message))) {
        learner = await ensureLearner(true); // backend DB was reset or token lost
        continue;
      }
      throw err;
    }
  }
}

// ── fetch helper ──────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const { backendUrl, backendToken } = await getConfig();
  const url = `${backendUrl.replace(/\/$/, "")}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> ?? {}),
  };
  if (backendToken) {
    // Backend accepts either header — send both for compatibility
    headers["X-API-Token"] = backendToken;
    headers["Authorization"] = `Bearer ${backendToken}`;
  }

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ── endpoints ─────────────────────────────────────────────────────────────────

/** GET /health */
export async function checkHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

/** POST /problems/capture — idempotent, registers the problem with the backend */
export async function captureProblem(problem: LCProblem): Promise<CaptureResponse> {
  return apiFetch<CaptureResponse>("/problems/capture", {
    method: "POST",
    body: JSON.stringify(problem),
  });
}

/** POST /analyze — run tests, fuzz, diagnose */
export async function analyzeProblem(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  // Attempts are stored under the SAME learner the chat uses, so chat can see "my latest attempt".
  const learner = await ensureLearner();
  return apiFetch<AnalyzeResponse>("/analyze", {
    method: "POST",
    body: JSON.stringify({ ...req, user_id: learner.userId }),
  });
}

/** POST /hint — get the next hint for the current attempt */
export async function getHint(
  problemSlug: string,
  attemptId: number,
  level: number
): Promise<HintResult> {
  return learnerFetch<HintResult>("/hint", {
    method: "POST",
    body: JSON.stringify({ problem_slug: problemSlug, attempt_id: attemptId, level }),
  });
}

/** GET /dashboard/{user_id} — mastery, mistakes, recent diagnoses */
export async function getDashboard(userId?: string): Promise<Record<string, unknown>> {
  const id = userId ?? (await ensureLearner()).userId;
  return apiFetch<Record<string, unknown>>(`/dashboard/${id}`);
}

/** POST /explain — LLM plain-language explanation for a given attempt */
export async function getExplanation(
  attemptId: number,
  lang = "en"
): Promise<{ text: string }> {
  return learnerFetch<{ text: string }>("/explain", {
    method: "POST",
    body: JSON.stringify({ attempt_id: attemptId, lang }),
  });
}

// ── chat + profile consent (backend FEATURE_CHAT) ────────────────────────────

/** Text of the permission dialog shown when the chat opens. */
export function chatConsentInfo(): Promise<ConsentInfo> {
  return apiFetch<ConsentInfo>("/chat/consent-info");
}

export function chatConsentStatus(): Promise<ConsentStatus> {
  return learnerFetch<ConsentStatus>("/chat/consent");
}

/** The learner allows access: backend records consent and fetches + indexes their PUBLIC LeetCode profile. */
export function chatGrantConsent(leetcodeUsername: string): Promise<ConsentStatus> {
  return learnerFetch<ConsentStatus>("/chat/consent", {
    method: "POST",
    body: JSON.stringify({ leetcode_username: leetcodeUsername }),
  });
}

/** Withdraw permission: backend deletes the stored profile and its index. */
export function chatRevokeConsent(): Promise<ConsentStatus> {
  return learnerFetch<ConsentStatus>("/chat/consent", { method: "DELETE" });
}

async function threadFor(slug: string, fresh = false): Promise<string> {
  const key = `cqThread:${slug}`;
  if (!fresh) {
    const cached = (await chrome.storage.local.get(key))[key] as string | undefined;
    if (cached) return cached;
  }
  const { langPref } = await getConfig();
  const t = await learnerFetch<{ thread_id: string }>("/chat/threads", {
    method: "POST",
    body: JSON.stringify({ problem_slug: slug, language: langPref }),
  });
  await chrome.storage.local.set({ [key]: t.thread_id });
  return t.thread_id;
}

/** Send one chat message about the problem `slug` (one thread per problem, created on demand). */
export interface ChatExtras { code?: string; codeLanguage?: string }

export async function chatSend(slug: string, content: string, extras: ChatExtras = {}): Promise<ChatSendResponse> {
  const post = async (fresh: boolean) => {
    const id = await threadFor(slug, fresh);
    return learnerFetch<ChatSendResponse>(`/chat/threads/${id}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, code: extras.code, code_language: extras.codeLanguage }),
    });
  };
  try {
    return await post(false);
  } catch (err) {
    if (/^403\b/.test(String((err as Error).message))) return post(true); // thread gone (e.g. backend DB reset)
    throw err;
  }
}

/**
 * Streamed chat: relays the backend's SSE events (meta, token*, done) to `onEvent`. The backend only streams text
 * that already passed the Guard. Thread creation, learner re-registration and the 403/401 retries mirror chatSend.
 */
export async function chatSendStream(
  slug: string,
  content: string,
  onEvent: (e: ChatStreamEvent) => void,
  extras: ChatExtras = {},
): Promise<void> {
  const open = async (fresh: boolean): Promise<Response> => {
    const learner = await ensureLearner();
    const { backendUrl, backendToken } = await getConfig();
    const id = await threadFor(slug, fresh);
    return fetch(`${backendUrl.replace(/\/$/, "")}/chat/threads/${id}/messages?stream=true`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        "X-API-Token": backendToken,
        Authorization: `Bearer ${backendToken}`,
        "X-User-Token": learner.userToken,
      },
      body: JSON.stringify({ content, code: extras.code, code_language: extras.codeLanguage }),
    });
  };
  let res = await open(false);
  if (res.status === 403) res = await open(true); // thread gone
  if (res.status === 401) { await ensureLearner(true); res = await open(true); } // token unknown to the backend
  if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}: ${await res.text().catch(() => "")}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let cut: number;
    while ((cut = buf.indexOf("\n\n")) >= 0) {
      const block = buf.slice(0, cut);
      buf = buf.slice(cut + 2);
      const ev = /^event: (\w+)/.exec(block)?.[1];
      const raw = block.split("\ndata: ")[1];
      if (!ev || raw === undefined) continue;
      try { onEvent({ event: ev, data: JSON.parse(raw) } as ChatStreamEvent); } catch { /* malformed block: skip */ }
    }
  }
}

export type { AnalyzeRequest };
