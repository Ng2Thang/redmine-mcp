# frozen_string_literal: true

# Remove only unattached artifacts from interrupted preparation acceptance calls.
require 'json'
raise 'Wrong fixture environment' unless ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1' && ENV['REDMINE_E2E_OWNER'] == 'prep-018'
raise 'Wrong Redmine version' unless [Redmine::VERSION::MAJOR, Redmine::VERSION::MINOR, Redmine::VERSION::TINY] == [7, 0, 2]
base = JSON.parse(File.read('/seed-state/fixtures.json'))
raise 'Wrong fixture owner' unless base['owner'] == 'prep-018'
attachments = Attachment.where(filename: %w[prep024.txt prep024-inspector.txt], container_id: nil, author_id: base['users']['a']['id']).to_a
attachments.each(&:destroy!)
puts JSON.generate({owner: 'prep-022-026', unattached_preparation_artifacts_removed: attachments.size})
