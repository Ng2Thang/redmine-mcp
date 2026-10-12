# encoding: utf-8
#
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

require File.expand_path(File.dirname(__FILE__) + '/../../../test/test_helper')

def compatible_request(type, action, parameters = {})
  send(type, action, params: parameters)
end

def compatible_xhr_request(type, action, parameters = {})
  send(type, action, params: parameters, xhr: true)
end

# Returns the issues that are displayed in the list in the same order
def issues_in_list
  ids = css_select('tr.issue td.id').map{ |tag| tag['text'].to_i }
  Issue.where(id: ids).sort_by { |issue| ids.index(issue.id) }
end
