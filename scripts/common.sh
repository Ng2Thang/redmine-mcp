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
assert_redmine_version() {
  local volume label
  for volume in redmine-mcp-test_redmine_db_data redmine-mcp-test_redmine_files; do
    label="$(docker volume inspect --format '{{ index .Labels "redmine-mcp.redmine-version" }}' "$volume" 2>/dev/null)" || {
      echo "Missing synthetic volume: $volume" >&2
      exit 1
    }
    [[ "$label" == '7.0.2' ]] || {
      echo "Synthetic volume is not marked for Redmine 7.0.2: $volume" >&2
      exit 1
    }
  done
}

