from typing import Protocol

from redmine_mcp.common.pagination import Page
from redmine_mcp.features.time_entries.models import IssueTimeEntry


class TimeEntryReader(Protocol):
    async def list_issue_time_entries(
        self, issue_id: int, limit: int, offset: int
    ) -> Page[IssueTimeEntry]: ...
