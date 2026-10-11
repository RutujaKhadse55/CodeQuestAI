// ─── Guards — page-level enable/disable rules ──────────────────────────────
// The extension is DISABLED on contest, solutions, and editorial pages
// to protect hint integrity (a Hint Guard is pointless next to the editorial).

const DISABLED_PATH_PATTERNS: RegExp[] = [
  /\/contest\//,
  /\/solutions\//,
  /\/editorial\//,
  /\/discuss\//,
];

/** Returns true when the extension should be active on the current page */
export function isExtensionEnabled(url: string = location.href): boolean {
  for (const pattern of DISABLED_PATH_PATTERNS) {
    if (pattern.test(url)) return false;
  }
  // Must be on a problem page
  return /\/problems\/[^/]+/.test(url);
}

/** Returns the reason the extension is disabled, or null if it's enabled */
export function disabledReason(url: string = location.href): string | null {
  if (/\/contest\//.test(url)) return "Disabled on contest pages";
  if (/\/solutions\//.test(url)) return "Disabled on solution pages";
  if (/\/editorial\//.test(url)) return "Disabled on editorial pages";
  if (/\/discuss\//.test(url)) return "Disabled on discussion pages";
  if (!/\/problems\/[^/]+/.test(url)) return "Not a problem page";
  return null;
}
