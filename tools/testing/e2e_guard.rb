# frozen_string_literal: true

# Validate the running server, not just its Docker tag or a supplied manifest.
module E2EGuard
  VERSION = [Redmine::VERSION::MAJOR, Redmine::VERSION::MINOR, Redmine::VERSION::TINY].join('.')

  def self.verify!
    raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
    supported = VERSION.match?(/\A6\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\z/) || VERSION == '7.0.2'
    raise 'Wrong Redmine version' unless supported && ENV.fetch('REDMINE_E2E_VERSION', '7.0.2') == VERSION
  end

  def self.manifest!(data, owner = 'prep-018')
    raise 'Wrong fixture owner/version' unless data['owner'] == owner && data['version'] == VERSION
  end
end

E2EGuard.verify!
