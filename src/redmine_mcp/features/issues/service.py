from datetime import datetime

from redmine_mcp.common.pagination import Page
from redmine_mcp.features.issues.models import Issue, IssueDetail
from redmine_mcp.features.issues.ports import IssueReader


class IssueService:
    def __init__(self, reader: IssueReader) -> None:
        self.reader = reader

    async def list_issues(
        self,
        project_id: int | None = None,
        status_id: str = "open",
        assigned_to_id: str | None = None,
        limit: int = 25,
        offset: int = 0,
        tracker_id: int | None = None,
        parent_id: int | None = None,
        updated_since: datetime | None = None,
        sort: str = "id:asc",
        category_id: int | None = None,
        fixed_version_id: int | None = None,
        include_subprojects: bool = True,
    ) -> Page[Issue]:
        return await self.reader.list_issues(
            project_id,
            status_id,
            assigned_to_id,
            limit,
            offset,
            tracker_id,
            parent_id,
            updated_since,
            sort,
            category_id,
            fixed_version_id,
            include_subprojects,
        )

    async def get_issue(self, issue_id: int, include: tuple[str, ...] | None = None) -> IssueDetail:
        return await self.reader.get_issue(issue_id, include)
