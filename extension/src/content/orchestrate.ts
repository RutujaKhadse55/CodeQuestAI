// ─── Phase 1 Orchestrator — capture + analyze flow ───────────────────────────
// Called from the toolbar when the user clicks "🔍 Debug".
// 1. Captures problem context from DOM (Source A) + run-panel (Source C)
// 2. Gets selected / full code from Monaco (via SW bridge)
// 3. POST /problems/capture → registers problem with backend
// 4. POST /analyze → returns results, diagnosis, hints
// 5. Returns the AnalyzeResponse for the result card to render

import type { LCProblem, AnalyzeRequest, AnalyzeResponse, CaptureResponse } from "../api/types";
import { totalPasteChars, pageLoadTime } from "./toolbar";

export interface OrchestrationResult {
  capture: CaptureResponse;
  analysis: AnalyzeResponse;
  problem: LCProblem;
  code: string;
}

export interface OrchestrationError {
  kind: "capture_failed" | "unsupported" | "analyze_failed" | "no_problem";
  message: string;
  detail?: string;
}

export type OrchestrationOutcome =
  | { ok: true; data: OrchestrationResult }
  | { ok: false; error: OrchestrationError };

// ── helpers ───────────────────────────────────────────────────────────────────

function sendToSW<T>(message: object): Promise<T> {
  return chrome.runtime.sendMessage(message) as Promise<T>;
}

/** Read the entire Monaco editor code via the SW page-world bridge */
async function fetchFullCode(): Promise<{ code: string; language: string } | null> {
  try {
    return await sendToSW<{ code: string; language: string } | null>({ type: "GET_FULL_CODE" });
  } catch { return null; }
}

// ── capture DOM data (Source A) ───────────────────────────────────────────────

/** Query multiple selectors, return first non-empty text */
function selectText(selectors: string[]): string {
  for (const sel of selectors) {
    try {
      const el = document.querySelector(sel) as HTMLElement | null;
      const text = el?.innerText?.trim() || el?.textContent?.trim();
      if (text) return text;
    } catch { /* invalid selector, skip */ }
  }
  return "";
}

