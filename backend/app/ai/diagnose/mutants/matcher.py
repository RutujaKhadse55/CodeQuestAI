"""Hamming-similarity matcher between a learner's fuzz vector and mutant fingerprints."""
from dataclasses import dataclass

from .fingerprint import Fingerprint

THRESHOLD = 0.8
AMBIGUOUS_FAIL_RATE = 0.9


@dataclass(frozen=True)
class Match:
    mistake_class: str | None
    confidence: float


def hamming_similarity(a: str, b: str) -> float:
    if not a or len(a) != len(b):
        return 0.0
    return sum(x == y for x, y in zip(a, b)) / len(a)


def _overlap(a: str, b: str) -> float:
    fa = {i for i, c in enumerate(a) if c == "1"}
    fb = {i for i, c in enumerate(b) if c == "1"}
    return len(fa & fb) / len(fa | fb) if fa | fb else 0.0


def match(learner_vector: str, fingerprints: list[Fingerprint], threshold: float = THRESHOLD) -> Match:
    """Best mutant by (Hamming similarity, failing-set overlap). Below threshold, or sharing no failing input with the
    learner (agreement on passes alone says nothing), => no known pattern: class None, low confidence."""
    if not learner_vector or "1" not in learner_vector or not fingerprints:
        return Match(None, 0.0)
    if learner_vector.count("1") / len(learner_vector) > AMBIGUOUS_FAIL_RATE:
        return Match(None, 0.15)  # fails (almost) every input: many different bugs look identical, so do not guess a class
    best: tuple[float, float, Fingerprint] | None = None
    for fp in fingerprints:
        sim, ov = hamming_similarity(learner_vector, fp.vector), _overlap(learner_vector, fp.vector)
        if ov > 0 and (best is None or (sim, ov) > best[:2]):
            best = (sim, ov, fp)
    if best is None:
        return Match(None, 0.0)
    sim, _, fp = best
    if sim >= threshold:
        return Match(fp.mistake_class, round(sim, 3))
    return Match(None, round(min(sim, 0.3) * 0.5, 3))  # low confidence: nearest pattern is too far
