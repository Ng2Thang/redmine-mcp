# frozen_string_literal: true

require 'json'
require 'securerandom'
raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
require_relative 'e2e_guard'
path = '/e2e-state/tool042-fixtures.json'

case ARGV.first
when 'setup'
  raise 'Unreconciled TOOL-042 fixtures' if File.exist?(path)
  prefix = "mcp-e2e-tool042-#{SecureRandom.hex(6)}"
  ledger = {owner: 'tool-042', version: E2EGuard::VERSION, project: ENV['REDMINE_E2E_PROJECT'], prefix: prefix, project_id: nil, users: {}, role_ids: [], activities: {},
            policies: {future: Setting.timelog_accept_future_dates?,
                       closed: !Setting.respond_to?(:timelog_accept_closed_issues?) || Setting.timelog_accept_closed_issues?,
                       daily_max: Setting.timelog_max_hours_per_day.to_f, required: Setting.timelog_required_fields},
            closed_status_id: IssueStatus.where(is_closed: true).first&.id}
  File.write(path, JSON.generate(ledger))
  File.chmod(0600, path)
  begin
    ActiveRecord::Base.transaction do
    project = Project.create!(name: 'TOOL-042 disposable time updates', identifier: prefix, is_public: false)
    project.enabled_module_names = %w[issue_tracking time_tracking]
    ledger[:project_id] = project.id
    %w[active inactive].each do |name|
      activity = TimeEntryActivity.create!(name: "TOOL042 #{name}", project: project,
                                          active: name == 'active', is_default: false)
      ledger[:activities][name] = activity.id
    end
    grants = {
      'all' => %i[view_issues view_time_entries log_time edit_time_entries],
      'own' => %i[view_issues view_time_entries log_time edit_own_time_entries],
      'denied' => %i[view_issues view_time_entries log_time],
      'no_view' => %i[view_issues log_time edit_time_entries],
      'read_only' => %i[view_issues view_time_entries]
    }
    grants.each do |name, permissions|
      role = Role.create!(name: "#{prefix}-#{name}", permissions: permissions,
                          issues_visibility: 'all', time_entries_visibility: 'all', users_visibility: 'all')
      ledger[:role_ids] << role.id
      user = User.new(login: "#{prefix}-#{name}", firstname: 'TOOL042', lastname: name,
                      mail: "#{prefix}-#{name}@example.invalid", admin: false)
      user.password = SecureRandom.hex(24)
      user.password_confirmation = user.password
      user.save!
      Member.create!(project: project, principal: user, roles: [role])
      ledger[:users][name] = {id: user.id, key: user.api_key}
    end
    project.trackers = Tracker.all
    File.write(path, JSON.generate(ledger))
    File.chmod(0600, path)
    end
  rescue StandardError
    File.delete(path) if File.exist?(path)
    raise
  end
  puts JSON.generate(ledger)
when 'cleanup'
  ledger = JSON.parse(File.read(path))
  E2EGuard.manifest!(ledger, 'tool-042')
  raise 'Wrong TOOL-042 owner' unless ledger['owner'] == 'tool-042' && ledger['prefix'].start_with?('mcp-e2e-tool042-')
  project = Project.find_by(id: ledger['project_id'])
  if project
    raise 'Unowned project' unless project.identifier == ledger['prefix']
    project.destroy!
  end
  ledger['activities'].each_value do |id|
    activity = TimeEntryActivity.find_by(id: id)
    next unless activity
    raise 'Unowned activity' unless activity.project_id == ledger['project_id'] && activity.name.start_with?('TOOL042 ')
    activity.destroy!
  end
  ledger['users'].each do |name, values|
    user = User.find_by(id: values['id'])
    next unless user
    raise 'Unowned user' unless user.login == "#{ledger['prefix']}-#{name}" && !user.admin?
    raise 'Unexpected membership' if user.members.any?
    user.destroy!
  end
  ledger['role_ids'].each do |id|
    role = Role.find_by(id: id)
    next unless role
    raise 'Unowned role' unless role.name.start_with?(ledger['prefix'] + '-') && role.members.empty?
    role.destroy!
  end
  remaining = {projects: Project.where(id: ledger['project_id']).count,
               entries: TimeEntry.where(project_id: ledger['project_id']).count,
               users: User.where(id: ledger['users'].values.map { |row| row['id'] }).count,
               roles: Role.where(id: ledger['role_ids']).count,
               activities: TimeEntryActivity.where(id: ledger['activities'].values).count}
  raise 'Incomplete TOOL-042 cleanup' unless remaining.values.all?(&:zero?)
  File.delete(path)
  evidence = {owner: 'tool-042', version: E2EGuard::VERSION, cleanup: 'passed', remaining: remaining,
              observed_policies: ledger['policies']}
  File.write('/e2e-state/tool042-last-cleanup.json', JSON.generate(evidence))
  puts JSON.generate(evidence)
else
  raise 'Expected setup or cleanup'
end
