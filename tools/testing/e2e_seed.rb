# frozen_string_literal: true

require 'json'
require 'securerandom'

raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
require_relative 'e2e_guard'
path = '/seed-state/fixtures.json'
def ensure_inherited_members(child, parent)
  raise 'Unowned inheritance fixture' unless child.identifier == 'mcp-e2e-child' && parent.identifier == 'mcp-e2e-parent' && child.parent_id == parent.id
  expected = MemberRole.where(member_id: parent.membership_ids).pluck(:id)
  observed = MemberRole.where(member_id: child.membership_ids).pluck(:inherited_from)
  return if (expected - observed).empty?

  child.inherit_members = false
  child.save!
  child.inherit_members = true
  child.save!
end

def ensure_fixture_journals(issue, user)
  raise 'Unowned journal fixture' unless issue.project.identifier == 'mcp-e2e-a' && issue.subject == 'E2E a' && user.login == 'mcp-e2e-a'
  { 'E2E initial note' => false, 'E2E private note' => true }.each do |notes, private_notes|
    journal = issue.journals.find_by(notes: notes) || Journal.new(journalized: issue, user: user, notes: notes)
    journal.private_notes = private_notes
    journal.save!
  end
end

if File.exist?(path)
  previous = JSON.parse(File.read(path))
  E2EGuard.manifest!(previous)
  raise 'Invalid existing ownership' unless previous['owner'] == 'prep-018' && previous['kind'] == ENV['REDMINE_TEST_MARKER']
  ensure_inherited_members(Project.find(previous['projects']['child']), Project.find(previous['projects']['parent']))
  issue = Issue.find(previous['issues']['a'])
  ensure_fixture_journals(issue, User.find(previous['users']['a']['id']))
  previous['journals'] = issue.journals.pluck(:id)
  File.write(path, JSON.pretty_generate(previous))
  load '/opt/testing/e2e_reporting_seed.rb'
  exit
end

Redmine::DefaultData::Loader.load('en') if Tracker.count.zero?
Setting.rest_api_enabled = '1'
permissions = %i[view_issues add_issues edit_issues copy_issues add_issue_notes edit_issue_notes set_notes_private view_private_notes manage_issue_relations view_issue_watchers add_issue_watchers delete_issue_watchers manage_files view_files view_time_entries log_time view_issue_categories manage_issue_categories view_project]
available = Redmine::AccessControl.permissions.map(&:name)
roles = {}
{
  'writer' => permissions,
  'reader' => %i[view_issues view_files view_time_entries],
  'own' => %i[view_issues edit_own_issues add_issue_notes edit_own_issue_notes],
  'tracker' => %i[view_issues edit_issues],
  'notes' => %i[view_issues add_issue_notes]
}.each do |name, grants|
  roles[name] = Role.find_by(name: "E2E #{name}") || Role.create!(name: "E2E #{name}", permissions: grants & available,
    issues_visibility: name == 'reader' ? 'default' : 'all', users_visibility: 'all', time_entries_visibility: 'all')
  roles[name].copy_workflow_rules(Role.find_by(name: 'Manager'))
end
trackers = Tracker.order(:id).to_a
raise 'Need contrasting trackers' unless trackers.size >= 2
roles['tracker'].set_permission_trackers(:edit_issues, [trackers.first.id]).save!

users = {}
%w[a b own tracker notes admin].each do |name|
  password = SecureRandom.hex(24)
  users[name] = User.find_by(login: "mcp-e2e-#{name}") || User.create!(login: "mcp-e2e-#{name}", firstname: 'E2E', lastname: name,
    mail: "mcp-e2e-#{name}@example.invalid", password: password, password_confirmation: password,
    admin: name == 'admin', status: User::STATUS_ACTIVE)
