#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
# Prevent Git Bash rewriting Linux paths passed to Docker.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'
test_version="${REDMINE_TEST_VERSION:-7.0.2}"
case "$test_version" in
  7.0.2) test_project=redmine-mcp-dev-7-0-2 ;;
  6.0.1) test_project=redmine-mcp-dev-6-0-1 ;;
  *) echo 'Unsupported synthetic Redmine version' >&2; exit 2 ;;
esac
export REDMINE_TEST_VERSION="$test_version"
compose() {
  python scripts/local_env.py compose "$@"
}
assert_environment() {
  python scripts/local_env.py assert
}
assert_redmine_version() {
  local volume label
  for volume in "${test_project}_redmine_db_data" "${test_project}_redmine_files"; do
    label="$(docker volume inspect --format '{{ index .Labels "redmine-mcp.redmine-version" }}' "$volume" 2>/dev/null)" || {
      echo "Missing synthetic volume: $volume" >&2
      exit 1
    }
    [[ "$label" == "$test_version" ]] || {
      echo "Synthetic volume is not marked for Redmine $test_version: $volume" >&2
      exit 1
    }
  done
}

