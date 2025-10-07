FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY uv.lock pyproject.toml /app/

RUN uv sync --no-dev

COPY . /app

CMD uv run python -m app.main
