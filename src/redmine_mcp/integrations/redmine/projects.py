from redmine_mcp.common.pagination import Page
from redmine_mcp.features.projects.models import IssueCategory, Project, ProjectDetail, Version
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import complete_collection, item, page


class RedmineProjects:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_projects(self, limit: int, offset: int) -> Page[Project]:
        data = await self.client.get("projects.json", {"limit": limit, "offset": offset})
        return page(Project, data, "projects", limit, offset)

    async def get_project(self, project_id: int) -> ProjectDetail:
        data = await self.client.get(f"projects/{project_id}.json", {})
        return item(ProjectDetail, data.get("project"))

    async def list_project_versions(self, project_id: int) -> list[Version]:
        data = await self.client.get(f"projects/{project_id}/versions.json", {})
        return complete_collection(Version, data, "versions")

    async def list_project_issue_categories(self, project_id: int) -> list[IssueCategory]:
        data = await self.client.get(f"projects/{project_id}/issue_categories.json", {})
        return complete_collection(IssueCategory, data, "issue_categories")
