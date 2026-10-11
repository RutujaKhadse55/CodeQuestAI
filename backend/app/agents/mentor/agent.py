"""The mentor chat agent lives in app.chat (guarded, tool-allowlisted, EN/HI/MR). This module only re-exports it so
the Agents package has one stable import path; do not add a second implementation here."""
from ...chat.agent import respond  # noqa: F401

__all__ = ["respond"]
