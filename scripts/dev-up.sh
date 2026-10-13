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
redmine_port=3002
postgres_port=5433
reader_port=8000
if [[ "$version" == '6.0.1' ]]; then
  redmine_port=3001
  postgres_port=5436
  reader_port=8002
fi
python scripts/local_env.py preflight
echo "Starting Redmine $version using deploy/compose.test.${version}.yaml"
compose up -d --wait --wait-timeout 600 postgres redmine
bash scripts/seed.sh all
compose up -d --build --wait --wait-timeout 180 mcp-server
echo "Ready: Redmine $version localhost:$redmine_port | MCP localhost:$reader_port/mcp | PostgreSQL localhost:$postgres_port"

