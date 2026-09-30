from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from redmine_mcp.api.dependencies import get_projects
from redmine_mcp.api.security import require_token
from redmine_mcp.common.pagination import Page
from redmine_mcp.common.visibility import Collection
from redmine_mcp.features.projects.models import IssueCategory, Project, ProjectDetail, Version
from redmine_mcp.features.projects.service import ProjectService

router = APIRouter(
    prefix="/api/v1/projects", tags=["projects"], dependencies=[Depends(require_token)]
)


@router.get("", operation_id="list_projects", response_model=Page[Project])
async def list_projects(
    service: Annotated[ProjectService, Depends(get_projects)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[Project]:
    """List projects visible to the shared Redmine account with visibility scope metadata."""
    return await service.list_projects(limit, offset)


@router.get("/{project_id}", operation_id="get_project", response_model=ProjectDetail)
async def get_project(
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[int, Path(ge=1, description="ID of the project to retrieve")],
) -> ProjectDetail:
    """Read one project visible to the shared Redmine account with visibility metadata."""
    return await service.get_project(project_id)


@router.get(
    "/{project_id}/versions",
    operation_id="list_project_versions",
    response_model=Collection[Version],
)
async def list_project_versions(
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[int, Path(ge=1, description="ID of the project")],
) -> Collection[Version]:
    """List project versions, including shared ones, in items with visibility metadata."""
    return await service.list_project_versions(project_id)


@router.get(
    "/{project_id}/issue-categories",
    operation_id="list_project_issue_categories",
    response_model=Collection[IssueCategory],
)
async def list_project_issue_categories(
    service: Annotated[ProjectService, Depends(get_projects)],
    project_id: Annotated[int, Path(ge=1, description="ID of the project")],
) -> Collection[IssueCategory]:
    """List issue categories and optional default assignees in items with visibility metadata."""
    return await service.list_project_issue_categories(project_id)
