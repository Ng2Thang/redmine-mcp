from redmine_mcp.common.pagination import Page
from redmine_mcp.common.visibility import Collection
from redmine_mcp.features.projects.models import IssueCategory, Project, ProjectDetail, Version
from redmine_mcp.features.projects.ports import ProjectReader


class ProjectService:
    def __init__(self, reader: ProjectReader) -> None:
        self.reader = reader

    async def list_projects(self, limit: int = 25, offset: int = 0) -> Page[Project]:
        return await self.reader.list_projects(limit, offset)

    async def get_project(self, project_id: int) -> ProjectDetail:
        return await self.reader.get_project(project_id)

    async def list_project_versions(self, project_id: int) -> Collection[Version]:
        return await self.reader.list_project_versions(project_id)

    async def list_project_issue_categories(self, project_id: int) -> Collection[IssueCategory]:
        return await self.reader.list_project_issue_categories(project_id)
