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
    ) -> Page[Issue]:
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
            "status_id": status_id,
            "sort": "id:asc",
        }
        if project_id is not None:
            params["project_id"] = project_id
        if assigned_to_id is not None:
            params["assigned_to_id"] = assigned_to_id
        data = await self.client.get("issues.json", params)
        return page(Issue, data, "issues", limit, offset)

    async def get_issue(self, issue_id: int) -> Issue:
        data = await self.client.get(f"issues/{issue_id}.json", {"include": "journals,attachments"})
        return item(Issue, data.get("issue"))
