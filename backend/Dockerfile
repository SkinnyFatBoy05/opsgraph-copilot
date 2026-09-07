FROM ghcr.io/astral-sh/uv:0.8.11-python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --extra aws --no-install-project

COPY backend/src ./src
COPY data /app/data
COPY evaluation/reports/deterministic /app/evaluation/reports/deterministic
RUN uv sync --frozen --no-dev --extra aws

RUN useradd --system --uid 10001 --create-home opsgraph
USER 10001:10001

EXPOSE 8000
CMD [".venv/bin/uvicorn", "opsgraph.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--limit-concurrency", "32", "--timeout-keep-alive", "5"]
