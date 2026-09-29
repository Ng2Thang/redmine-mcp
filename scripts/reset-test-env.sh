#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
assert_environment
[[ "${1:-}" == "--confirm-reset" ]] || {
  echo 'Deletes synthetic DB and attachments. Usage: bash scripts/reset-test-env.sh --confirm-reset'
  exit 1
}
compose down --volumes --remove-orphans
python scripts/local_env.py reset-state
bash scripts/dev-up.sh

