# Bot Development Plan

This plan defines how to build a testable Telegram bot that can be validated offline and then deployed on a VM. The architecture is transport-first at the edge and domain-first in the core. The command logic lives in pure handlers that take input and dependencies, then return plain text. That keeps handler behavior testable without Telegram and allows one shared routing path for both CLI and Telegram updates. The `bot.py` entry point owns process concerns only: argument parsing, environment loading, dependency construction, and runtime selection (`--test` vs polling mode).

## Architecture Overview

The bot follows a layered architecture:

1. **Entry Point (`bot.py`)**: Handles CLI arguments, loads configuration, creates dependencies, and routes to either test mode or Telegram polling mode.

2. **Handlers Layer (`handlers/`)**: Pure functions that receive command arguments and service dependencies, return text responses. No Telegram imports, no side effects—just input → output transformations.

3. **Services Layer (`services/`)**: API clients for the LMS backend and LLM. These wrap HTTP calls with error handling and retry logic.

4. **Configuration (`config.py`)**: Loads environment variables using `pydantic-settings`, provides type-safe access to secrets.

This separation means the same handler functions work in both `--test` mode (called directly from CLI) and Telegram mode (called from aiogram handlers).

## Phase 1: Scaffolding (Task 1)

Create the project skeleton:

- `bot.py` with `--test` flag support that prints to stdout and exits 0
- `config.py` for loading `.env.bot.secret`
- `handlers/__init__.py` with stub handlers for `/start`, `/help`, `/health`, `/labs`, `/scores`
- `services/__init__.py` with stub API clients
- `pyproject.toml` with dependencies: `aiogram`, `httpx`, `pydantic-settings`

Verification: `uv run bot.py --test "/start"` prints welcome message, exits 0.

## Phase 2: Backend Integration (Task 2)

Replace stub service methods with real LMS API calls:

- Implement `LmsClient` in `services/lms_client.py` using `httpx`
- Map backend endpoints: `/health`, `/labs`, `/scores/{lab_id}`
- Add error handling: catch connection errors, return user-friendly messages
- Handlers call real API, format responses

Verification: `uv run bot.py --test "/health"` shows actual backend status.

## Phase 3: Intent-Based Natural Language Routing (Task 3)

Add LLM-powered intent recognition:

- Implement `LlmClient` in `services/llm_client.py`
- Define tools for each backend endpoint (function calling)
- Route plain text through LLM to determine intent
- Execute matched tool, format response
- Fallback to help message when intent unclear

Verification: `uv run bot.py --test "what labs are available"` returns lab list.

## Phase 4: Containerize and Deploy (Task 4)

Production deployment:

- Create `Dockerfile` for bot
- Add bot service to `docker-compose.yml`
- Configure environment variables on VM
- Run bot as background service
- Verify in Telegram

Verification: Bot responds to `/start` in Telegram app.

## Testing Strategy

Every feature follows the same loop:

1. Implement handler logic
2. Test with `--test` flag (fast, no Telegram needed)
3. Deploy and verify in Telegram

This ensures rapid iteration during development and confidence before deployment.
