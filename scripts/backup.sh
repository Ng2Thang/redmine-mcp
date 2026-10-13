#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
assert_environment
assert_redmine_version
snapshot="${1:-$(date +%Y%m%d-%H%M%S)}"
[[ "$snapshot" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$ ]] || { echo 'Invalid snapshot ID'; exit 1; }
compose stop mcp-server redmine
trap 'compose up -d --wait --wait-timeout 600 redmine mcp-server' EXIT
compose --profile tools run --build --rm -e "SNAPSHOT_ID=$snapshot" backup-restore backup
echo "Backup created in ${test_project}_backup_data at /$snapshot. Full restore validation is deferred."

