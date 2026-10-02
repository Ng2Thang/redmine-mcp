#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
assert_environment

snapshot_id="${1:?Usage: bash scripts/prepare-upgrade-copy.sh SNAPSHOT_ID}"
[[ "$snapshot_id" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$ ]] || {
  echo 'Invalid snapshot ID' >&2
  exit 1
}

source_snapshot="$REPO_ROOT/.local/backups/$snapshot_id"
copy_root="$REPO_ROOT/.local/upgrades/$snapshot_id"
for guarded_path in "$REPO_ROOT/.local" "$REPO_ROOT/.local/backups" \
  "$REPO_ROOT/.local/upgrades" "$source_snapshot"; do
  [[ ! -L "$guarded_path" ]] || {
    echo 'Refusing a symlinked source or destination path' >&2
    exit 1
  }
done
[[ -f "$source_snapshot/COMPLETE" && -f "$source_snapshot/environment.json" ]] || {
  echo 'Missing completed source snapshot' >&2
  exit 1
}
[[ ! -e "$copy_root" ]] || {
  echo 'Isolated copy already exists; choose an unused snapshot ID' >&2
  exit 1
}
docker info >/dev/null 2>&1 || {
  echo 'Docker is unavailable' >&2
  exit 1
}
for target_volume in redmine-mcp-7-0-2_redmine_db_data redmine-mcp-7-0-2_redmine_files; do
  if docker volume inspect "$target_volume" >/dev/null 2>&1; then
    echo 'Isolated target volume already exists; inspect it before proceeding' >&2
    exit 1
  fi
done

mkdir -p -- "$REPO_ROOT/.local/upgrades"
mkdir -m 700 -- "$copy_root"
cp -a -- "$source_snapshot" "$copy_root/snapshot"
cp -- "$REPO_ROOT/.env" "$copy_root/candidate.env"
chmod 600 -- "$copy_root/candidate.env"

# Docker Compose receives a Windows-friendly host path without Git Bash argument rewriting.
export PREP005_SNAPSHOT_DIR="$(cygpath -m "$copy_root/snapshot")"
compose_args=(
  -p redmine-mcp-7-0-2
  --env-file ".local/upgrades/$snapshot_id/candidate.env"
  -f deploy/compose.redmine-7-0-2.yaml
  -f deploy/compose.redmine-7-0-2-restore.yaml
)

docker compose "${compose_args[@]}" up -d --wait --wait-timeout 600 postgres
docker compose "${compose_args[@]}" --profile ops run --rm restore-copy
echo "Isolated pre-upgrade copy prepared in .local/upgrades/$snapshot_id."
