#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
assert_environment
assert_redmine_version
compose --profile tools run --build --rm \
  --entrypoint /app/.venv/bin/python seed -m tools.seed.history
