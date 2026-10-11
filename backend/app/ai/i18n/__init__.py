"""Language detection, translation with glossary + guard, voice-friendly text."""


def register():
    """Return the Translator. providers has no translator hook yet, so it is only registered if one appears."""
    from ... import providers
    from .translate import TranslatorImpl
    t = TranslatorImpl()
    hook = getattr(providers, "register_translator", None)
    if hook is not None and getattr(providers, "translator", lambda: None)() is None:
        hook(t)
    return t
