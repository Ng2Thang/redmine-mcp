from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from redmine_mcp.api import get_projects, require_read_access
from redmine_mcp.common import Collection, Page
from redmine_mcp.features import ProjectService
from redmine_mcp.features.projects.models import (
    IssueCategory,
    Project,
    ProjectDetail,
    ProjectFile,
    Version,
)

router = APIRouter(
    prefix="/api/v1/projects", tags=["projects"], dependencies=[Depends(require_read_access)]
)


@router.get(
    "",
    operation_id="list_projects",
    response_model=Page[Project],
    description=(
        "Discover projects visible to the requesting Redmine user and resolve "
        "project names to numeric IDs for other tools. Returns project names, "
        "identifiers, descriptions, statuses, and parent references in a paginated "
        "result with visibility metadata. Use limit and offset to retrieve further "
        "pages. Use get_project for details of a known project ID, or list_issues "
        "with project_id to find its issues. This tool has no project-name search "
        "parameter; inspect the returned projects."
    ),
)
async def list_projects(
    service: Annotated[ProjectService, Depends(get_projects)],
    limit: Annotated[int, Query(ge=1, le=100, description=("Projects per discovery page"))] = 25,
    offset: Annotated[int, Query(ge=0, description=("Offset for pagination"))] = 0,
) -> Page[Project]:
    """List projects visible to the requesting Redmine user with visibility metadata."""
    return await service.list_projects(limit, offset)


@router.get(
    "/{project_id}",
    operation_id="get_project",
    response_model=ProjectDetail,
    description=(
        "Read details of one visible project using its numeric project ID. Use "
        "list_projects first when only the project name or identifier is known. "
        "Returns project metadata, including its description, status, parent, and "
        "optional public flag and timestamps. Visibility metadata identifies "
        "selected fields omitted by Redmine. Use list_issues, "
        "list_project_versions, or list_project_issue_categories for those related "
        "resources."
    ),
)
async def get_project(
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[int, Path(ge=1, description=("ID of the project to retrieve"))],
) -> ProjectDetail:
    """Read one project visible to the requesting Redmine user with visibility metadata."""
    return await service.get_project(project_id)


@router.get(
    "/{project_id}/versions",
    operation_id="list_project_versions",
    response_model=Collection[Version],
    description=(
        "Discover Target versions available to a visible project, including shared "
        "versions. Use a numeric project_id from list_projects. Returns version "
        "IDs, names, owning projects, open/locked/closed statuses, and optional "
        "descriptions and due dates in items with visibility metadata. A shared "
        "version may belong to another project. Use a returned version ID as "
        "fixed_version_id in list_issues to find its issues. This collection has no "
        "pagination inputs and does not report release progress."
    ),
)
async def list_project_versions(
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[int, Path(ge=1, description=("ID of the project"))],
) -> Collection[Version]:
    """List project versions, including shared ones, in items with visibility metadata."""
    return await service.list_project_versions(project_id)


@router.get(
    "/{project_id}/issue-categories",
    operation_id="list_project_issue_categories",
    response_model=Collection[IssueCategory],
    description=(
        "Discover issue categories for a visible project using its numeric project "
        "ID. Returns category IDs, names, project references, and optional default "
        "assignees in items with visibility metadata. Categories are "
        "project-specific; resolve them for the intended project before filtering "
        "issues. Use a returned category ID with the same project_id in "
        "list_issues. This collection has no pagination inputs."
    ),
)
async def list_project_issue_categories(
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[
        int,
        Path(ge=1, description=("ID of the project")),
    ],
) -> Collection[IssueCategory]:
    """List issue categories and optional default assignees in items with visibility metadata."""
    return await service.list_project_issue_categories(project_id)


@router.get(
    "/{project_id}/files",
    operation_id="list_project_files",
    response_model=Collection[ProjectFile],
    description=(
        "List files attached to a project and its versions using a project ID from "
        "list_projects. Returns file metadata and optional version references in "
        "items with visibility metadata. Redmine provides no pagination or total count "
        "for this endpoint. Listing files does not download their content."
    ),
)
async def list_project_files(
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[int, Path(ge=1, description="ID of the project")],
) -> Collection[ProjectFile]:
    """List project and version file metadata without downloading content."""
    return await service.list_project_files(project_id)
