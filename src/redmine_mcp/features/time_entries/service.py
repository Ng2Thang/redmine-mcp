from datetime import date

from redmine_mcp.common import Page, PageRequest, require_positive_id, validated_query
from redmine_mcp.features.time_entries.models import IssueTimeEntry, TimeEntry
from redmine_mcp.features.time_entries.ports import TimeEntryReader
from redmine_mcp.features.time_entries.queries import TimeEntrySearch, TimeEntryUserId


class TimeEntryService:
    def __init__(self, reader: TimeEntryReader) -> None:
        self.reader = reader

    async def list_time_entries(
        self,
        project_id: int | None = None,
        include_subprojects: bool = False,
        user_id: TimeEntryUserId | None = None,
        issue_id: int | None = None,
        spent_from: date | None = None,
        spent_to: date | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> Page[TimeEntry]:
        query = validated_query(
            TimeEntrySearch,
            {
                "project_id": project_id,
                "include_subprojects": include_subprojects,
                "user_id": user_id,
                "issue_id": issue_id,
                "spent_from": spent_from,
                "spent_to": spent_to,
                "limit": limit,
                "offset": offset,
            },
        )
        return await self.reader.list_time_entries(
            project_id=query.project_id,
            include_subprojects=query.include_subprojects,
            user_id=query.user_id,
            issue_id=query.issue_id,
            spent_from=query.spent_from,
            spent_to=query.spent_to,
            limit=query.limit,
            offset=query.offset,
        )

    async def list_issue_time_entries(
        self, issue_id: int, limit: int = 25, offset: int = 0
    ) -> Page[IssueTimeEntry]:
        require_positive_id(issue_id, "issue_id")
        query = validated_query(PageRequest, {"limit": limit, "offset": offset})
        return await self.reader.list_issue_time_entries(
            issue_id=issue_id, limit=query.limit, offset=query.offset
        )
