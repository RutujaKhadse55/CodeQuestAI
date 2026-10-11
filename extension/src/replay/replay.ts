// ─── Replay Mode — load a fixture snapshot instead of live capture ──────────
// Enables development and demo safety when LeetCode's DOM changes.
// Usage: pass ?replay=two-sum in the extension URL, or set storage flag.

import type { LCProblem } from "../api/types";

const FIXTURES_BASE = chrome.runtime.getURL("fixtures/lc/");

/** Load a problem fixture from the bundled fixtures/lc/<slug>/problem.json */
export async function loadFixture(slug: string): Promise<LCProblem | null> {
  const url = `${FIXTURES_BASE}${slug}/problem.json`;
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const problem: LCProblem = await res.json();
    console.info(`[CQ Replay] Loaded fixture: ${slug} (captured ${problem.captured_at})`);
    return problem;
  } catch (err) {
    console.warn(`[CQ Replay] Could not load fixture ${slug}:`, err);
    return null;
  }
}

/** Check if replay mode is active (storage flag or URL param) */
export async function getReplaySlug(): Promise<string | null> {
  return new Promise((resolve) => {
    chrome.storage.session.get({ replaySlug: null }, (items) => {
      resolve(items.replaySlug as string | null);
    });
  });
}

/** Enable replay for a given slug */
export function setReplaySlug(slug: string | null): Promise<void> {
  return new Promise((resolve) => {
    chrome.storage.session.set({ replaySlug: slug }, resolve);
  });
}
