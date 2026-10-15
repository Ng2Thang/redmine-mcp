#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
cd "$REPO_ROOT" || exit 1

if ! command -v uv >/dev/null 2>&1; then
  echo 'uv is required. Install uv, then run uv sync --frozen.' >&2
  exit 1
fi

status=0
uv run --frozen ruff check src/redmine_mcp || status=1
uv run --frozen ruff format --check src/redmine_mcp || status=1
uv run --frozen mypy src/redmine_mcp || status=1
uv run --frozen python scripts/check_architecture.py || status=1
exit "$status"
