# This file is a part of Redmine Tags (redmine_tags) plugin,
# customer relationship management plugin for Redmine
#
# Copyright (C) 2011-2026 RedmineUP
# http://www.redmineup.com/
#
# redmine_tags is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# redmine_tags is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with redmine_tags.  If not, see <http://www.gnu.org/licenses/>.

require_dependency 'queries_helper'
require_dependency 'issue_queries_query' if ActiveSupport::Dependencies::search_for_file('issue_queries_helper')

module RedmineupTags
  module Patches
    module QueriesHelperPatch
      def self.prepended(base)
        base.include TagsHelper
      end

      def column_value(column, list_object, value)
        if column.name == :tags_relations && list_object.is_a?(Issue)
          [value].flatten.collect{ |t| render_issue_tag_link(t) }.join(RedmineupTags.settings['issues_use_colors'].to_i > 0 ? ' ' : ', ').html_safe
        else
          super(column, list_object, value)
        end
      end
    end
  end
end

base = ActiveSupport::Dependencies::search_for_file('issue_queries_helper') ? IssueQueriesHelper : QueriesHelper
base.prepend(RedmineupTags::Patches::QueriesHelperPatch)
