from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from redmine_mcp.api import get_time_entries, require_read_access
from redmine_mcp.common import Page
from redmine_mcp.features import TimeEntryService
from redmine_mcp.features.time_entries.models import IssueTimeEntry

router = APIRouter(
    prefix="/api/v1/issues", tags=["time entries"], dependencies=[Depends(require_read_access)]
)


@router.get(
    "/{issue_id}/time-entries",
    operation_id="list_issue_time_entries",
    response_model=Page[IssueTimeEntry],
    description=(
        "List time entries visible to the requesting Redmine user that are logged directly "
        "on one issue. Each entry identifies the user credited with the hours; that user "
        "may differ from the person who submitted the entry. Page through all results "
        "before totaling hours. Use this tool to inspect who was credited with time, "
        "how many hours, and on which dates. Use list_issues to discover an issue ID "
        "and get_issue for aggregate spent_hours and total_spent_hours. Entries on "
        "descendant issues are excluded. An empty page does not establish that no "
        "entries exist outside the requesting user's permissions."
    ),
)
async def list_issue_time_entries(
    service: Annotated[TimeEntryService, Depends(get_time_entries)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the visible issue")],
    limit: Annotated[int, Query(ge=1, le=100, description="Entries per page")] = 25,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
) -> Page[IssueTimeEntry]:
    return await service.list_issue_time_entries(issue_id, limit, offset)
