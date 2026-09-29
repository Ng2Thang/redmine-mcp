#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
# Prevent Git Bash rewriting Linux paths passed to Docker.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'
compose() {
  docker compose -p redmine-mcp-test --env-file .env \
    -f deploy/compose.yaml -f deploy/compose.test.yaml "$@"
}
assert_environment() {
  python scripts/local_env.py assert
}

