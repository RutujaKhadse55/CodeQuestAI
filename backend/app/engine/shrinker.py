"""Failure shrinking and classification. Pure functions, stdlib only.

This file is ALSO concatenated into the sandbox harness source (see sandbox/runner.py), so it must stay
standalone: no relative imports, no app imports.
"""
import json


def _sum_abs(v):
    if isinstance(v, bool):
        return 0
    if isinstance(v, (int, float)):
        return abs(v)
    if isinstance(v, (list, tuple)):
        return sum(_sum_abs(x) for x in v)
    return 0


def _cost(args):
    return (len(json.dumps(args, default=repr)), _sum_abs(args))


def _variants(v):
    """Simpler versions of one value, most aggressive first."""
    out = []
    if isinstance(v, bool):
        return out
    if isinstance(v, int):
        for c in (0, int(v / 2), v - 1 if v > 0 else v + 1):
            if c != v and c not in out:
                out.append(c)
    elif isinstance(v, (list, str)):
        n = len(v)
        if n > 0:
            out.append(v[:0])
        if n > 1:
            out.append(v[: n // 2])
            out.append(v[n // 2:])
        for i in range(min(n, 24)):
            out.append(v[:i] + v[i + 1:])
        if isinstance(v, list):
            for i in range(min(n, 24)):
                for sub in _variants(v[i]):
                    out.append(v[:i] + [sub] + v[i + 1:])
    return out


def _candidates(args):
    for i, a in enumerate(args):
        for v in _variants(a):
            yield args[:i] + [v] + args[i + 1:]


def shrink(args, still_fails, max_steps=300):
    """Greedy delta-debugging: keep the simplest args for which still_fails(args) is True."""
    cur, steps, improved = list(args), 0, True
    while improved and steps < max_steps:
        improved = False
        for cand in _candidates(cur):
            steps += 1
            if steps > max_steps:
                break
            if _cost(cand) < _cost(cur) and still_fails(cand):
                cur, improved = cand, True
                break
    return cur


def _flat_numbers(v):
    if isinstance(v, bool):
        return []
    if isinstance(v, (int, float)):
        return [v]
    if isinstance(v, (list, tuple)):
        return [n for x in v for n in _flat_numbers(x)]
    return []


def classify_failure(args):
    """Bucket a (shrunk) failing input: empty, single_element, duplicates, negatives, large, boundary, general.

    Only the bucket is ever shown to the learner — never the input itself.
    """
    seqs = [a for a in args if isinstance(a, (list, tuple, str))]
    if any(len(s) == 0 for s in seqs):
        return "empty"
    if any(len(s) == 1 for s in seqs):
        return "single_element"
    for s in seqs:
        if isinstance(s, (list, tuple)):
            flat = _flat_numbers(s) if all(not isinstance(x, (list, tuple)) for x in s) else None
            items = list(s) if flat is None else flat
            try:
                if len(set(map(repr, items))) < len(items):
                    return "duplicates"
            except TypeError:
                pass
    nums = _flat_numbers(list(args))
    if any(n < 0 for n in nums):
        return "negatives"
    if any(abs(n) >= 1000 for n in nums):
        return "large"
    if any(isinstance(a, int) and not isinstance(a, bool) and a in (0, 1) for a in args):
        return "boundary"
    return "general"