function getSlug(): string {
  const match = location.pathname.match(/\/problems\/([^/?#]+)/);
  return match?.[1] ?? "unknown";
}

function getTitle(): string {
  // Try data attributes and semantic elements first
  const candidates = [
    "[data-cy='question-title']",
    ".mr-2.text-lg",
    ".text-title-large",
    "[class*='title'] a",
    "h4",
    "h3",
    ".question-title",
    "[class*='questionTitle']",
  ];
  const found = selectText(candidates);
  if (found) return found;
  // Fallback: parse document.title "678. Valid Parenthesis String - LeetCode"
  return document.title.split(" - ")[0].trim();
}

function getDifficulty(): string {
  // LeetCode puts difficulty in a span near the title
  const el = document.querySelector(
    "[diff-level], .difficulty-label, [class*='Difficulty'], [class*='difficulty']"
  ) as HTMLElement | null;
  if (el?.innerText?.trim()) return el.innerText.trim();

  // Try color-coded spans (Easy=green, Medium=yellow, Hard=red)
  const spans = document.querySelectorAll("span");
  for (const span of spans) {
    const t = span.innerText?.trim();
    if (t === "Easy" || t === "Medium" || t === "Hard") return t;
  }
  return "Unknown";
}

function getTags(): string[] {
  const tags: string[] = [];
  document.querySelectorAll("[data-cy='topic-tag'], [class*='topicTag'], [class*='topic-tag']").forEach((el) => {
    const t = (el as HTMLElement).innerText?.trim();
    if (t) tags.push(t);
  });
  return tags;
}

/**
 * Get the problem statement text.
 * LeetCode uses generated class names — we use the stable data attribute container
 * and fall back to broader queries.
 */
function getStatementText(): string {
  // Primary: stable data attribute (present since ~2023)
  const primary = document.querySelector("[data-track-load='description_content']") as HTMLElement | null;
  if (primary?.innerText?.trim()) return primary.innerText.trim().slice(0, 8000);

  // Secondary: look for the main content pane by class fragments
  const secondarySelectors = [
    "[class*='description_content']",
    "[class*='questionContent']",
    "[class*='question-content']",
    ".content-wrapper",
    "[class*='Description']",
  ];
  for (const sel of secondarySelectors) {
    try {
      const el = document.querySelector(sel) as HTMLElement | null;
      const text = el?.innerText?.trim();
      if (text && text.length > 50) return text.slice(0, 8000);
    } catch { /* skip */ }
  }

  // Tertiary: find the div containing "Example 1" which is always in the statement
  const allDivs = document.querySelectorAll("div");
  for (const div of allDivs) {
    if ((div as HTMLElement).innerText?.includes("Example 1:") &&
        (div as HTMLElement).innerText?.length > 100) {
      return (div as HTMLElement).innerText.trim().slice(0, 8000);
    }
  }

  return "";
}

function getConstraints(): string {
  // Look for "Constraints:" header in the page text
  const pageText = document.body.innerText;
  const match = pageText.match(/Constraints:\s*([\s\S]*?)(?:\n\n|$)/i);
  return match?.[1]?.trim() ?? "";
}

function getExamples(): Array<{ input_text: string; output_text: string }> {
  const examples: Array<{ input_text: string; output_text: string }> = [];
  document.querySelectorAll("pre").forEach((pre) => {
    const text = (pre as HTMLElement).innerText ?? pre.textContent ?? "";
    const inputMatch = text.match(/Input:\s*([\s\S]*?)Output:/i);
    const outputMatch = text.match(/Output:\s*([^\n]+)/i);
    if (inputMatch && outputMatch) {
      examples.push({
        input_text: inputMatch[1].trim(),
        output_text: outputMatch[1].trim(),
      });
    }
  });
  return examples;
}

function getStarterCode(language: string): string | null {
  if (language === "python3") {
    const lines = Array.from(document.querySelectorAll(".view-lines .view-line"))
      .map((l) => (l as HTMLElement).innerText ?? "").join("\n");
    if (lines.includes("class Solution")) return lines;
  }
  return null;
}

function getRunPanelCapture(): {
  verdict: string; input?: string; output?: string; expected?: string;
} | null {
  const verdictSelectors = [
    "[data-e2e-locator='console-result']",
    "[class*='result-container'] [class*='status']",
    "[class*='testcase-result']",
    "[class*='SubmissionResultStatus']",
  ];
  const verdict = selectText(verdictSelectors);
  if (!verdict) return null;
  return {
    verdict: verdict.replace(/\s+/g, " ").trim(),
    input: selectText(["[data-e2e-locator='console-testcase-input']"]) || undefined,
    output: selectText(["[data-e2e-locator='console-output']"]) || undefined,
    expected: selectText(["[data-e2e-locator='console-expected-output']"]) || undefined,
  };
}

async function getCurrentLanguage(): Promise<string> {
  // Try the language selector button text
  const langSelectors = [
    "[data-cy='lang-select'] button",
    ".ant-select-selection-item",
    "[class*='languageSelector'] button",
    "[class*='CodeEditor'] button",
    "button[class*='lang']",
  ];
  const langText = selectText(langSelectors);
  if (langText) {
    const normalized = langText.toLowerCase()
      .replace("c++", "cpp")
      .replace("python3", "python3")
      .replace("python", "python3")
      .replace(/\s/g, "");
    if (normalized) return normalized;
  }
  // Fallback via SW Monaco bridge
  const codeResult = await fetchFullCode();
  return codeResult?.language ?? "python3";
}


// ── content hash ──────────────────────────────────────────────────────────────

async function sha256Short(text: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
}

// ── main orchestrate function ─────────────────────────────────────────────────

export async function orchestrateDebug(
  selectedCode?: string
): Promise<OrchestrationOutcome> {
  try {
    // 1. Build problem object from DOM
    const slug = getSlug();
    const statementText = getStatementText();
    if (!statementText) {
      return {
        ok: false,
        error: { kind: "no_problem", message: "Could not read problem statement. Are you on a problem page?" },
      };
    }

    // Detect actual language for display, but always send python3 to backend
    // (MOCK mode and Phase 1 engine only support Python 3)
    const detectedLang = await getCurrentLanguage();
    const contentHash = await sha256Short(statementText + detectedLang);

    const problem: LCProblem = {
      slug,
      source: "leetcode",
      title: getTitle(),
      difficulty: getDifficulty(),
      tags: getTags(),
      statement_text: statementText,
      examples: getExamples(),
      constraints_text: getConstraints(),
      starter_python: getStarterCode(detectedLang) ?? undefined,
      // Always send python3 so MOCK + real backend accepts the capture
      lang_selected: "python3",
      content_hash: contentHash,
      captured_at: new Date().toISOString(),
      run_capture: getRunPanelCapture() ?? undefined,
    };

    // 2. Get the code to analyze
    let code = selectedCode?.trim() ?? "";
    if (!code) {
      const fullCode = await fetchFullCode();
      code = fullCode?.code.trim() ?? "";
    }
    // If still no code (editor not yet loaded), use a stub so panels still show
    if (!code) {
      code = "# No code captured — open the code editor and try again";
    }

    // 3. POST /problems/capture
    let capture: CaptureResponse;
    try {
      const raw = await sendToSW<CaptureResponse | { error: string }>({ type: "CAPTURE_PROBLEM", problem });
      if (!raw || "error" in raw) {
        return { ok: false, error: { kind: "capture_failed", message: "Backend unavailable — is it running at localhost:8000?", detail: (raw as { error: string })?.error } };
      }
      capture = raw;
    } catch (err) {
      return { ok: false, error: { kind: "capture_failed", message: "Backend unavailable — is it running at localhost:8000?", detail: String(err) } };
    }

    // ── Do NOT gate on capture.supported — show panels even for unsupported langs.
    // The result card will display a warning flag instead of blocking the user.
    // This lets the UI demo work on any problem / language in Phase 1.

    // 4. POST /analyze
    const req: AnalyzeRequest = {
      user_id: "local-user",
      problem_slug: slug,
      code,
      language: "python3",
      run_capture: problem.run_capture ?? null,
      paste_chars: totalPasteChars,
      elapsed_ms: Date.now() - pageLoadTime,
    };

    let analysis: AnalyzeResponse;
    try {
      const raw = await sendToSW<AnalyzeResponse | { error: string }>({ type: "ANALYZE", req });
      if (!raw || "error" in raw) {
        return { ok: false, error: { kind: "analyze_failed", message: "Analysis failed", detail: (raw as { error: string })?.error } };
      }
      analysis = raw;
    } catch (err) {
      return { ok: false, error: { kind: "analyze_failed", message: "Analysis failed", detail: String(err) } };
    }

    return { ok: true, data: { capture, analysis, problem, code } };
  } catch (err) {
    return {
      ok: false,
      error: { kind: "analyze_failed", message: "Unexpected error", detail: String(err) },
    };
  }
}
