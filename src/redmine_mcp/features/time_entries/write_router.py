"""Restricted time-entry writes on visible issues."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from redmine_mcp.api import get_time_entries, require_write_access
from redmine_mcp.features.time_entries.service import TimeEntryService
from redmine_mcp.features.time_entries.write_models import (
    TimeEntryCreateRequest,
    TimeEntryCreateResult,
    TimeEntryUpdateRequest,
    TimeEntryUpdateResult,
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


@router.put(
    "/{issue_id}/time-entries/{time_entry_id}",
    operation_id="update_time_entry",
    response_model=TimeEntryUpdateResult,
    description=(
        "Update supplied hours, spent_on date, activity_id or comments on one time entry "
        "belonging to a visible issue. Supply issue_id, time_entry_id and at least one field; "
        "omitted fields are unchanged and supplied nulls are rejected. Empty comments clear "
        "comments subject to native validation. Requires the separate restricted writer, "
        "visible spent time and native Edit spent time or eligible Edit own spent time "
        "permission. Cannot move or recredit entries. Sends one update and reports acceptance "
        "separately from independent read-back; reconcile uncertainty before retrying."
    ),
)
async def update_time_entry(
    request: TimeEntryUpdateRequest,
    service: Annotated[TimeEntryService, Depends(get_time_entries)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the visible issue")],
    time_entry_id: Annotated[int, Path(ge=1, description="ID of the entry on this issue")],
) -> TimeEntryUpdateResult:
    return await service.update_time_entry(issue_id, time_entry_id, request)
