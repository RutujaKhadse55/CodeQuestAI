// ─── Source C: Run Panel Observer ─────────────────────────────────────────
// Watches the LeetCode result panel with a MutationObserver.
// When the learner clicks Run and results appear, captures the verdict,
// failing input, actual output, and expected output.
// Only activates on user-triggered run events (not auto-polling).

import type { RunCapture } from "../../api/types";

type RunCaptureCallback = (capture: RunCapture) => void;

const RESULT_PANEL_SELECTORS = [
  '[data-e2e-locator="submission-result"]',
  "#result_state_container",
];

/** Find the result panel in the DOM */
function findResultPanel(): Element | null {
  for (const sel of RESULT_PANEL_SELECTORS) {
    const el = document.querySelector(sel);
    if (el) return el;
  }
  return null;
}

/** Parse text content from a child matching a label */
function extractField(panel: Element, labels: string[]): string {
  // Try data attributes first
  for (const label of labels) {
    const el = panel.querySelector(`[data-label="${label}"]`);
    if (el) return el.textContent?.trim() ?? "";
  }
  // Fallback: look for a <span>/<div> whose previous sibling text contains the label
  const allText = panel.querySelectorAll("span, div, p");
  for (const el of allText) {
    const prev = el.previousSibling?.textContent?.toLowerCase() ?? "";
    if (labels.some((l) => prev.includes(l.toLowerCase()))) {
      return el.textContent?.trim() ?? "";
    }
  }
  return "";
}

/** Parse the current result panel state */
function parseResultPanel(panel: Element): RunCapture | null {
  const fullText = panel.textContent ?? "";

  // Detect verdict keyword
  let verdict: RunCapture["verdict"] = "Wrong Answer";
  if (/accepted/i.test(fullText)) verdict = "Accepted";
  else if (/runtime error/i.test(fullText)) verdict = "Runtime Error";
  else if (/time limit/i.test(fullText)) verdict = "Time Limit Exceeded";
  else if (/wrong answer/i.test(fullText)) verdict = "Wrong Answer";
  else return null; // no recognisable verdict yet

  return {
    verdict,
    input: extractField(panel, ["Input", "Last Executed Input"]),
    output: extractField(panel, ["Output", "Stdout"]),
    expected: extractField(panel, ["Expected Output", "Expected"]),
    stdout: extractField(panel, ["Stdout"]),
    error: extractField(panel, ["Error", "Runtime Error"]),
  };
}

// ── singleton observer ─────────────────────────────────────────────────────────

let observer: MutationObserver | null = null;

/** Start watching the result panel. Calls `cb` whenever a run result appears. */
export function watchRunPanel(cb: RunCaptureCallback): () => void {
  if (observer) observer.disconnect();

  const observe = (panel: Element) => {
    observer = new MutationObserver(() => {
      const capture = parseResultPanel(panel);
      if (capture) cb(capture);
    });
    observer.observe(panel, { childList: true, subtree: true, characterData: true });
    console.info("[CQ RunPanel] Watching result panel.");
  };

  // Try to find the panel immediately; if not present, use a root observer
  const panel = findResultPanel();
  if (panel) {
    observe(panel);
  } else {
    // Wait for the panel to appear (LeetCode renders it lazily)
    const rootObs = new MutationObserver(() => {
      const p = findResultPanel();
      if (p) {
        rootObs.disconnect();
        observe(p);
      }
    });
    rootObs.observe(document.body, { childList: true, subtree: true });
  }

  // Return a cleanup function
  return () => {
    observer?.disconnect();
    observer = null;
  };
}
