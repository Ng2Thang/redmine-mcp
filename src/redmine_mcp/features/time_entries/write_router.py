"""Restricted own-time creation on a visible issue."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from redmine_mcp.api import get_time_entries, require_write_access
from redmine_mcp.features.time_entries.service import TimeEntryService
from redmine_mcp.features.time_entries.write_models import (
    TimeEntryCreateRequest,
    TimeEntryCreateResult,
)

router = APIRouter(
    prefix="/api/v1/issues", tags=["time entries"], dependencies=[Depends(require_write_access)]
)


@router.post(
    "/{issue_id}/time-entries",
    operation_id="create_time_entry",
    response_model=TimeEntryCreateResult,
    description=(
        "Log time for the authenticated Redmine caller on one visible issue. Required issue_id, "
        "positive numeric hours and explicit spent_on date. Optional activity_id uses the "
        "project's native caller default when omitted; comments are optional. Requires the "
        "separate restricted writer and Log spent time permission. Each call creates a separate "
        "entry and changes spent-time totals. Reports write acceptance separately from "
        "independent read-back; reconcile uncertain outcomes before retrying."
    ),
)
async def create_time_entry(
    request: TimeEntryCreateRequest,
    service: Annotated[TimeEntryService, Depends(get_time_entries)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the visible issue")],
) -> TimeEntryCreateResult:
    return await service.create_time_entry(issue_id, request)
