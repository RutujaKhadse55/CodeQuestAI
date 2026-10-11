"""Normalise LeetCode language labels ("Python3", "Python", "python3") to our internal ids."""


def normalize_lang(label: str | None) -> str:
    v = (label or "").strip().lower().replace(" ", "")
    return "python3" if v in ("python3", "python", "py", "py3") else v
