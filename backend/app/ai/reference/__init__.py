"""Real ReferenceBuilder (curated bundles + sandbox-validated LLM synthesis)."""


def register() -> None:
    from ... import providers
    from .synth import AIReferenceBuilder
    providers.register_reference_builder(AIReferenceBuilder())
