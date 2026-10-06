from typing import Annotated

from fastapi import APIRouter, Depends, Path

from redmine_mcp.api import get_projects, require_write_access
from redmine_mcp.features.projects.models import (
    AddProjectFileRequest,
    AddProjectFileResult,
    CreateProjectVersionRequest,
    CreateProjectVersionResult,
)
from redmine_mcp.features.projects.service import ProjectService

router = APIRouter(
    prefix="/api/v1/projects", tags=["projects"], dependencies=[Depends(require_write_access)]
)


@router.post(
    "/{project_id}/files",
    operation_id="add_project_file",
    response_model=AddProjectFileResult,
    description=(
        "Attach one temporary upload token as a project file. The optional version ID must "
        "belong to the selected project. Redmine's empty success response is reported "
        "separately from file-list read-back verification. This operation is writer-only."
    ),
)
async def add_project_file(
    request: AddProjectFileRequest,
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[int, Path(ge=1, description="ID of the target project")],
) -> AddProjectFileResult:
    return await service.add_project_file(project_id, request)


@router.post(
    "/{project_id}/versions",
    operation_id="create_project_version",
    response_model=CreateProjectVersionResult,
    description=(
        "Create an open, unshared Target version in a selected project. Requires the restricted "
        "writer and Manage versions permission. Returns an existing readable version with an "
        "explicit error when creation is rejected and that project already contains the same "
        "name. Reports acceptance separately from verification; reconcile uncertain outcomes "
        "before retrying."
    ),
)
async def create_project_version(
    request: CreateProjectVersionRequest,
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[int, Path(ge=1, description="ID of the target project")],
) -> CreateProjectVersionResult:
    return await service.create_project_version(project_id, request)
