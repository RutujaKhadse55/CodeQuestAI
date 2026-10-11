"""AI Diagnoser: mutation-fingerprint matching (F-07) + hardcode detector hook (F-08).

The Diagnoser protocol only passes the slug, so the ReferenceBundle is taken from providers' bundle cache (analyze.py
always calls providers.bundle_for(problem) before diagnose, keyed "slug:content_hash"), falling back to a DB lookup of
the captured problem. No router change is needed.
"""
from ... import providers
from ...contracts.models import Diagnosis, Divergence, ReferenceBundle
from .mutants.fingerprint import FingerprintStore
from .mutants.matcher import match

_registry: dict[str, ReferenceBundle] = {}  # optional explicit override: remember_bundle(slug, bundle)


def remember_bundle(slug: str, bundle: ReferenceBundle) -> None:
    _registry[slug] = bundle


def _find_bundle(slug: str) -> ReferenceBundle | None:
    if slug in _registry:
        return _registry[slug]
    hits = [v for k, v in providers._bundle_cache.items() if k.startswith(f"{slug}:")]
    if hits:
        return hits[-1]  # most recently built = current content hash
    try:
        from sqlmodel import Session

        from ...contracts.models import LCProblem
        from ...db import engine
        from ...db.models_core import LCProblemRow
        with Session(engine) as s:
            row = s.get(LCProblemRow, slug)
            if row is not None and row.supported:
                return providers.bundle_for(LCProblem.model_validate_json(row.payload_json))
    except Exception:  # noqa: BLE001
        pass
    return None


class AIDiagnoser:
    """Implements contracts.protocols.Diagnoser."""

    def __init__(self, store: FingerprintStore | None = None):
        self.store = store or FingerprintStore()

    def diagnose(self, fuzz_vector: str, problem_slug: str, divergence: Divergence | None) -> Diagnosis:
        out = Diagnosis(mistake_class=None, confidence=0.0, divergence=divergence)
        try:
            bundle = _find_bundle(problem_slug)
            if bundle is None or not fuzz_vector:
                return out
            m = match(fuzz_vector, self.store.get(problem_slug, bundle))
            out.mistake_class, out.confidence = m.mistake_class, m.confidence
        except Exception:  # noqa: BLE001  (diagnosis must degrade to 'no known pattern', never fail /analyze)
            pass
        return out


def register() -> AIDiagnoser:
    from .hardcode import detect
    d = AIDiagnoser()
    providers.register_diagnoser(d)
    providers.register_hardcode(detect)
    return d
