from typing import Protocol

from redmine_mcp.common.pagination import Page
from redmine_mcp.features.projects.models import IssueCategory, Project, ProjectDetail, Version


class ProjectReader(Protocol):
    async def list_projects(self, limit: int, offset: int) -> Page[Project]: ...

    async def get_project(self, project_id: int) -> ProjectDetail: ...

    async def list_project_versions(self, project_id: int) -> list[Version]: ...

    async def list_project_issue_categories(self, project_id: int) -> list[IssueCategory]: ...
