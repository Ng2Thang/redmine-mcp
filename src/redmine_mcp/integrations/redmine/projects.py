from redmine_mcp.common.pagination import Page
from redmine_mcp.features.projects.models import Project
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import page


class RedmineProjects:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_projects(self, limit: int, offset: int) -> Page[Project]:
        data = await self.client.get("projects.json", {"limit": limit, "offset": offset})
        return page(Project, data, "projects", limit, offset)
