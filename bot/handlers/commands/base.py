"""Base handler types and stub implementations."""

from dataclasses import dataclass


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


def handle_health(text: str, deps: HandlerDeps) -> str:
    """Handle /health command.

    Args:
        text: The command text (ignored for /health).
        deps: Handler dependencies.

    Returns:
        System health status.
    """
    # Placeholder - will be implemented in Task 2
    if deps.lms_api_base_url:
        return (
            "🏥 Статус системы:\n\n"
            f"✅ LMS API: подключен ({deps.lms_api_base_url})\n"
            "⏳ Backend: проверка будет реализована в Task 2"
        )
    return (
        "🏥 Статус системы:\n\n"
        "⚠️ LMS API: не настроен (проверьте .env.bot.secret)\n"
        "⏳ Backend: проверка будет реализована в Task 2"
    )


def handle_labs(text: str, deps: HandlerDeps) -> str:
    """Handle /labs command.

    Args:
        text: The command text (ignored for /labs).
        deps: Handler dependencies.

    Returns:
        List of available labs.
    """
    # Placeholder - will be implemented in Task 2
    return (
        "📋 Доступные лабораторные работы:\n\n"
        "⏳ Список будет загружен из LMS в Task 2\n\n"
        "Пока вы можете проверить команды /start и /help."
    )


def handle_scores(text: str, deps: HandlerDeps) -> str:
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
        return (
            "⚠️ Укажите ID лабораторной работы.\n\n"
            "Пример: /scores lab-04"
        )

    lab_id = parts[1]
    # Placeholder - will be implemented in Task 2
    return (
        f"📊 Результаты по {lab_id}:\n\n"
        "⏳ Данные будут загружены из LMS в Task 2\n\n"
        f"Запрошена лабораторная: {lab_id}"
    )
