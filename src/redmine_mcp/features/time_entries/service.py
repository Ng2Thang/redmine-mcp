from redmine_mcp.common.pagination import Page
from redmine_mcp.features.time_entries.models import IssueTimeEntry
from redmine_mcp.features.time_entries.ports import TimeEntryReader


class TimeEntryService:
    def __init__(self, reader: TimeEntryReader) -> None:
        self.reader = reader

    async def list_issue_time_entries(
        self, issue_id: int, limit: int = 25, offset: int = 0
    ) -> Page[IssueTimeEntry]:
        return await self.reader.list_issue_time_entries(issue_id, limit, offset)
