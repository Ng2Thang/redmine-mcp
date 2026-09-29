from redmine_mcp.common.pagination import Page
from redmine_mcp.features.projects.models import Project
from redmine_mcp.features.projects.ports import ProjectReader


class ProjectService:
    def __init__(self, reader: ProjectReader) -> None:
        self.reader = reader

    async def list_projects(self, limit: int = 25, offset: int = 0) -> Page[Project]:
        return await self.reader.list_projects(limit, offset)
