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

require_dependency 'query'

module RedmineupTags
  module Patches
    module TimeReportPatch

      def load_available_criteria
        return @load_available_criteria_with_redmine_tags if @load_available_criteria_with_redmine_tags
        @load_available_criteria_with_redmine_tags = super
        @load_available_criteria_with_redmine_tags['tags'] = { sql: "#{Redmineup::Tag.table_name}.id",
                                                               klass: Redmineup::Tag,
                                                               joins: redmine_tags_join,
                                                               label: :tags }
        @load_available_criteria_with_redmine_tags
      end

      private

      def redmine_tags_join
        { issue: :tags }
      end
    end
  end
end

Redmine::Helpers::TimeReport.prepend(RedmineupTags::Patches::TimeReportPatch)
