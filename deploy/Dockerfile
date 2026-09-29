FROM python:3.13.3-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.20 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev && useradd --uid 10001 --create-home app
USER app
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "redmine_mcp.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

