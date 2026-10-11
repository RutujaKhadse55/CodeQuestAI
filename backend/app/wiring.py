"""Registers the AI / Agents implementations with `providers` at startup. Every step is isolated: a failing optional
module is logged and skipped, never a startup error."""
import logging

from . import config

log = logging.getLogger("codequest.wiring")


def _try(name: str, fn) -> None:
    try:
        fn()
        log.info("registered %s", name)
    except Exception as exc:  # noqa: BLE001
        log.warning("could not register %s: %s", name, type(exc).__name__)


def register_all() -> None:
    if config.USE_REAL_AI:
        from .ai import reference, diagnose
        _try("reference builder", reference.register)
        _try("diagnoser + hardcode detector", diagnose.register)
    # /hint and /explain call ai.hints / ai.explain directly; the crew registers its own hint service (FEATURE_CREW).
    from .agents import voice
    _try("voice / credits", voice.register)
    if config.FEATURE_MEMORY:
        from .agents import memory
        _try("memory", memory.register)
