#!/usr/bin/env bash
set -euo pipefail
if [[ $# -gt 1 ]]; then
  echo 'Usage: bash scripts/dev-up.sh [7.0.2|6.0.1]' >&2
  exit 2
fi
version="${1:-7.0.2}"
case "$version" in
  7.0.2|6.0.1) ;;
  -h|--help) echo 'Usage: bash scripts/dev-up.sh [7.0.2|6.0.1]'; exit 0 ;;
  *) echo 'Usage: bash scripts/dev-up.sh [7.0.2|6.0.1]' >&2; exit 2 ;;
esac
export REDMINE_TEST_VERSION="$version"
source "$(dirname -- "$0")/common.sh"
project=redmine-mcp-test
redmine_port=3002
postgres_port=5433
if [[ "$version" == '6.0.1' ]]; then
  project=redmine-mcp-test-6-0-1
  redmine_port=3001
  postgres_port=5436
fi
python scripts/local_env.py init
for volume in "${project}_redmine_db_data" "${project}_redmine_files"; do
  if docker volume inspect "$volume" >/dev/null 2>&1; then
    label="$(docker volume inspect --format '{{ index .Labels "redmine-mcp.redmine-version" }}' "$volume")"
    [[ "$label" == "$version" ]] || {
      echo "Existing Redmine volume is not marked for $version: $volume" >&2
      exit 1
    }
  fi
done
compose up -d --wait --wait-timeout 600 postgres redmine
bash scripts/seed.sh all
compose up -d --build --wait --wait-timeout 180 mcp-server
reader_port=8000
[[ "$version" == '6.0.1' ]] && reader_port=8002
echo "Ready: Redmine localhost:$redmine_port | MCP localhost:${MCP_HOST_PORT:-$reader_port}/mcp | PostgreSQL localhost:$postgres_port"

