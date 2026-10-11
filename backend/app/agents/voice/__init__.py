from . import cache, credits


def register() -> None:
    """Wire the credit meter and deletion hooks into providers (call from startup)."""
    from ... import providers
    providers.register_credits(credits.snapshot)
    providers.register_deletion_hook("tts_credits", credits.delete_user)
