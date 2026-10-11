// ─── Typed API client — wraps all fetch calls to the backend ───────────────
// All network requests go through the service worker (SW).
// This module is imported by the SW; content scripts use chrome.runtime.sendMessage.

import type { LCProblem, AnalyzeResponse, HealthResponse } from "./types";

// ── storage helpers ──────────────────────────────────────────────────────────

export async function getSettings(): Promise<{ backendUrl: string; token: string }> {
  return new Promise((resolve) => {
    chrome.storage.sync.get(
      { backendUrl: "http://localhost:8000", token: "" },
      (items) => resolve(items as { backendUrl: string; token: string })
    );
  });
}

// ── core fetch ───────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const { backendUrl, token } = await getSettings();
  const url = `${backendUrl}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ── endpoints ────────────────────────────────────────────────────────────────

export function checkHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export function captureProblem(problem: LCProblem): Promise<{ slug: string }> {
  return apiFetch<{ slug: string }>("/problems/capture", {
    method: "POST",
    body: JSON.stringify(problem),
  });
}

export interface AnalyzeRequest {
  slug: string;
  source: "leetcode";
  code: string;
  lang: string;
  paste_chars?: number;
  elapsed_ms?: number;
  lang_pref?: "en" | "hi" | "mr";
  run_capture?: LCProblem["run_capture"];
}

export function analyzeProblem(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  return apiFetch<AnalyzeResponse>("/analyze", {
    method: "POST",
    body: JSON.stringify(req),
  });
}
