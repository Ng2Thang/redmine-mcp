import re

from fastapi import status as http_status

from redmine_mcp.auth.capability_models import WriteIntent
from redmine_mcp.auth.capability_ports import WriteAuthorizer
from redmine_mcp.common import (
    ApplicationError,
    Collection,
    Page,
    PageRequest,
    require_positive_id,
    validated_query,
)
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.projects.models import (
    AddProjectFileRequest,
    AddProjectFileResult,
    IssueCategory,
    Project,
    ProjectDetail,
    ProjectFile,
    Version,
)
from redmine_mcp.features.projects.ports import ProjectReader, ProjectWriter


class ProjectService:
    def __init__(
        self,
        reader: ProjectReader,
        writer: ProjectWriter | None = None,
        authorizer: WriteAuthorizer | None = None,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.authorizer = authorizer

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

    async def add_project_file(
        self, project_id: int, request: AddProjectFileRequest
    ) -> AddProjectFileResult:
        require_positive_id(project_id, "project_id")
        if (
            request.filename in (".", "..")
            or any(character in request.filename for character in ("/", "\\", "\x00"))
            or any(ord(character) < 32 or ord(character) == 127 for character in request.filename)
        ):
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.INVALID_FILENAME,
                http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        match = re.fullmatch(r"([1-9][0-9]*)\.[0-9a-f]+", request.token)
        if match is None:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.INVALID_UPLOAD_TOKEN,
                http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        if request.version_id is not None:
            versions = await self.reader.list_project_versions(project_id)
            if not any(
                version.id == request.version_id and version.project.id == project_id
                for version in versions.items
            ):
                raise ApplicationError(
                    codes_text.INVALID_PARAMETERS,
                    redmine_text.INVALID_PROJECT_VERSION,
                    http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                )
        if self.writer is None:
            raise RuntimeError("Project writer is not configured")
        if self.authorizer is not None:
            await self.authorizer.authorize(WriteIntent("add_project_file", project_id=project_id))
        return await self.writer.add_project_file(
            project_id,
            request.token,
            request.filename,
            request.description,
            request.version_id,
            int(match.group(1)),
        )
