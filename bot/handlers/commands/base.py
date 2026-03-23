"""Base handler types and implementations with real backend integration."""

import sys
from dataclasses import dataclass
from pathlib import Path

# Add the bot directory to the Python path for imports
bot_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(bot_dir))

from services import BackendError, LmsClient


@dataclass
class HandlerDeps:
    """Dependencies injected into handlers."""

    lms_api_base_url: str | None = None
    lms_api_key: str | None = None
    llm_api_base_url: str | None = None
    llm_api_key: str | None = None


def handle_start(text: str, deps: HandlerDeps) -> str:
    """Handle /start command.

    Args:
        text: The command text (ignored for /start).
        deps: Handler dependencies.

    Returns:
        Welcome message.
    """
    return (
        "👋 Welcome to LMS Bot!\n\n"
        "I'll help you interact with the LMS through Telegram.\n\n"
        "Available commands:\n"
        "/help — list all commands\n"
        "/health — check system status\n"
        "/labs — show available labs\n"
        "/scores <lab> — show scores for a lab\n\n"
        "You can also ask questions in natural language."
    )


def handle_help(text: str, deps: HandlerDeps) -> str:
    """Handle /help command.

    Args:
        text: The command text (ignored for /help).
        deps: Handler dependencies.

    Returns:
        List of available commands.
    """
    return (
        "📚 Command Help:\n\n"
        "/start — welcome message\n"
        "/help — this help message\n"
        "/health — check system health status\n"
        "/labs — list available laboratory works\n"
        "/scores <lab_id> — show results for a specific lab\n\n"
        "You can also ask questions in natural language, e.g.:\n"
        "• 'What labs are available?'\n"
        "• 'Show my results for lab-04'\n"
        "• 'How does the system work?'"
    )


async def handle_health(text: str, deps: HandlerDeps) -> str:
    """Handle /health command.

    Args:
        text: The command text (ignored for /health).
        deps: Handler dependencies.

    Returns:
        System health status.
    """
    client = LmsClient(deps.lms_api_base_url, deps.lms_api_key)
    try:
        result = await client.health_check()
        return (
            f"🏥 System Health Status:\n\n"
            f"✅ Backend: OK\n"
            f"📦 Items available: {result['item_count']}"
        )
    except BackendError as e:
        return f"🏥 System Health Status:\n\n⚠️ {e.user_message}"
    finally:
        await client.close()


async def handle_labs(text: str, deps: HandlerDeps) -> str:
    """Handle /labs command.

    Args:
        text: The command text (ignored for /labs).
        deps: Handler dependencies.

    Returns:
        List of available labs.
    """
    client = LmsClient(deps.lms_api_base_url, deps.lms_api_key)
    try:
        labs = await client.get_labs()
        if not labs:
            return (
                "📋 Available Labs:\n\n"
                "⚠️ No labs available.\n"
                "Data may not be synced yet."
            )

        lines = ["📋 Available Labs:"]
        for lab in labs:
            lab_id = lab.get("id", "unknown")
            lab_name = lab.get("name", lab.get("title", lab_id))
            description = lab.get("description", "")
            if description:
                # Truncate long descriptions
                if len(description) > 100:
                    description = description[:97] + "..."
                lines.append(f"\n• **{lab_id}** — {lab_name}")
                lines.append(f"  {description}")
            else:
                lines.append(f"\n• **{lab_id}** — {lab_name}")

        return "\n".join(lines)
    except BackendError as e:
        return f"📋 Available Labs:\n\n⚠️ {e.user_message}"
    finally:
        await client.close()


async def handle_scores(text: str, deps: HandlerDeps) -> str:
    """Handle /scores command.

    Args:
        text: The command text including lab ID.
        deps: Handler dependencies.

    Returns:
        Scores for the specified lab.
    """
    # Extract lab ID from text (e.g., "/scores lab-04" -> "lab-04")
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return "⚠️ Please specify a lab ID.\n\nExample: /scores lab-04"

    lab_id = parts[1]
    client = LmsClient(deps.lms_api_base_url, deps.lms_api_key)
    try:
        pass_rates = await client.get_pass_rates(lab_id)
        if not pass_rates:
            return (
                f"📊 Results for {lab_id}:\n\n"
                "⚠️ No results available.\n"
                "This lab may not have been submitted by any student yet."
            )

        lines = [f"📊 Results for {lab_id}:"]
        for task in pass_rates:
            # API returns 'task' for name and 'avg_score' for percentage
            task_name = task.get(
                "task", task.get("task_name", task.get("task_id", "unknown"))
            )
            pass_rate = task.get("avg_score", task.get("pass_rate", 0))
            attempts = task.get("attempts", 0)
            percentage = (
                f"{pass_rate:.1f}%"
                if isinstance(pass_rate, (float, int))
                else f"{pass_rate}%"
            )
            lines.append(f"\n• {task_name}: {percentage} ({attempts} attempts)")

        return "\n".join(lines)
    except BackendError as e:
        return f"📊 Results for {lab_id}:\n\n⚠️ {e.user_message}"
    finally:
        await client.close()
