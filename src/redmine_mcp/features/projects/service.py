from redmine_mcp.common import Collection, Page, PageRequest, require_positive_id, validated_query
from redmine_mcp.features.projects.models import (
    IssueCategory,
    Project,
    ProjectDetail,
    ProjectFile,
    Version,
)
from redmine_mcp.features.projects.ports import ProjectReader


class ProjectService:
    def __init__(self, reader: ProjectReader) -> None:
        self.reader = reader

    async def list_projects(self, limit: int = 25, offset: int = 0) -> Page[Project]:
        query = validated_query(PageRequest, {"limit": limit, "offset": offset})
        return await self.reader.list_projects(limit=query.limit, offset=query.offset)

    async def get_project(self, project_id: int) -> ProjectDetail:
        require_positive_id(project_id, "project_id")
        return await self.reader.get_project(project_id)

    async def list_project_versions(self, project_id: int) -> Collection[Version]:
        require_positive_id(project_id, "project_id")
        return await self.reader.list_project_versions(project_id)

    async def list_project_issue_categories(self, project_id: int) -> Collection[IssueCategory]:
        require_positive_id(project_id, "project_id")
        return await self.reader.list_project_issue_categories(project_id)

    async def list_project_files(self, project_id: int) -> Collection[ProjectFile]:
        require_positive_id(project_id, "project_id")
        return await self.reader.list_project_files(project_id)
