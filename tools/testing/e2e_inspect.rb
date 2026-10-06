# frozen_string_literal: true

require 'json'
raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
raise 'Wrong Redmine version' unless [Redmine::VERSION::MAJOR, Redmine::VERSION::MINOR, Redmine::VERSION::TINY] == [7, 0, 2]
manifest = JSON.parse(File.read('/seed-state/fixtures.json'))
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
