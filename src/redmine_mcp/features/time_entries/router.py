from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from redmine_mcp.api.dependencies import get_time_entries
from redmine_mcp.api.security import require_token
from redmine_mcp.common.pagination import Page
from redmine_mcp.features.time_entries.models import IssueTimeEntry
from redmine_mcp.features.time_entries.service import TimeEntryService

router = APIRouter(
    prefix="/api/v1/issues", tags=["time entries"], dependencies=[Depends(require_token)]
)


@router.get(
    "/{issue_id}/time-entries",
    operation_id="list_issue_time_entries",
    response_model=Page[IssueTimeEntry],
    description=(
        "List time entries visible to the shared Redmine account that are logged directly "
        "on one issue. Each entry identifies the user credited with the hours; that user "
        "may differ from the person who submitted the entry. Page through all results "
        "before totaling hours."
    ),
)
async def list_issue_time_entries(
    service: Annotated[TimeEntryService, Depends(get_time_entries)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the visible issue")],
    limit: Annotated[int, Query(ge=1, le=100, description="Entries per page")] = 25,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
) -> Page[IssueTimeEntry]:
    return await service.list_issue_time_entries(issue_id, limit, offset)
