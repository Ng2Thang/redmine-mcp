#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
python scripts/local_env.py init
compose up -d --wait --wait-timeout 600 postgres redmine
bash scripts/seed.sh
compose up -d --build --wait --wait-timeout 180 mcp-server
echo 'Ready: Redmine localhost:3000 | MCP localhost:8000/mcp | PostgreSQL localhost:5433'

