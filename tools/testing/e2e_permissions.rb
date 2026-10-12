# frozen_string_literal: true

require 'json'
raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
require_relative 'e2e_guard'
manifest = JSON.parse(File.read('/seed-state/fixtures.json'))
E2EGuard.manifest!(manifest)
raise 'Wrong owner' unless manifest['owner'] == 'prep-018'
role = Role.find(manifest['roles']['writer'])
raise 'Unowned role' unless role.name == 'E2E writer' && role.members.all? { |member| member.project.identifier.start_with?('mcp-e2e-') }
snapshot = '/seed-state/permission-snapshot.json'
case ARGV.first
when 'revoke'
  raise 'Outstanding permission reconciliation' if File.exist?(snapshot)
  File.write(snapshot, JSON.generate({role_id: role.id, permissions: role.permissions}))
  role.permissions = []
  role.save!
when 'restore'
  data = JSON.parse(File.read(snapshot))
  raise 'Wrong snapshot role' unless data['role_id'] == role.id
  role.permissions = data['permissions']
  role.save!
  File.delete(snapshot)
else
  raise 'Unsupported fixture action'
end
puts 'Owned permission fixture updated'
