#!/usr/bin/env bash
usage() {
  echo 'Usage: bash scripts/seed.sh [base|history|all]'
  echo 'base (default): Rails bootstrap, then 150-issue baseline.'
  echo 'history: Add or resume 300 issues and 900 time entries after a complete base.'
  echo 'all: Bootstrap and baseline, then add or resume history.'
}
if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi
mode="${1:-base}"
case "$mode" in
  base|history|all) ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

source "$(dirname -- "$0")/common.sh"
# Bootstrap needs Rails internals; dataset creation lives in tools/seed/generate.py.
# History deliberately skips bootstrap and requires an already completed baseline.
if [[ "$mode" != 'history' ]]; then
  python scripts/local_env.py init
  assert_redmine_version
  compose exec -T redmine bundle exec rails runner /opt/seed/bootstrap.rb
fi
assert_environment
assert_redmine_version
compose --profile tools run --build --rm seed "$mode"
if [[ "$mode" != 'history' ]]; then
  python scripts/local_env.py runtime
fi
echo 'Seed ready; use a personal Redmine API key in the request header.'

