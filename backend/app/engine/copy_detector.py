"""Copy detection (plan F-09): a large paste that passes quickly is flagged.

Flagged attempts do not count toward hint unlocks and their mastery update is deferred until the learner
passes an explain-back (Mastery.release_pending).
"""
LARGE_PASTE_CHARS = 120
PASTE_SHARE = 0.6        # pasted chars / total code length
QUICK_PASS_MS = 90_000   # time on problem before this run


def is_copy(paste_chars: int, code_len: int, elapsed_ms: int, passed_all: bool) -> bool:
    if not passed_all or paste_chars < LARGE_PASTE_CHARS or code_len <= 0:
        return False
    if paste_chars < PASTE_SHARE * code_len:
        return False
    return 0 < elapsed_ms < QUICK_PASS_MS
