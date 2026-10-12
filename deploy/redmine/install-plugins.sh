#!/usr/bin/env bash
set -euo pipefail

# Keep host sources read-only; Redmine owns its container-local plugin copies.
cd /usr/src/redmine
mkdir -p plugins
for plugin_source in /opt/redmine/plugins/*; do
  [[ -d "$plugin_source" ]] || continue
  plugin_name="$(basename -- "$plugin_source")"
  if [[ ! -f "$plugin_source/init.rb" ]]; then
    echo "Plugin $plugin_name is missing init.rb" >&2
    exit 1
  fi
  echo "Installing Redmine plugin: $plugin_name"
  mkdir -p "plugins/$plugin_name"
  cp -R "$plugin_source/." "plugins/$plugin_name/"
done
chown -R redmine:redmine plugins

# Apply the installation options shared by Agile and Tags using Bundler config,
# which also works with Bundler versions that removed the corresponding CLI flags.
gosu redmine bundle config set --local without 'development test'
gosu redmine bundle config set --local deployment false
export RAILS_ENV=production
export REDMINE_PLUGINS_MIGRATE=1

# The official entrypoint configures the database, installs missing gems,
# drops privileges, and runs core and plugin migrations before starting Rails.
# It runs bundle check || bundle install, then redmine:plugins:migrate for all
# copied plugins, including redmine_agile, redmineup_tags, and redmine_work_time.
exec /docker-entrypoint.sh "$@"
