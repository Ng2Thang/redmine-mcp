from datetime import datetime
from typing import Protocol

from redmine_mcp.common import Page
from redmine_mcp.features.issues.models import Issue, IssueDetail


class IssueReader(Protocol):
    async def list_issues(
        self,
        project_id: int | None,
        status_id: str,
        assigned_to_id: str | None,
        limit: int,
        offset: int,
        tracker_id: int | None,
        parent_id: int | None,
        updated_since: datetime | None,
        sort: str,
        category_id: int | None,
        fixed_version_id: int | None,
        include_subprojects: bool,
        include: tuple[str, ...] | None,
    ) -> Page[Issue]: ...

    async def get_issue(
        self, issue_id: int, include: tuple[str, ...] | None = None
    ) -> IssueDetail: ...
