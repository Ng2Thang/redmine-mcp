# frozen_string_literal: true

# Disposable prep-020 fixtures; never change existing roles, memberships or project settings.
require 'json'
require 'fileutils'
raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
require_relative 'e2e_guard'
base = JSON.parse(File.read('/seed-state/fixtures.json'))
E2EGuard.manifest!(base)
raise 'Wrong owner' unless base['owner'] == 'prep-018'
action, run = ARGV
raise 'Invalid run identifier' unless run&.match?(/\A[0-9a-f]{32}\z/)
prefix = "mcp-e2e-prep020-#{run}"
role_prefix = "prep020 #{run} "
directory = "/seed-state/prep-020/#{run}"
FileUtils.mkdir_p(directory)
path = "#{directory}/fixture.json"

case action
when 'prepare'
  raise 'Fixture already exists' if File.exist?(path)
  writer = Role.find(base['roles']['writer'])
  raise 'Unexpected base role' unless writer.name == 'E2E writer'
  roles, projects = {}, {}
  ActiveRecord::Base.transaction do
    %w[read other protected].each do |name|
      roles[name] = Role.create!(name: role_prefix + name, permissions: [:view_issues], assignable: true, users_visibility: 'all')
    end
    roles['manager'] = Role.create!(name: role_prefix + 'manager', permissions: writer.permissions | %i[manage_members manage_versions], all_roles_managed: false, users_visibility: 'all', issues_visibility: 'all')
    roles['manager'].managed_roles = [roles['read'], roles['other']]
    roles['manager'].copy_workflow_rules(writer)
    roles['version_only'] = Role.create!(name: role_prefix + 'version_only', permissions: [:manage_versions], users_visibility: 'all')
    %w[parent child public version_only].each do |name|
      projects[name] = Project.create!(name: "Prep020 #{name}", identifier: "#{prefix}-#{name}", is_public: name == 'public')
      projects[name].enabled_module_names = %w[issue_tracking time_tracking files]
      projects[name].trackers = Tracker.order(:id).to_a
    end
    projects['child'].set_parent!(projects['parent'])
    projects['child'].update!(inherit_members: true)
    projects['parent'].reload
    %w[parent public].each do |name|
      Member.create!(project: projects[name], user_id: base['users']['a']['id'], roles: [roles['manager']])
    end
    Member.create!(project: projects['parent'], user_id: base['users']['b']['id'], roles: [roles['read']])
    Member.create!(project: projects['parent'], user_id: base['users']['notes']['id'], roles: [roles['protected'], roles['read']])
    Member.create!(project: projects['parent'], user_id: base['group_id'], roles: [roles['read']])
    Member.create!(project: projects['version_only'], user_id: base['users']['own']['id'], roles: [roles['version_only']])
  end
  data = {owner: 'prep-020', run: run, prefix: prefix, roles: roles.transform_values(&:id), projects: projects.transform_values(&:id)}
  File.write(path, JSON.pretty_generate(data))
  File.chmod(0600, path)
  puts JSON.generate(data)
when 'assign'
  data = JSON.parse(File.read(path))
  project = Project.find(data['projects']['parent'])
  raise 'Unowned assignment project' unless project.identifier == "#{prefix}-parent"
  user = User.find(base['users']['own']['id'])
  raise 'Assignment target is not a member' unless project.members.exists?(user_id: user.id)
  project.update!(default_assigned_to_id: user.id)
  category = IssueCategory.create!(project: project, name: "Prep020 #{run}", assigned_to: user)
  issue = Issue.create!(project: project, subject: "Prep020 #{run}", tracker: Tracker.first, author_id: base['users']['a']['id'], assigned_to: user, status: IssueStatus.first, priority: IssuePriority.first)
  data['category_id'], data['issue_id'] = category.id, issue.id
  File.write(path, JSON.pretty_generate(data))
  puts JSON.generate(data)
when 'inspect'
  data = JSON.parse(File.read(path))
  raise 'Wrong fixture owner' unless data['owner'] == 'prep-020' && data['run'] == run
  observed = data['projects'].to_h do |name, id|
    project = Project.find(id)
    raise 'Unowned inspection project' unless project.identifier == "#{prefix}-#{name}"
    [name, {default_assigned_to_id: project.default_assigned_to_id, members: project.memberships.map { |member| {id: member.id, user_id: member.user_id, roles: member.member_roles.map { |row| {id: row.role_id, inherited: row.inherited_from.present?} }} }}]
  end
  puts JSON.generate({projects: observed, category_assigned_to_id: data['category_id'] && IssueCategory.find(data['category_id']).assigned_to_id, issue_assigned_to_id: data['issue_id'] && Issue.find(data['issue_id']).assigned_to_id})
when 'cleanup'
  # Prefix ownership also permits cleanup if preparation failed before writing its manifest.
  projects = Project.where('identifier LIKE ?', "#{prefix}-%").to_a
  raise 'Unexpected project tree' unless projects.all? { |project| project.children.all? { |child| child.identifier.start_with?(prefix + '-') } }
  projects.sort_by { |project| -project.lft }.each(&:destroy!)
  roles = Role.where('name LIKE ?', role_prefix + '%').to_a
  raise 'Task role still used outside disposable projects' unless roles.all? { |role| role.members.empty? }
  roles.each(&:destroy!)
  raise 'Disposable projects remain' if Project.where('identifier LIKE ?', "#{prefix}-%").exists?
  raise 'Disposable roles remain' if Role.where('name LIKE ?', role_prefix + '%').exists?
  puts JSON.generate({owner: 'prep-020', cleanup: 'passed', projects_removed: projects.size, roles_removed: roles.size, existing_grants_changed: false})
else
  raise 'Unsupported fixture action'
end
