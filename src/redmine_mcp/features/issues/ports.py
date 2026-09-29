from typing import Protocol

from redmine_mcp.common.pagination import Page
from redmine_mcp.features.issues.models import Issue


class IssueReader(Protocol):
    async def list_issues(
        self,
        project_id: int | None,
        status_id: str,
        assigned_to_id: str | None,
        limit: int,
        offset: int,
    ) -> Page[Issue]: ...

    async def get_issue(self, issue_id: int) -> Issue: ...
