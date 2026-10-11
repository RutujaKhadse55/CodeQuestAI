"""Wiring point between Backend and the AI/Agents implementations.

Until AI's real ReferenceBuilder / Diagnoser are merged (flag USE_REAL_AI=1), Backend's stand-ins are used.
Swapping later = register the real objects here (or in AI's package at import time); no router changes.
"""
from . import config
from .contracts.fakes.backend_fakes import FakeDiagnoser, FakeReferenceBuilder
from .contracts.protocols import Diagnoser, ReferenceBuilder

_reference_builder: ReferenceBuilder | None = None
_diagnoser: Diagnoser | None = None
_bundle_cache: dict[str, object] = {}  # content_hash -> ReferenceBundle (plan §1.4 item 5)


def register_reference_builder(b: ReferenceBuilder) -> None:
    global _reference_builder
    _reference_builder = b
    _bundle_cache.clear()


def register_diagnoser(d: Diagnoser) -> None:
    global _diagnoser
    _diagnoser = d


def reference_builder() -> ReferenceBuilder:
    return _reference_builder or FakeReferenceBuilder()


def diagnoser() -> Diagnoser:
    return _diagnoser or FakeDiagnoser()


def bundle_for(problem):
    """Build once per content_hash and cache."""
    key = f"{problem.slug}:{problem.content_hash}"
    if key not in _bundle_cache:
        _bundle_cache[key] = reference_builder().build(problem)
    return _bundle_cache[key]


USING_REAL_AI = config.USE_REAL_AI


# ---- hooks owned by other roles; defaults keep Backend self-sufficient ----
from typing import Callable  # noqa: E402

_credits: Callable[[str], dict] | None = None          # Agents: ElevenLabs credit meter
_learner_model = None                                   # AI: LearnerModel Protocol
_deletion_hooks: dict[str, Callable[[str], None]] = {}  # Agents: Chroma memory, TTS cache; AI: profiles


def register_credits(fn: Callable[[str], dict]) -> None:
    global _credits
    _credits = fn


def credits(user_id: str) -> dict | None:
    try:
        return _credits(user_id) if _credits else None
    except Exception:  # noqa: BLE001  (a broken meter must never break the dashboard)
        return None


def register_learner_model(m) -> None:
    global _learner_model
    _learner_model = m


def learner_model():
    return _learner_model


def register_deletion_hook(name: str, fn: Callable[[str], None]) -> None:
    """e.g. register_deletion_hook("memory", memory.delete_user); called by DELETE /users/{id}/data."""
    _deletion_hooks[name] = fn


def run_deletion_hooks(user_id: str) -> dict[str, str]:
    out = {}
    for name, fn in _deletion_hooks.items():
        try:
            fn(user_id)
            out[name] = "ok"
        except Exception as e:  # noqa: BLE001
            out[name] = f"error: {type(e).__name__}"
    return out


# ---- LLM hook: AI's llm client registers `complete(prompt) -> str | None`; default None => answerer uses Gemini ----
_llm: Callable[[str], str | None] | None = None


def register_llm(fn: Callable[[str], str | None]) -> None:
    global _llm
    _llm = fn


def llm() -> Callable[[str], str | None] | None:
    return _llm


# ---- hardcode detector hook: AI's detector registers `detect(code, examples) -> list[str]` (reasons) ----
_hardcode: Callable[[str, list], list[str]] | None = None


def register_hardcode(fn: Callable[[str, list], list[str]]) -> None:
    global _hardcode
    _hardcode = fn


def hardcode_detector() -> Callable[[str, list], list[str]]:
    if _hardcode:
        return _hardcode
    from .engine.hardcode import detect  # Backend fallback
    return detect


# ---- chat hooks owned by AI / Agents; Backend defaults keep the problem chat working on its own ----
_guard = None
_hint_service: Callable[[str, str, int, dict], str | None] | None = None
_concept_service: Callable[[str, str], str | None] | None = None


def register_guard(g) -> None:
    """AI's Guard (Protocol: check(text, ctx) -> GuardResult) replaces Backend's DefaultGuard."""
    global _guard
    _guard = g


def guard():
    if _guard:
        return _guard
    from .chat.guard import DefaultGuard
    return DefaultGuard()


def register_hint_service(fn: Callable[[str, str, int, dict], str | None]) -> None:
    """AI's HintService: fn(user_id, problem_slug, level, ctx) -> guarded hint text (or None)."""
    global _hint_service
    _hint_service = fn


def hint_service():
    return _hint_service


def register_concept_service(fn: Callable[[str, str], str | None]) -> None:
    """Approved learning content: fn(concept, language) -> explanation (or None to fall back to the LLM)."""
    global _concept_service
    _concept_service = fn


def concept_service():
    return _concept_service
