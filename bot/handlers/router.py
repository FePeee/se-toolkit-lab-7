from __future__ import annotations

from handlers.core import (
    handle_free_text,
    handle_health,
    handle_help,
    handle_labs,
    handle_scores,
    handle_start,
)
from services import LLMClient, LMSClient


def route_input(text: str, lms_client: LMSClient, llm_client: LLMClient) -> str:
    cleaned = text.strip()
    if not cleaned:
        return "Please send a command or question."

    if not cleaned.startswith("/"):
        return handle_free_text(cleaned, llm_client, lms_client)

    parts = cleaned.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None

    if command == "/start":
        return handle_start()
    if command == "/help":
        return handle_help()
    if command == "/health":
        return handle_health(lms_client)
    if command == "/labs":
        return handle_labs(lms_client)
    if command == "/scores":
        return handle_scores(arg, lms_client)
    return "Unknown command. Use /help."
