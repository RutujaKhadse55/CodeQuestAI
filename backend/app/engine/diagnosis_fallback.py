"""AST-free rule fallback used when AI's Diagnoser returns no mistake class (plan §6 P2 go/no-go)."""

_RULES = {
    "empty": "missing_empty_case",
    "single_element": "missing_edge_single",
    "boundary": "off_by_one_bound",
    "duplicates": "wrong_comparison",
    "negatives": "wrong_init",
}
FALLBACK_CONFIDENCE = 0.3


def mistake_from_failure_class(failure_class: str | None) -> str | None:
    return _RULES.get(failure_class or "")
