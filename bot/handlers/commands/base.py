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
        "👋 Добро пожаловать в LMS Bot!\n\n"
        "Я помогу вам взаимодействовать с LMS через Telegram.\n\n"
        "Доступные команды:\n"
        "/help — показать список команд\n"
        "/health — проверить статус системы\n"
        "/labs — показать доступные лабораторные работы\n"
        "/scores <lab> — показать результаты по лабораторной\n\n"
        "Также вы можете задавать вопросы естественным языком."
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
        "📚 Справка по командам:\n\n"
        "/start — приветственное сообщение\n"
        "/help — эта справка\n"
        "/health — проверка работоспособности системы\n"
        "/labs — список доступных лабораторных работ\n"
        "/scores <lab_id> — результаты по конкретной лабораторной\n\n"
        "Вы также можете задавать вопросы естественным языком, например:\n"
        "• «Какие лабораторные доступны?»\n"
        "• «Покажи мои результаты по lab-04»\n"
        "• «Как работает система?»"
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
            f"🏥 Статус системы:\n\n"
            f"✅ Backend: здоров\n"
            f"📦 Доступно элементов: {result['item_count']}"
        )
    except BackendError as e:
        return f"🏥 Статус системы:\n\n⚠️ {e.user_message}"
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
                "📋 Доступные лабораторные работы:\n\n"
                "⚠️ Список лабораторных пуст.\n"
                "Возможно, данные ещё не синхронизированы."
            )

        lines = ["📋 Доступные лабораторные работы:"]
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
        return f"📋 Доступные лабораторные работы:\n\n⚠️ {e.user_message}"
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
        return "⚠️ Укажите ID лабораторной работы.\n\nПример: /scores lab-04"

    lab_id = parts[1]
    client = LmsClient(deps.lms_api_base_url, deps.lms_api_key)
    try:
        pass_rates = await client.get_pass_rates(lab_id)
        if not pass_rates:
            return (
                f"📊 Результаты по {lab_id}:\n\n"
                "⚠️ Данные о результатах отсутствуют.\n"
                "Возможно, эта лабораторная ещё не сдана ни одним студентом."
            )

        lines = [f"📊 Результаты по {lab_id}:"]
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
            lines.append(f"\n• {task_name}: {percentage} ({attempts} попыток)")

        return "\n".join(lines)
    except BackendError as e:
        return f"📊 Результаты по {lab_id}:\n\n⚠️ {e.user_message}"
    finally:
        await client.close()
