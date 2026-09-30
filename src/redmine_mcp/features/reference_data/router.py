from typing import Annotated

from fastapi import APIRouter, Depends

from redmine_mcp.api.dependencies import get_reference_data
from redmine_mcp.api.security import require_token
from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker
from redmine_mcp.features.reference_data.service import ReferenceService

router = APIRouter(prefix="/api/v1", tags=["reference-data"], dependencies=[Depends(require_token)])


@router.get("/issue-statuses", operation_id="list_issue_statuses", response_model=list[IssueStatus])
async def list_issue_statuses(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> list[IssueStatus]:
    """List global issue statuses and closed flags; these are not issue-specific transitions."""
    return await service.list_issue_statuses()


@router.get("/trackers", operation_id="list_trackers", response_model=list[Tracker])
async def list_trackers(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> list[Tracker]:
    """List global trackers and enabled standard fields; project availability may differ."""
    return await service.list_trackers()


@router.get(
    "/issue-priorities", operation_id="list_issue_priorities", response_model=list[IssuePriority]
)
async def list_issue_priorities(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> list[IssuePriority]:
    """List issue priority IDs and the default priority from Redmine's global enumeration."""
    return await service.list_issue_priorities()
