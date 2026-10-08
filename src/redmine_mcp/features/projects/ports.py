from typing import Protocol

from redmine_mcp.common import Collection, Page
from redmine_mcp.features.projects.models import (
    AddProjectFileResult,
    CreateProjectVersionRequest,
    CreateProjectVersionResult,
    IssueCategory,
    Project,
    ProjectDetail,
    ProjectFile,
    ProjectTimeEntryActivity,
    Version,
)


class ProjectReader(Protocol):
    async def list_projects(self, limit: int, offset: int) -> Page[Project]: ...

    async def get_project(self, project_id: int) -> ProjectDetail: ...

    async def list_project_versions(self, project_id: int) -> Collection[Version]: ...

    async def list_project_issue_categories(self, project_id: int) -> Collection[IssueCategory]: ...

    async def list_project_files(self, project_id: int) -> Collection[ProjectFile]: ...

    async def list_project_time_entry_activities(
        self, project_id: int
    ) -> Collection[ProjectTimeEntryActivity]: ...


class ProjectWriter(Protocol):
    async def add_project_file(
        self,
        project_id: int,
        token: str,
        filename: str,
        description: str | None,
        version_id: int | None,
        attachment_id: int,
    ) -> AddProjectFileResult: ...


class ProjectVersionCreator(Protocol):
    async def create_project_version(
        self, project_id: int, request: CreateProjectVersionRequest
    ) -> CreateProjectVersionResult: ...
