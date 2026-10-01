from typing import Annotated

from fastapi import APIRouter, Depends

from redmine_mcp.api import get_reference_data, require_read_access
from redmine_mcp.common import Collection
from redmine_mcp.features import ReferenceService
from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker

router = APIRouter(
    prefix="/api/v1", tags=["reference-data"], dependencies=[Depends(require_read_access)]
)


@router.get(
    "/issue-statuses",
    operation_id="list_issue_statuses",
    response_model=Collection[IssueStatus],
    description=(
        "Resolve issue status names to IDs and determine which statuses are closed. "
        "Returns the global status catalog in items with visibility metadata and no "
        "pagination inputs. Pass a returned ID as a string in list_issues.status_id to "
        "filter by a specific status. This catalog does not describe permitted transitions "
        "for an individual issue; use get_issue with include='allowed_statuses' for that "
        "context. This tool only reads status definitions."
    ),
)
async def list_issue_statuses(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> Collection[IssueStatus]:
    """List global statuses and closed flags in items; not issue-specific transitions."""
    return await service.list_issue_statuses()


@router.get(
    "/trackers",
    operation_id="list_trackers",
    response_model=Collection[Tracker],
    description=(
        "Resolve tracker names, such as Bug or Feature, to IDs for list_issues.tracker_id. "
        "Returns the global tracker catalog, including optional descriptions, default "
        "statuses, and enabled standard fields, in items with visibility metadata. "
        "This collection has no pagination inputs. Global availability does not establish "
        "that a tracker is enabled for a particular project."
    ),
)
async def list_trackers(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> Collection[Tracker]:
    """List global trackers and enabled fields in items; project availability may differ."""
    return await service.list_trackers()


@router.get(
    "/issue-priorities",
    operation_id="list_issue_priorities",
    response_model=Collection[IssuePriority],
    description=(
        "Look up issue priority IDs and names and identify the configured default priority. "
        "Use this catalog to interpret priority references returned by list_issues or "
        "get_issue. Returns items with visibility metadata and no pagination inputs. "
        "The current list_issues tool has no priority filter, and this tool does not "
        "change an issue's priority."
    ),
)
async def list_issue_priorities(
    service: Annotated[ReferenceService, Depends(get_reference_data)],
) -> Collection[IssuePriority]:
    """List issue priority IDs and the default in items with visibility metadata."""
    return await service.list_issue_priorities()
