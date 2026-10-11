// ─── Typed API Client ─────────────────────────────────────────────────────────
// All network calls go through the Service Worker (see service_worker.ts).
// This module is used directly by the SW — never by content scripts.

import type {
  AnalyzeRequest,
  AnalyzeResponse,
  CaptureResponse,
  HealthResponse,
  HintResult,
  LCProblem,
} from "./types";

// ── config ────────────────────────────────────────────────────────────────────

interface StorageItems {
  backendUrl: string;
  backendToken: string;
}

async function getConfig(): Promise<StorageItems> {
  return new Promise((resolve) => {
    chrome.storage.sync.get(
      { backendUrl: "http://localhost:8000", backendToken: "dev" },
      (items) => resolve(items as StorageItems)
    );
  });
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
  return apiFetch<AnalyzeResponse>("/analyze", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/** POST /hint — get the next hint for the current attempt */
export async function getHint(
  problemSlug: string,
  attemptId: number,
  level: number
): Promise<HintResult> {
  return apiFetch<HintResult>("/hint", {
    method: "POST",
    body: JSON.stringify({ problem_slug: problemSlug, attempt_id: attemptId, level }),
  });
}

/** GET /dashboard/{user_id} — mastery, mistakes, recent diagnoses */
export async function getDashboard(userId = "local-user"): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/dashboard/${userId}`);
}

/** POST /explain — LLM plain-language explanation for a given attempt */
export async function getExplanation(
  attemptId: number,
  lang = "en"
): Promise<{ text: string }> {
  return apiFetch<{ text: string }>("/explain", {
    method: "POST",
    body: JSON.stringify({ attempt_id: attemptId, lang }),
  });
}

export type { AnalyzeRequest };
