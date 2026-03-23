from __future__ import annotations

import argparse
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from config import load_config
from handlers import route_input
from services import LLMClient, LMSClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SE Toolkit bot entrypoint")
    parser.add_argument(
        "--test",
        metavar="TEXT",
        help="Run command/message in local test mode and print bot response",
    )
    return parser


def run_test_mode(text: str) -> int:
    cfg = load_config(require_bot_token=False)
    lms_client = LMSClient(cfg.lms_api_base_url, cfg.lms_api_key)
    llm_client = LLMClient(cfg.llm_api_key, cfg.llm_api_base_url, cfg.llm_api_model)
    response = route_input(text, lms_client, llm_client)
    print(response)
    return 0


async def run_telegram_bot() -> int:
    cfg = load_config(require_bot_token=True)
    bot = Bot(token=cfg.bot_token or "")
    dispatcher = Dispatcher()
    lms_client = LMSClient(cfg.lms_api_base_url, cfg.lms_api_key)
    llm_client = LLMClient(cfg.llm_api_key, cfg.llm_api_base_url, cfg.llm_api_model)
    keyboard_rows = [
        [KeyboardButton(text="what labs are available?")],
        [
            KeyboardButton(text="show me scores for lab 4"),
            KeyboardButton(text="which lab has the lowest pass rate?"),
        ],
        [KeyboardButton(text="/health"), KeyboardButton(text="/help")],
    ]
    if cfg.miniapp_url:
        keyboard_rows.insert(
            0,
            [KeyboardButton(text="Open Mini App", web_app=WebAppInfo(url=cfg.miniapp_url))],
        )
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)

    @dispatcher.message()
    async def on_message(message: Message) -> None:
        text = message.text or ""
        response = route_input(text, lms_client, llm_client)
        await message.answer(response, reply_markup=keyboard)

    await dispatcher.start_polling(bot)
    return 0


def main() -> int:
    args = build_parser().parse_args()

    if args.test is not None:
        return run_test_mode(args.test)

    return asyncio.run(run_telegram_bot())


if __name__ == "__main__":
    raise SystemExit(main())