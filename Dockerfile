FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH=".venv/bin:$PATH"

COPY uv.lock pyproject.toml /app/

RUN uv sync --frozen --no-install-project --no-dev

COPY . /app

RUN uv sync --frozen

CMD uv run python3 -m app.bot.main
