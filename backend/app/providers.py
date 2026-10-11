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
