#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
python scripts/local_env.py init
assert_redmine_version
compose exec -T redmine bundle exec rails runner /opt/seed/bootstrap.rb
assert_environment
compose --profile tools run --build --rm seed
python scripts/local_env.py runtime
echo 'Seed ready; use a personal Redmine API key in the request header.'

