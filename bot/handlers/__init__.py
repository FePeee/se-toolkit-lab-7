"""Command handlers for the Telegram bot.

Handlers are pure functions that take input and return text responses.
They have no dependency on Telegram - this allows testing via --test mode.
"""

from .commands.base import (
    HandlerDeps,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_start,
)

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
    "HandlerDeps",
]
