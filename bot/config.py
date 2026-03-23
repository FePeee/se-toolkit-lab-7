from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILES = [REPO_ROOT / ".env.bot.secret", REPO_ROOT / ".env.bot.example"]


@dataclass(frozen=True)
class BotConfig:
    bot_token: str | None
    lms_api_base_url: str
    lms_api_key: str
    llm_api_key: str
    llm_api_base_url: str
    llm_api_model: str
    miniapp_url: str | None


def _load_env_files() -> None:
    for env_path in DEFAULT_ENV_FILES:
        if env_path.exists():
            load_dotenv(env_path, override=False)


def load_config(*, require_bot_token: bool = True) -> BotConfig:
    _load_env_files()

    bot_token = os.getenv("BOT_TOKEN")
    lms_api_base_url = os.getenv("LMS_API_BASE_URL")
    lms_api_key = os.getenv("LMS_API_KEY")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_api_base_url = os.getenv("LLM_API_BASE_URL", "http://localhost:42005/v1")
    llm_api_model = os.getenv("LLM_API_MODEL", "qwen/qwen3-coder-480b-a35b")
    miniapp_url = os.getenv("MINIAPP_URL")

    missing = []
    if require_bot_token and not bot_token:
        missing.append("BOT_TOKEN")
    if not lms_api_base_url:
        missing.append("LMS_API_BASE_URL")
    if not lms_api_key:
        missing.append("LMS_API_KEY")
    if not llm_api_key:
        missing.append("LLM_API_KEY")

    if missing:
        missing_csv = ", ".join(missing)
        raise ValueError(f"Missing required environment variables: {missing_csv}")

    return BotConfig(
        bot_token=bot_token,
        lms_api_base_url=lms_api_base_url or "",
        lms_api_key=lms_api_key or "",
        llm_api_key=llm_api_key or "",
        llm_api_base_url=llm_api_base_url,
        llm_api_model=llm_api_model,
        miniapp_url=miniapp_url,
    )
