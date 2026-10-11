def register() -> None:
    """Register the per-user memory deletion hook ("memory"). The Chroma client/embedder are created lazily on first
    use, so registering is cheap and needs no model download. Call only when config.FEATURE_MEMORY is on."""
    from ... import providers
    from .vector_store import get_memory
    providers.register_deletion_hook("memory", lambda uid: get_memory().delete_user(uid))
