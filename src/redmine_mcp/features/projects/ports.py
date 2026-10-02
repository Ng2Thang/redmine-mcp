from typing import Protocol

from redmine_mcp.common import Collection, Page
from redmine_mcp.features.projects.models import (
    IssueCategory,
    Project,
    ProjectDetail,
    ProjectFile,
    Version,
)


class ProjectReader(Protocol):
    async def list_projects(self, limit: int, offset: int) -> Page[Project]: ...

    async def get_project(self, project_id: int) -> ProjectDetail: ...

    async def list_project_versions(self, project_id: int) -> Collection[Version]: ...

    async def list_project_issue_categories(self, project_id: int) -> Collection[IssueCategory]: ...

    async def list_project_files(self, project_id: int) -> Collection[ProjectFile]: ...
