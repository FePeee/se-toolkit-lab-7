ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}astral/uv:python3.14-bookworm-slim

WORKDIR /app/bot

# Dependency layer first for better build caching.
COPY bot/pyproject.toml ./pyproject.toml
RUN uv sync --project . --no-dev

# Application code
COPY bot/ ./

CMD ["uv", "run", "bot.py"]