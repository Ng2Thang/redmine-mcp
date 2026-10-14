# frozen_string_literal: true

# G05-only records. No adoption by name and no changes to existing roles or settings.
require 'json'
require 'securerandom'
require 'tempfile'
require_relative 'e2e_guard'
path = '/e2e-state/g05-fixtures.json'

def save_ledger(path, data)
  File.write(path, JSON.generate(data))
  File.chmod(0600, path)
end

def owned(data)
  E2EGuard.manifest!(data, 'g05')
  prefix = data.fetch('prefix')
  raise 'Invalid G05 prefix' unless prefix.match?(/\Amcp-e2e-g05-[0-9a-f]{12}\z/)
  data.fetch('projects').each do |name, id|
    project = Project.find(id)
    raise 'Foreign G05 project' unless project.identifier == "#{prefix}-#{name}"
    raise 'Foreign G05 descendant' unless (project.self_and_descendants.pluck(:id) - data['projects'].values).empty?
  end
  data.fetch('users').each do |name, row|
    user = User.find_by(id: row['id'])
    next unless user
    raise 'Foreign G05 user' unless user.login == "#{prefix}-#{name}" && user.admin? == (name == 'admin')
    raise 'Foreign G05 membership' unless (user.members.pluck(:project_id) - data['projects'].values).empty?
  end
  data.fetch('roles').each do |name, id|
    role = Role.find(id)
    raise 'Foreign G05 role' unless role.name == "#{prefix}-#{name}"
    raise 'Foreign role membership' unless (role.members.pluck(:project_id) - data['projects'].values).empty?
  end
end

case ARGV.first
when 'setup'
  raise 'Unreconciled G05 fixtures' if File.exist?(path)
  prefix = "mcp-e2e-g05-#{SecureRandom.hex(6)}"
  data = {owner: 'g05', version: E2EGuard::VERSION, project: ENV['REDMINE_E2E_PROJECT'], prefix: prefix,
          projects: {}, roles: {}, users: {}, issues: {}, activities: {}, tags: [prefix + '-a', prefix + '-b'],
          activity_defaults_before: TimeEntryActivity.order(:id).pluck(:id, :is_default),
          policies: {required: Setting.timelog_required_fields, future: Setting.timelog_accept_future_dates?,
                     closed_supported: Setting.respond_to?(:timelog_accept_closed_issues?),
                     closed: !Setting.respond_to?(:timelog_accept_closed_issues?) || Setting.timelog_accept_closed_issues?,
                     cross_project: Setting.cross_project_issue_relations?},
          plugins: Redmine::Plugin.all.map { |p| {id: p.id, version: p.version} }}
  save_ledger(path, data)
  begin
    ActiveRecord::Base.transaction do
      Redmine::DefaultData::Loader.load('en') if Tracker.count.zero?
      grants = {
        'writer' => %i[view_issues add_issues edit_issues add_issue_notes edit_issue_notes edit_own_issue_notes set_notes_private view_private_notes manage_issue_relations view_issue_watchers add_issue_watchers delete_issue_watchers manage_files view_files view_time_entries log_time edit_time_entries],
        'reader' => %i[view_issues view_files view_time_entries],
        'own' => %i[view_issues add_issue_notes edit_own_issue_notes],
        'watch_view' => %i[view_issues view_issue_watchers],
        'watch_mutate' => %i[view_issues add_issue_watchers delete_issue_watchers]
      }
      available = Redmine::AccessControl.permissions.map(&:name)
      roles = grants.to_h do |name, permissions|
        role = Role.create!(name: "#{prefix}-#{name}", permissions: permissions & available,
                            issues_visibility: name == 'reader' ? 'default' : 'all', users_visibility: 'all', time_entries_visibility: 'all')
        role.copy_workflow_rules(Role.find_by(name: 'Manager'))
        data[:roles][name] = role.id
        [name, role]
      end
      projects = %w[parent child other].to_h do |name|
        project = Project.create!(name: "G05 #{name}", identifier: "#{prefix}-#{name}", is_public: false)
        project.enabled_module_names = %w[issue_tracking time_tracking files]
        project.trackers = Tracker.all
        data[:projects][name] = project.id
        [name, project]
      end
      projects['child'].set_parent!(projects['parent'])
      projects['child'].update!(inherit_members: true)
      users = %w[writer reader own watch_view watch_mutate locked deleted rotated admin].to_h do |name|
        password = SecureRandom.hex(24)
        user = User.create!(login: "#{prefix}-#{name}", firstname: 'G05', lastname: name,
                            mail: "#{prefix}-#{name}@example.invalid", password: password,
                            password_confirmation: password, admin: name == 'admin')
        data[:users][name] = {id: user.id, key: user.api_key}
        unless name == 'admin'
          role = roles.fetch(name, roles['reader'])
          Member.create!(project: projects['parent'], principal: user, roles: [role])
          Member.create!(project: projects['other'], principal: user, roles: [role]) if name == 'writer'
        end
        [name, user]
      end
      projects['child'].reload.update!(inherit_members: false)
      projects['child'].reload.update!(inherit_members: true)
      raise 'G05 child inheritance not established' unless projects['child'].reload.members.exists?(user_id: users['reader'].id)
      %w[a b ab private child other].each do |name|
        project = projects.fetch(name, projects['parent'])
        issue = Issue.create!(project: project, tracker: Tracker.first, author: users['writer'],
                              subject: "G05 #{name}", status: IssueStatus.first, priority: IssuePriority.first, is_private: name == 'private')
        raise 'Native issue tag plugin required; G05 is not accepted without it' unless issue.respond_to?(:tag_list=)
        issue.reload
        issue.tag_list = name == 'b' ? [data[:tags][1]] : name == 'a' ? [data[:tags][0]] : data[:tags]
        issue.save!
        data[:issues][name] = issue.id
      end
      target = Issue.find(data[:issues]['a'])
      data[:journals] = %w[own writer].to_h do |name|
        journal = Journal.create!(journalized: target, user: users[name], notes: "G05 #{name} control")
        [name, journal.id]
      end
      version = Version.create!(project: projects['parent'], name: "#{prefix} version", status: 'open')
      data[:version_id] = version.id
      %w[active default inactive].each do |name|
        # Enumeration#check_default clears defaults across every project. Use the
        # owned writer role's native default instead of changing any shared flag.
        activity = TimeEntryActivity.create!(project: projects['parent'], name: "G05 #{prefix[-12, 12]} #{name}", active: name != 'inactive', is_default: false)
        roles['writer'].update!(default_time_entry_activity_id: activity.id) if name == 'default'
        data[:activities][name] = activity.id
      end
      protected_ids = data[:activity_defaults_before].map(&:first)
      raise 'Unrelated activity defaults changed during setup' unless TimeEntryActivity.where(id: protected_ids).order(:id).pluck(:id, :is_default) == data[:activity_defaults_before]
      closed = Issue.create!(project: projects['parent'], tracker: Tracker.first, author: users['writer'],
                             subject: 'G05 closed', status: IssueStatus.where(is_closed: true).first!, priority: IssuePriority.first)
      data[:issues]['closed'] = closed.id
      data[:today] = Date.today.iso8601
      save_ledger(path, data)
    end
  rescue StandardError
    File.delete(path) if File.exist?(path)
    raise
  end
  puts JSON.generate(data)
