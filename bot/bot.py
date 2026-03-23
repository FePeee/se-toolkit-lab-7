#!/usr/bin/env python3
"""Telegram bot entry point with --test mode support.

Usage:
    uv run bot.py --test "/start"    # Test mode: prints response to stdout
    uv run bot.py                     # Telegram mode: starts polling
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the bot directory to the Python path
bot_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(bot_dir))

from config import settings
from handlers import HandlerDeps, handle_help, handle_health, handle_labs, handle_scores, handle_start
from services import LlmClient, LmsClient


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        type=str,
        metavar="TEXT",
        help="Test mode: process input and print response to stdout (no Telegram connection)",
    )
    return parser.parse_args()


def create_handler_deps() -> HandlerDeps:
    """Create handler dependencies from settings."""
    return HandlerDeps(
        lms_api_base_url=settings.lms_api_base_url,
        lms_api_key=settings.lms_api_key,
        llm_api_base_url=settings.llm_api_base_url,
        llm_api_key=settings.llm_api_key,
    )


async def run_test_mode(text: str) -> None:
    """Run the bot in test mode.

    Args:
        text: Input text to process (e.g., "/start", "/help", "what labs are available").
    """
    deps = create_handler_deps()

    # Determine which handler to call based on the input
    text_lower = text.strip().lower()

    if text_lower == "/start":
        response = handle_start(text, deps)
    elif text_lower == "/help":
        response = handle_help(text, deps)
    elif text_lower == "/health":
        response = handle_health(text, deps)
    elif text_lower == "/labs":
        response = handle_labs(text, deps)
    elif text_lower.startswith("/scores"):
        response = handle_scores(text, deps)
    else:
        # For natural language input, use LLM client (will be implemented in Task 3)
        llm_client = LlmClient(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_api_model,
        )
        try:
            response = await llm_client.chat(text)
        finally:
            await llm_client.close()

    print(response)


async def run_telegram_mode() -> None:
    """Run the bot in Telegram polling mode."""
    # Check if bot token is configured
    if not settings.bot_token:
        print(
            "Error: BOT_TOKEN not configured in .env.bot.secret\n"
            "Please copy .env.bot.example to .env.bot.secret and fill in your bot token.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from aiogram import Bot, Dispatcher
    except ImportError:
        print(
            "Error: aiogram not installed. Run: uv sync",
            file=sys.stderr,
        )
        sys.exit(1)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Register handlers (will be implemented in Task 2)
    @dp.message()
    async def handle_message(message):
        """Handle incoming messages."""
        text = message.text or ""
        deps = create_handler_deps()

        if text == "/start":
            response = handle_start(text, deps)
        elif text == "/help":
            response = handle_help(text, deps)
        elif text == "/health":
            response = handle_health(text, deps)
        elif text == "/labs":
            response = handle_labs(text, deps)
        elif text.startswith("/scores"):
            response = handle_scores(text, deps)
        else:
            # Natural language handling (Task 3)
            response = "Извините, я пока понимаю только команды. Используйте /help для справки."

        await message.answer(response)

    print("Bot started. Press Ctrl+C to stop.")
    await dp.start_polling(bot)
    await bot.session.close()


async def main() -> None:
    """Main entry point."""
    args = parse_args()

    if args.test:
        await run_test_mode(args.test)
    else:
        await run_telegram_mode()


if __name__ == "__main__":
    asyncio.run(main())
