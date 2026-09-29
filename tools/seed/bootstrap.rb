require 'json'
require 'fileutils'
abort 'Not the synthetic environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1'
state = '/seed-state'
FileUtils.mkdir_p(state)
marker = File.join(state, 'environment.json')
if File.exist?(marker)
  abort 'Invalid environment marker' unless JSON.parse(File.read(marker))['kind'] == 'redmine-mcp-synthetic-v1'
elsif Project.exists? || User.where.not(login: ['admin', '']).where(type: 'User').exists?
  abort 'Refusing to bootstrap a nonempty unknown Redmine'
end

password = ENV.fetch('TEST_USER_PASSWORD')
abort 'Test password must be at least 12 characters' if password.length < 12
Redmine::DefaultData::Loader.load('en') unless Tracker.exists?
Setting.rest_api_enabled = '1'
Setting.app_title = 'Redmine MCP Synthetic Test'
Setting.self_registration = '0'
Setting.notified_events = []
admin = User.find_by!(login: 'admin')
admin.password = password
admin.password_confirmation = password
admin.must_change_passwd = false
admin.save!

reader = Role.find_or_initialize_by(name: 'MCP Reader')
reader.permissions = [:view_issues]
reader.issues_visibility = 'default'
reader.users_visibility = 'members_of_visible_projects'
reader.save!
manager = Role.find_by!(name: 'Manager')
developer = Role.find_by!(name: 'Developer')
reporter = Role.find_by!(name: 'Reporter')
users = {}
%w[manager developer reporter mcp-reader].each do |name|
  user = User.find_or_initialize_by(login: "demo-#{name}")
  user.firstname = 'Demo'
  user.lastname = name
  user.mail = "#{name}@example.invalid"
  user.password = password
  user.password_confirmation = password
  user.status = User::STATUS_ACTIVE
  user.must_change_passwd = false
  user.mail_notification = 'none'
  user.save!
  users[name] = user
end
fields = [
  ['Environment', 'string', nil, false],
  ['Release channel', 'list', ['stable', 'beta'], false],
  ['Components', 'list', ['api', 'web', 'database'], true]
].map do |name, format, values, multiple|
  field = IssueCustomField.find_or_initialize_by(name: name)
  field.field_format = format
  field.is_for_all = true
  field.is_required = false
  field.visible = true
  field.multiple = multiple
  field.possible_values = values if values
  field.trackers = Tracker.all
  field.save!
  field
end
# Default workflows belong to the default roles. Reader gets no transitions or write permissions.
credentials = {
  admin_key: admin.api_key, reader_key: users['mcp-reader'].api_key,
  users: users.transform_values(&:id),
  roles: {manager: manager.id, developer: developer.id, reporter: reporter.id, reader: reader.id},
  custom_fields: fields.map { |f| {id: f.id, name: f.name} }
}
File.write(File.join(state, 'credentials.json'), JSON.pretty_generate(credentials))
File.chmod(0600, File.join(state, 'credentials.json'))
File.write(marker, JSON.pretty_generate({kind: 'redmine-mcp-synthetic-v1', version: 1}))
puts 'Synthetic configuration ready; credentials saved locally.'

