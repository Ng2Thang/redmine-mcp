#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
assert_environment
assert_redmine_version
[[ "${1:-}" == "--confirm-reset" ]] || {
  echo 'Deletes synthetic DB and attachments. Usage: bash scripts/reset-test-env.sh --confirm-reset'
  exit 1
}
compose down --remove-orphans
for name in redmine_db_data redmine_files seed_state e2e_state; do
  volume="${test_project}_${name}"
  if docker volume inspect "$volume" >/dev/null 2>&1; then
    docker volume rm "$volume"
  fi
done
bash scripts/dev-up.sh "$test_version"

