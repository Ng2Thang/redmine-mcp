# frozen_string_literal: true

require 'json'
raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
require_relative 'e2e_guard'
manifest = JSON.parse(File.read('/seed-state/fixtures.json'))
E2EGuard.manifest!(manifest)
raise 'Wrong ownership' unless manifest['owner'] == 'prep-018'
projects = manifest['projects'].to_h do |name, id|
  project = Project.find(id)
  raise 'Unowned project' unless project.identifier == "mcp-e2e-#{name}"
  [id, {identifier: project.identifier, status: project.status}]
end
issues = manifest['issues'].values.to_h do |id|
  issue = Issue.find(id)
  raise 'Unowned issue' unless projects.key?(issue.project_id)
  [id, {id: id, subject: issue.subject, project: {id: issue.project_id}}]
end
puts JSON.generate({projects: projects, issues: issues})
