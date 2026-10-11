// ─── Source B: LeetCode Page GraphQL (public problem metadata) ─────────────
// Uses same-origin fetch to /graphql from the content script context.
// This is an unofficial interface — [VERIFY field names] on demo day.
// Rate-limited: ≥ 1 second between calls.

import type { LCProblem } from "../../api/types";

const GRAPHQL_URL = "https://leetcode.com/graphql";
const QUERY = `
  query QuestionData($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
      titleSlug
      title
      difficulty
      topicTags { name }
      content
      exampleTestcases
      codeSnippets { lang langSlug code }
    }
  }
`;

let lastFetchAt = 0;

/** Fetch problem metadata via page GraphQL. Returns null on failure. */
export async function captureFromGraphQL(slug: string): Promise<Partial<LCProblem> | null> {
  // Rate limiting: 1 req/s
  const now = Date.now();
  if (now - lastFetchAt < 1000) {
    await new Promise((r) => setTimeout(r, 1000 - (now - lastFetchAt)));
  }
  lastFetchAt = Date.now();

  try {
    const res = await fetch(GRAPHQL_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: QUERY, variables: { titleSlug: slug } }),
      credentials: "include", // same-origin session cookie
    });

    if (!res.ok) return null;

    const json = await res.json();
    const q = json?.data?.question;
    if (!q) return null;

    // Strip HTML from content
    const div = document.createElement("div");
    div.innerHTML = q.content ?? "";
    const statement_text = (div.textContent ?? "").replace(/\s+/g, " ").trim().slice(0, 8000);

    // Get Python 3 starter code
    const pythonSnippet = (q.codeSnippets as Array<{ langSlug: string; code: string }> | undefined)
      ?.find((s) => s.langSlug === "python3");

    return {
      slug: q.titleSlug,
      title: q.title,
      difficulty: (q.difficulty as LCProblem["difficulty"]) ?? "Medium",
      tags: (q.topicTags as Array<{ name: string }> | undefined)?.map((t) => t.name) ?? [],
      statement_text,
      starter_python: pythonSnippet?.code ?? "",
      // exampleTestcases is a newline-delimited string of raw inputs
      examples: [],  // parse examples from DOM (Source A) — more reliable
    };
  } catch (err) {
    console.warn("[CQ GraphQL] fetch failed:", err);
    return null;
  }
}
