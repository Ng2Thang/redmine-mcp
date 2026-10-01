from redmine_mcp.common import Collection, Page
from redmine_mcp.features.projects import IssueCategory, Project, ProjectDetail, Version
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import page, visible_item, wrapped_collection
from redmine_mcp.integrations.redmine.responses import resource_object


class RedmineProjects:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_projects(self, limit: int, offset: int) -> Page[Project]:
        data = await self.client.get("projects.json", {"limit": limit, "offset": offset})
        return page(Project, data, "projects", limit, offset)

    async def get_project(self, project_id: int) -> ProjectDetail:
        data = await self.client.get(f"projects/{project_id}.json", {})
        return visible_item(ProjectDetail, resource_object(data.get("project"), project_id))

    async def list_project_versions(self, project_id: int) -> Collection[Version]:
        data = await self.client.get(f"projects/{project_id}/versions.json", {})
        return wrapped_collection(Version, data, "versions", complete=True)

    async def list_project_issue_categories(self, project_id: int) -> Collection[IssueCategory]:
        data = await self.client.get(f"projects/{project_id}/issue_categories.json", {})
        return wrapped_collection(IssueCategory, data, "issue_categories", complete=True)
