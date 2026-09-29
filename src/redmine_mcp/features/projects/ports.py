from typing import Protocol

from redmine_mcp.common.pagination import Page
from redmine_mcp.features.projects.models import Project


class ProjectReader(Protocol):
    async def list_projects(self, limit: int, offset: int) -> Page[Project]: ...
