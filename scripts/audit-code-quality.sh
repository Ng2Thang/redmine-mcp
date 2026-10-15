#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || exit 2
cd "$REPO_ROOT" || exit 2

if ! command -v uv >/dev/null 2>&1; then
  echo 'uv is required. Install uv, then run uv sync --frozen --group audit.' >&2
  exit 2
fi

# The dedicated group keeps audit dependencies out of the runtime deployment.
uv run --frozen --group audit python scripts/code_quality_audit.py "$@"