when 'attachments'
  data = JSON.parse(File.read(path)); owned(data)
  result = {}
  ActiveRecord::Base.transaction do
    {'issue' => Issue.find(data['issues']['a']), 'version' => Version.find(data['version_id'])}.each do |name, container|
      result[name] = %w[target control].to_h do |kind|
        tempfile = Tempfile.new(['g05', '.txt'])
        begin
          tempfile.write("G05 #{kind} bytes"); tempfile.rewind
          attachment = Attachment.create!(container: container, author_id: data['users']['writer']['id'],
                                          file: tempfile, filename: "#{data['prefix']}-#{kind}.txt", description: 'G05 original')
          [kind, attachment.id]
        ensure
          tempfile.close!
        end
      end
    end
  end
  data['attachment_ids'] = Array(data['attachment_ids']) + result.values.flat_map(&:values)
  save_ledger(path, data)
  puts JSON.generate(result)
when 'lock', 'delete', 'rotate'
  data = JSON.parse(File.read(path)); owned(data)
  action = ARGV.first
  name = {'lock' => 'locked', 'delete' => 'deleted', 'rotate' => 'rotated'}.fetch(action)
  user = User.find(data['users'][name]['id'])
  raise 'Identity fixture must be ordinary' if user.admin?
  if action == 'lock'
    user.update!(status: User::STATUS_LOCKED)
  elsif action == 'delete'
    user.destroy!
  else
    user.api_token.destroy!
    puts JSON.generate({key: user.reload.api_key})
    exit
  end
  puts JSON.generate({action: action, ordinary: true})
when 'cleanup'
  data = JSON.parse(File.read(path)); owned(data)
  projects = Project.where(id: data['projects'].values).order(lft: :desc).to_a
  projects.each(&:destroy!)
  data['users'].each_value { |row| User.find_by(id: row['id'])&.destroy! }
  data['roles'].each_value { |id| Role.find(id).destroy! }
  protected_ids = data.fetch('activity_defaults_before').map(&:first)
  raise 'Unrelated activity defaults changed during G05' unless TimeEntryActivity.where(id: protected_ids).order(:id).pluck(:id, :is_default) == data['activity_defaults_before']
  remaining = {projects: Project.where(id: data['projects'].values).count,
               users: User.where(id: data['users'].values.map { |row| row['id'] }).count,
               roles: Role.where(id: data['roles'].values).count,
               issues: Issue.where(project_id: data['projects'].values).count,
               entries: TimeEntry.where(project_id: data['projects'].values).count,
               versions: Version.where(project_id: data['projects'].values).count,
               attachments: Attachment.where(id: Array(data['attachment_ids'])).count,
               journals: Journal.where(id: data['journals'].values).count,
               activities: TimeEntryActivity.where(project_id: data['projects'].values).count}
  raise 'G05 cleanup incomplete' unless remaining.values.all?(&:zero?)
  File.delete(path)
  evidence = {owner: 'g05', version: E2EGuard::VERSION, project: ENV['REDMINE_E2E_PROJECT'], cleanup: 'passed', remaining: remaining, shared_activity_defaults_unchanged: true}
  save_ledger('/e2e-state/g05-last-cleanup.json', evidence)
  puts JSON.generate(evidence)
else
  raise 'Expected G05 setup, attachments, lock, delete, rotate or cleanup'
end
