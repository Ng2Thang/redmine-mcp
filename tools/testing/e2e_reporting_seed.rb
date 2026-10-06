# frozen_string_literal: true

# Additive fixture for tasks 034/035; never changes existing role visibility.
require 'json'
raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
raise 'Wrong Redmine version' unless [Redmine::VERSION::MAJOR, Redmine::VERSION::MINOR, Redmine::VERSION::TINY] == [7, 0, 2]
path = '/seed-state/fixtures.json'
manifest = JSON.parse(File.read(path))
raise 'Wrong ownership' unless manifest['owner'] == 'prep-018' && manifest['kind'] == ENV['REDMINE_TEST_MARKER']
project = Project.find_by(identifier: 'mcp-e2e-reporting')
if project
  raise 'Unowned reporting project' unless manifest['projects']['reporting'] == project.id
else
  project = Project.create!(name: 'E2E reporting', identifier: 'mcp-e2e-reporting', is_public: false)
end
project.enabled_module_names = %w[issue_tracking time_tracking]
project.trackers = Tracker.order(:id).to_a
role = Role.find_by(name: 'E2E reporting own logs')
if role
  raise 'Unowned reporting role' unless manifest['roles']['reporting_own'] == role.id
else
  role = Role.create!(name: 'E2E reporting own logs', permissions: %i[view_time_entries log_time],
    time_entries_visibility: 'own', users_visibility: 'all')
end
{'a' => Role.find(manifest['roles']['writer']), 'own' => role}.each do |name, grant|
  user = User.find(manifest['users'][name]['id'])
  raise 'Unowned reporting user' unless user.login == "mcp-e2e-#{name}"
  Member.find_by(project: project, user_id: user.id) || Member.create!(project: project, principal: user, roles: [grant])
end
manifest['projects']['reporting'] = project.id
manifest['roles']['reporting_own'] = role.id
File.write(path, JSON.pretty_generate(manifest))
File.chmod(0600, path)