end
projects = {}
%w[a b own tracker public closed archived disabled parent child].each do |name|
  project = Project.find_by(identifier: "mcp-e2e-#{name}") || Project.create!(name: "E2E #{name}", identifier: "mcp-e2e-#{name}", is_public: name == 'public')
  project.enabled_module_names = %w[issue_tracking time_tracking files]
  project.trackers = trackers
  projects[name] = project
end
projects['child'].set_parent!(projects['parent'])
projects['child'].inherit_members = true
projects['child'].save!
memberships = {
  'a' => [['a','writer'],['b','reader'],['own','writer'],['tracker','writer'],['closed','writer'],['archived','writer'],['disabled','writer'],['parent','writer']],
  'b' => [['a','reader'],['b','writer']],
  'own' => [['own','own']], 'tracker' => [['tracker','tracker']], 'notes' => [['a','notes']]
}
memberships.each do |user_name, pairs|
  pairs.each do |project_name, role_name|
    Member.find_by(project: projects[project_name], user_id: users[user_name].id) || Member.create!(project: projects[project_name], principal: users[user_name], roles: [roles[role_name]])
  end
end
group = Group.find_by(lastname: 'E2E group') || Group.create!(lastname: 'E2E group')
group.users << users['b'] unless group.users.include?(users['b'])
Member.find_by(project: projects['parent'], user_id: group.id) || Member.create!(project: projects['parent'], principal: group, roles: [roles['reader']])
member = Member.find_by(project: projects['a'], user_id: users['a'].id)
member.roles << roles['notes'] unless member.roles.include?(roles['notes'])
ensure_inherited_members(projects['child'].reload, projects['parent'].reload)

issues = {}
%w[a b own tracker public closed archived disabled child].each do |name|
  issues[name] = Issue.find_by(project: projects[name], subject: "E2E #{name}") || Issue.create!(project: projects[name], tracker: trackers.first, author: users[name == 'own' ? 'own' : 'a'],
    subject: "E2E #{name}", status: IssueStatus.first, priority: IssuePriority.first)
end
issues['own_other'] = Issue.find_by(project: projects['own'], subject: 'E2E other author') || Issue.create!(project: projects['own'], tracker: trackers.first, author: users['a'], subject: 'E2E other author', status: IssueStatus.first, priority: IssuePriority.first)
issues['tracker_other'] = Issue.find_by(project: projects['tracker'], subject: 'E2E other tracker') || Issue.create!(project: projects['tracker'], tracker: trackers.last, author: users['a'], subject: 'E2E other tracker', status: IssueStatus.first, priority: IssuePriority.first)
issues['private'] = Issue.find_by(project: projects['a'], subject: 'E2E private') || Issue.create!(project: projects['a'], tracker: trackers.first, author: users['a'], subject: 'E2E private', is_private: true, status: IssueStatus.first, priority: IssuePriority.first)
ensure_fixture_journals(issues['a'].reload, users['a'])
TimeEntry.create!(project: projects['a'], issue: issues['a'], user: users['a'], author: users['a'], hours: 1.25, spent_on: Date.today, activity: TimeEntryActivity.first)
version = Version.create!(project: projects['a'], name: 'E2E version', status: 'open')
category = IssueCategory.create!(project: projects['a'], name: 'E2E category')
projects['closed'].close
projects['archived'].archive
projects['disabled'].enabled_module_names = %w[files]

File.write(path, JSON.pretty_generate({kind: ENV['REDMINE_TEST_MARKER'], owner: 'prep-018', version: E2EGuard::VERSION,
  users: users.transform_values { |user| {id: user.id, key: user.api_key} },
  roles: roles.transform_values(&:id), projects: projects.transform_values(&:id),
  issues: issues.transform_values(&:id), journals: issues['a'].journals.pluck(:id),
  tracker_ids: trackers.map(&:id), version_id: version.id, category_id: category.id,
  group_id: group.id, created_issues: [], attachments: [], relations: []}))
File.chmod(0600, path)
load '/opt/testing/e2e_reporting_seed.rb'
