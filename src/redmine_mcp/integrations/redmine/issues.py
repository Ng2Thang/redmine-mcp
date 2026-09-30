from datetime import UTC, datetime

from redmine_mcp.common.pagination import Page
from redmine_mcp.features.issues.models import Issue
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item, page


class RedmineIssues:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

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
    ) -> Page[Issue]:
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
            "status_id": status_id,
            "sort": sort,
        }
        if project_id is not None:
            params["project_id"] = project_id
        if category_id is not None:
            params["category_id"] = category_id
        if assigned_to_id is not None:
            params["assigned_to_id"] = assigned_to_id
        if tracker_id is not None:
            params["tracker_id"] = tracker_id
        if parent_id is not None:
            params["parent_id"] = parent_id
        if updated_since is not None:
            utc_timestamp = updated_since.astimezone(UTC).isoformat().replace("+00:00", "Z")
            params["updated_on"] = f">={utc_timestamp}"
        data = await self.client.get("issues.json", params)
        return page(Issue, data, "issues", limit, offset)

    async def get_issue(self, issue_id: int, include: tuple[str, ...] | None = None) -> Issue:
        selected = ("journals", "attachments") if include is None else include
        params: dict[str, str | int] = {"include": ",".join(selected)} if selected else {}
        data = await self.client.get(f"issues/{issue_id}.json", params)
        return item(Issue, data.get("issue"))
