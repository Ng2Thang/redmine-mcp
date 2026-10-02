#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
assert_environment

snapshot_id="${1:?Usage: bash scripts/prepare-recovery-copy.sh SNAPSHOT_ID}"
[[ "$snapshot_id" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$ ]] || {
  echo 'Invalid snapshot ID' >&2
  exit 1
}

copy_root="$REPO_ROOT/.local/upgrades/$snapshot_id"
for guarded_path in "$REPO_ROOT/.local" "$REPO_ROOT/.local/upgrades" \
  "$copy_root" "$copy_root/snapshot"; do
  [[ ! -L "$guarded_path" ]] || {
    echo 'Refusing a symlinked isolated snapshot path' >&2
    exit 1
  }
done
[[ -f "$copy_root/snapshot/COMPLETE" && -f "$copy_root/candidate.env" ]] || {
  echo 'Missing completed isolated snapshot or environment' >&2
  exit 1
}
docker info >/dev/null 2>&1 || {
  echo 'Docker is unavailable' >&2
  exit 1
}
for target_volume in redmine-mcp-recovery-6-0-5_redmine_db_data \
  redmine-mcp-recovery-6-0-5_redmine_files; do
  if docker volume inspect "$target_volume" >/dev/null 2>&1; then
    echo 'Recovery volume already exists; inspect it before proceeding' >&2
    exit 1
  fi
done

export PREP005_SNAPSHOT_DIR="$(cygpath -m "$copy_root/snapshot")"
compose_args=(
  -p redmine-mcp-recovery-6-0-5
  --env-file ".local/upgrades/$snapshot_id/candidate.env"
  -f deploy/compose.redmine-6-0-5-recovery.yaml
  -f deploy/compose.redmine-7-0-2-restore.yaml
)

docker compose "${compose_args[@]}" up -d --wait --wait-timeout 600 postgres
docker compose "${compose_args[@]}" --profile ops run --rm restore-copy
echo 'Independent 6.0.5 recovery copy prepared; validation remains pending.'
