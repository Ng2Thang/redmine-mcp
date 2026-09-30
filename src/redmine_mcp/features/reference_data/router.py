from typing import Annotated

from fastapi import APIRouter, Depends

from redmine_mcp.api.dependencies import get_reference_data
from redmine_mcp.api.security import require_token
from redmine_mcp.common.visibility import Collection
from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker
from redmine_mcp.features.reference_data.service import ReferenceService

router = APIRouter(prefix="/api/v1", tags=["reference-data"], dependencies=[Depends(require_token)])


@router.get(
    "/issue-statuses", operation_id="list_issue_statuses", response_model=Collection[IssueStatus]
)
async def list_issue_statuses(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> Collection[IssueStatus]:
    """List global statuses and closed flags in items; not issue-specific transitions."""
    return await service.list_issue_statuses()


@router.get("/trackers", operation_id="list_trackers", response_model=Collection[Tracker])
async def list_trackers(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> Collection[Tracker]:
    """List global trackers and enabled fields in items; project availability may differ."""
    return await service.list_trackers()


@router.get(
    "/issue-priorities",
    operation_id="list_issue_priorities",
    response_model=Collection[IssuePriority],
)
async def list_issue_priorities(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> Collection[IssuePriority]:
    """List issue priority IDs and the default in items with visibility metadata."""
    return await service.list_issue_priorities()
