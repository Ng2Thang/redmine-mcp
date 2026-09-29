from typing import Annotated

from fastapi import APIRouter, Depends, Query

from redmine_mcp.api.dependencies import get_projects
from redmine_mcp.api.security import require_token
from redmine_mcp.common.pagination import Page
from redmine_mcp.features.projects.models import Project
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
    """List projects visible to the shared Redmine account, one page at a time."""
    return await service.list_projects(limit, offset)
