// ─── LeetCode DOM Selectors (Source A) ────────────────────────────────────
// Each field has two fallback selectors in priority order.
// If both fail, we fall back to the user's manual text selection.
// ⚠️  LeetCode changes its DOM frequently — monitor and update as needed.

export const SELECTORS = {
  /** Problem title (h4 or data-cy) */
  title: [
    '[data-cy="question-title"]',
    ".mr-2.text-lg.font-medium.text-label-1",
  ],

  /** Difficulty badge */
  difficulty: [
    '[data-difficulty]',
    ".text-difficulty-easy, .text-difficulty-medium, .text-difficulty-hard",
  ],

  /** Problem statement HTML block */
  statement: [
    '[data-track-load="description_content"]',
    ".question-content__JfgR",
  ],

  /** Currently selected language (dropdown text) */
  language: [
    '[data-track-load="qd_selected_lang"]',
    ".ant-select-selection-item",
  ],

  /** Code editor content (CodeMirror or Monaco) */
  editor: [
    ".view-lines",              // Monaco
    ".CodeMirror-code",         // CodeMirror (legacy)
  ],

  /** Run/Submit result panel container */
  resultPanel: [
    '[data-e2e-locator="submission-result"]',
    "#result_state_container",
  ],

  /** Run result: verdict text */
  verdict: [
    ".result__1l3k span",
    "[data-e2e-locator='submission-result'] span",
  ],
} as const;

export type SelectorKey = keyof typeof SELECTORS;

/** Try each selector in order; return the first matching element or null */
export function querySelector(key: SelectorKey): Element | null {
  for (const sel of SELECTORS[key]) {
    const el = document.querySelector(sel);
    if (el) return el;
  }
  return null;
}

/** Return trimmed innerText for the first matching selector */
export function readText(key: SelectorKey): string {
  return querySelector(key)?.textContent?.trim() ?? "";
}
