"""Hint tiers, Hint Guard v1 and LLM hint generation."""


def register() -> None:
    """Register the Hint Guard and hint service with providers, without overriding anything already set
    (the crew's hint service and any other Guard win)."""
    from ... import providers
    from .generate import hint_service
    from .guard import HintGuard
    if providers._guard is None:
        providers.register_guard(HintGuard())
    if providers.hint_service() is None:
        providers.register_hint_service(hint_service)
