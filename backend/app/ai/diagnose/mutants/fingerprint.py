"""Mutation fingerprints (F-07): run each surviving mutant on the SAME fixed fuzz set the engine uses for learners
(FINGERPRINT_SEED / FINGERPRINT_N via SandboxEngine.fuzz -> FuzzResult.vector) so vectors are directly comparable."""
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from ....contracts.models import ReferenceBundle
from ....engine.service import FINGERPRINT_N, FINGERPRINT_SEED, SandboxEngine
from .operators import generate_mutants

SEED_FILE = Path(__file__).with_name("mistakes.json")
WORKERS = 4


def mistake_descriptions() -> dict[str, str]:
    try:
        return json.loads(SEED_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@dataclass(frozen=True)
class Fingerprint:
    mistake_class: str
    vector: str  # 0/1 per fixed fuzz input; 1 = this mutant fails that input
    source: str


def bundle_hash(bundle: ReferenceBundle) -> str:
    h = hashlib.sha256()
    for part in (bundle.reference_code, bundle.oracle_code, bundle.gen_inputs_code, bundle.comparator):
        h.update(part.encode("utf-8", "replace") + b"\0")
    return h.hexdigest()[:16]


class FingerprintStore:
    def __init__(self, engine=None):
        self.engine = engine or SandboxEngine()
        self._cache: dict[tuple[str, str], list[Fingerprint]] = {}
        self._lock = threading.Lock()

    def _run(self, bundle: ReferenceBundle, item: tuple[str, str]) -> Fingerprint | None:
        cls, src = item
        try:
            res = self.engine.fuzz(src, bundle, FINGERPRINT_SEED, FINGERPRINT_N)
        except Exception:  # noqa: BLE001  (sandbox hiccup on one mutant: skip it)
            return None
        vec = getattr(res, "vector", "") or ""
        if not vec or "1" not in vec:  # did not run, or behaviourally equivalent to the oracle on this set
            return None
        return Fingerprint(cls, vec, src)

    def build(self, bundle: ReferenceBundle) -> list[Fingerprint]:
        if not bundle.verified or not bundle.reference_code:
            return []
        mutants = generate_mutants(bundle.reference_code)
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            fps = [f for f in pool.map(lambda m: self._run(bundle, m), mutants) if f]
        seen: set[tuple[str, str]] = set()  # same class + same vector adds nothing
        out = []
        for f in fps:
            if (f.mistake_class, f.vector) not in seen:
                seen.add((f.mistake_class, f.vector))
                out.append(f)
        return out

    def get(self, slug: str, bundle: ReferenceBundle) -> list[Fingerprint]:
        """Cached per (slug, content hash of the bundle)."""
        key = (slug, bundle_hash(bundle))
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        fps = self.build(bundle)
        with self._lock:
            self._cache[key] = fps
        return fps

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
