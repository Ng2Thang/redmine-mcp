# frozen_string_literal: true

# Global settings are changed only in a newly allocated G05 policy stack.
require 'json'
require_relative 'e2e_guard'
raise 'Policy mutation requires isolated disposable stack' unless ENV['REDMINE_G05_POLICY'] == '1' && ENV['REDMINE_E2E_PROJECT'].match?(/\Aredmine-mcp-g05-policy-(6-0-1|7-0-2)-[0-9a-f]{12}\z/)
case ARGV.first
when 'initialize'
  raise 'Policy stack database must be fresh' unless Project.count.zero? && !File.exist?('/e2e-state/g05-fixtures.json')
  Redmine::DefaultData::Loader.load('en') if Tracker.count.zero?
  Setting.rest_api_enabled = '1'
when 'restrict', 'allow'
  data = JSON.parse(File.read('/e2e-state/g05-fixtures.json'))
  E2EGuard.manifest!(data, 'g05')
  restricted = ARGV.first == 'restrict'
  Setting.timelog_required_fields = restricted ? ['comments'] : []
  Setting.timelog_accept_future_dates = restricted ? '0' : '1'
  # Matrix entries share a caller/date; avoid an unrelated daily-cap interference.
  Setting.timelog_max_hours_per_day = '0'
  Setting.timelog_accept_closed_issues = restricted ? '0' : '1' if Setting.respond_to?(:timelog_accept_closed_issues?)
  Setting.cross_project_issue_relations = '1'
  Setting.clear_cache
else
  raise 'Expected initialize, restrict or allow'
end
puts JSON.generate({owner: 'g05', version: E2EGuard::VERSION, project: ENV['REDMINE_E2E_PROJECT'],
                    required: Setting.timelog_required_fields, future: Setting.timelog_accept_future_dates?,
                    daily_max: Setting.timelog_max_hours_per_day,
                    closed_supported: Setting.respond_to?(:timelog_accept_closed_issues?),
                    closed: !Setting.respond_to?(:timelog_accept_closed_issues?) || Setting.timelog_accept_closed_issues?,
                    cross_project: Setting.cross_project_issue_relations?})
