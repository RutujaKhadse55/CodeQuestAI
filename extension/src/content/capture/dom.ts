// ─── Source A: DOM Capture ─────────────────────────────────────────────────
// Reads the LeetCode problem page DOM and builds an LCProblem draft.
// Uses selectors from selectors.config.ts with 2 fallbacks each.

import { querySelector, readText } from "../selectors.config";
import type { LCProblem } from "../../api/types";
import { sha256Hex } from "../../utils/hash";

/** Strip HTML tags, normalise whitespace */
function stripHtml(html: string): string {
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  return (tmp.textContent ?? "").replace(/\s+/g, " ").trim().slice(0, 8000);
}

/** Extract difficulty from badge class or text */
function parseDifficulty(el: Element | null): LCProblem["difficulty"] {
  const text = el?.textContent?.trim().toLowerCase() ?? "";
  if (text.includes("easy")) return "Easy";
  if (text.includes("hard")) return "Hard";
  return "Medium";
}

/** Parse examples: extracts pairs from the visible example blocks */
function parseExamples(): LCProblem["examples"] {
  const examples: LCProblem["examples"] = [];
  // Modern LeetCode wraps examples in <pre> tags inside the content block
  const pres = document.querySelectorAll(
    '[data-track-load="description_content"] pre, .question-content__JfgR pre'
  );
  pres.forEach((pre) => {
    const text = pre.textContent ?? "";
    const inputMatch = text.match(/Input:\s*([\s\S]*?)(?=Output:|$)/i);
    const outputMatch = text.match(/Output:\s*([\s\S]*?)(?=Explanation:|Constraints:|$)/i);
    if (inputMatch && outputMatch) {
      examples.push({
        input_text: inputMatch[1].trim(),
        output_text: outputMatch[1].trim(),
      });
    }
  });
  return examples;
}

/** Get currently visible code from the Monaco / CodeMirror editor */
function getEditorCode(): string {
  // Monaco view-lines
  const lines = document.querySelectorAll(".view-line");
  if (lines.length > 0) {
    return Array.from(lines)
      .map((l) => l.textContent ?? "")
      .join("\n");
  }
  // CodeMirror (fallback)
  const cm = document.querySelector(".CodeMirror-code");
  if (cm) return cm.textContent?.trim() ?? "";
  // User text selection as last resort
  return window.getSelection()?.toString().trim() ?? "";
}

/** Get selected language */
function getLanguage(): string {
  const el = querySelector("language");
  const text = el?.textContent?.trim().toLowerCase() ?? "python3";
  if (text.includes("python")) return "python3";
  if (text.includes("java") && !text.includes("javascript")) return "java";
  if (text.includes("javascript")) return "javascript";
  if (text.includes("c++")) return "cpp";
  return text || "python3";
}

/** Get problem slug from URL */
function getSlug(): string {
  const match = location.pathname.match(/\/problems\/([^/]+)/);
  return match?.[1] ?? "unknown";
}

/** Get tags from the DOM breadcrumb / topic tags section */
function getTags(): string[] {
  const tagEls = document.querySelectorAll(
    'a[href*="/tag/"], .topic-tag__1jni'
  );
  return Array.from(tagEls).map((el) => el.textContent?.trim() ?? "").filter(Boolean);
}

/** Get constraints text */
function getConstraints(): string {
  const statementEl = querySelector("statement");
  if (!statementEl) return "";
  // Constraints section follows a <strong>Constraints:</strong> in the HTML
  const html = statementEl.innerHTML;
  const match = html.match(/Constraints:([\s\S]*?)(?:<\/ul>|$)/i);
  if (match) {
    const tmp = document.createElement("div");
    tmp.innerHTML = match[1];
    return tmp.textContent?.replace(/\s+/g, " ").trim() ?? "";
  }
  return "";
}

// ── main export ───────────────────────────────────────────────────────────────

/** Capture the current LeetCode problem from the page DOM */
export async function captureFromDom(): Promise<LCProblem | null> {
  const slug = getSlug();
  if (slug === "unknown") return null;

  const titleEl = querySelector("title");
  const diffEl = querySelector("difficulty");
  const stmtEl = querySelector("statement");

  const statement_text = stmtEl ? stripHtml(stmtEl.innerHTML) : "";
  const content_hash = await sha256Hex(statement_text);

  return {
    slug,
    source: "leetcode",
    title: titleEl?.textContent?.trim() ?? slug,
    difficulty: parseDifficulty(diffEl),
    tags: getTags(),
    statement_text,
    examples: parseExamples(),
    constraints_text: getConstraints(),
    starter_python: getEditorCode(),
    lang_selected: getLanguage(),
    captured_at: new Date().toISOString(),
    content_hash,
  };
}
