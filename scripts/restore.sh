#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
assert_environment
assert_redmine_version
snapshot="${1:?Usage: bash scripts/restore.sh SNAPSHOT_ID}"
[[ "$snapshot" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$ ]] || { echo 'Invalid snapshot ID'; exit 1; }
compose stop mcp-server redmine
# Failure intentionally leaves applications stopped instead of serving a partial restore.
compose --profile tools run --build --rm -e "SNAPSHOT_ID=$snapshot" backup-restore restore
python scripts/local_env.py runtime
compose up -d --wait --wait-timeout 600 redmine mcp-server
echo 'Restore commands completed. Full restore validation is deferred.'

