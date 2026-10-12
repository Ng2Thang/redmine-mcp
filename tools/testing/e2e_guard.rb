# frozen_string_literal: true

# Validate the running server, not just its Docker tag or a supplied manifest.
module E2EGuard
  VERSION = [Redmine::VERSION::MAJOR, Redmine::VERSION::MINOR, Redmine::VERSION::TINY].join('.')

  def self.verify!
    raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
    raise 'Missing Compose project identity' unless ENV['REDMINE_E2E_PROJECT']&.match?(/\A[a-z0-9][a-z0-9_-]*\z/)
    supported = VERSION.match?(/\A6\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\z/) || VERSION == '7.0.2'
    raise 'Wrong Redmine version' unless supported && ENV.fetch('REDMINE_E2E_VERSION', '7.0.2') == VERSION
  end

  def self.manifest!(data, owner = 'prep-018')
    raise 'Wrong fixture owner/version/project' unless data['owner'] == owner && data['version'] == VERSION && data['project'] == ENV['REDMINE_E2E_PROJECT']
    raise 'Wrong synthetic fixture marker' if owner == 'prep-018' && data['kind'] != ENV['REDMINE_TEST_MARKER']
  end

  def self.base_resources!(data)
    manifest!(data)
    data.fetch('projects').each do |name, id|
      raise 'Unowned fixture project' unless Project.find(id).identifier == "mcp-e2e-#{name}"
    end
    data.fetch('users').each do |name, user|
      raise 'Unowned fixture user' unless User.find(user.fetch('id')).login == "mcp-e2e-#{name}"
    end
    data.fetch('roles').each do |name, id|
      expected = name == 'reporting_own' ? 'E2E reporting own logs' : "E2E #{name}"
      raise 'Unowned fixture role' unless Role.find(id).name == expected
    end
    data.fetch('issues').each_value do |id|
      raise 'Unowned fixture issue' unless data['projects'].values.include?(Issue.find(id).project_id)
    end
    raise 'Unowned fixture group' unless Group.find(data.fetch('group_id')).lastname == 'E2E group'
  end
end

E2EGuard.verify!
