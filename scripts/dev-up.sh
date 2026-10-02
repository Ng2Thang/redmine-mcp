#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
python scripts/local_env.py init
for volume in redmine-mcp-test_redmine_db_data redmine-mcp-test_redmine_files; do
  if docker volume inspect "$volume" >/dev/null 2>&1; then
    label="$(docker volume inspect --format '{{ index .Labels "redmine-mcp.redmine-version" }}' "$volume")"
    [[ "$label" == '7.0.2' ]] || {
      echo "Existing Redmine volume is not marked for 7.0.2: $volume" >&2
      exit 1
    }
  fi
done
compose up -d --wait --wait-timeout 600 postgres redmine
bash scripts/seed.sh
compose up -d --build --wait --wait-timeout 180 mcp-server
echo 'Ready: Redmine localhost:3000 | MCP localhost:8000/mcp | PostgreSQL localhost:5433'

