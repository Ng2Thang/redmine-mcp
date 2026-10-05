from typing import Annotated

from fastapi import APIRouter, Depends, Path

from redmine_mcp.api import get_issues, require_write_access
from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.issues.write_models import (
    IssueCreateRequest,
    IssueCreateResult,
    IssueNoteUpdateRequest,
    IssueNoteUpdateResult,
    IssueRelationCreateRequest,
    IssueRelationCreateResult,
    IssueUpdateRequest,
    IssueUpdateResult,
    IssueWatcherAddRequest,
    IssueWatcherResult,
)

router = APIRouter(
    prefix="/api/v1/issues", tags=["issues"], dependencies=[Depends(require_write_access)]
)


@router.post(
    "",
    operation_id="create_issue",
    response_model=IssueCreateResult,
    description=(
        "Create an issue in the destination project, or use native Redmine copy_from for one "
        "visible source issue without copying its subtree. Subject is required without a copy. "
        "Native attachment, link, and watcher policies apply. Requires the restricted writer, "
        "destination Add issues and source Copy issues permissions. Reports write acceptance "
        "separately from supplied-field read-back; never automatically retries an uncertain create."
    ),
)
async def create_issue(
    request: IssueCreateRequest,
    service: Annotated[IssueService, Depends(get_issues)],
) -> IssueCreateResult:
    return await service.create_issue(request)


@router.put(
    "/{issue_id}",
    operation_id="update_issue",
    response_model=IssueUpdateResult,
    description=(
        "Update only supplied issue fields, attach uploads, or add a nonblank note. "
        "Explicit null clears supported fields; omissions are preserved. Notes-only calls "
        "require Add notes, without an additional Edit issues requirement. Redmine enforces "
        "each field's workflow and permissions. Reports empty success separately from "
        "per-field read-back and new-journal observations. Requires the restricted writer; "
        "an uncertain update must be reconciled before retrying, especially when adding notes."
    ),
)
async def update_issue(
    request: IssueUpdateRequest,
    service: Annotated[IssueService, Depends(get_issues)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the issue")],
) -> IssueUpdateResult:
    return await service.update_issue(issue_id, request)


@router.put(
    "/{issue_id}/notes/{journal_id}",
    operation_id="update_issue_note",
    response_model=IssueNoteUpdateResult,
    description=(
        "Edit supplied notes or privacy on one visible journal belonging to the declared issue. "
        "Empty notes clear text and may hide an entry with no visible details; this does not "
        "delete its stored journal row. Requires the restricted writer and Edit notes or Edit "
        "own notes, plus Set notes private for privacy changes. Reports write acceptance "
        "separately from same-journal read-back. Visible absence is not proof of clearing or "
        "deletion. Reconcile uncertain writes before retrying."
    ),
)
async def update_issue_note(
    request: IssueNoteUpdateRequest,
    service: Annotated[IssueService, Depends(get_issues)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the issue containing the note")],
    journal_id: Annotated[int, Path(ge=1, description="ID of the journal to edit")],
) -> IssueNoteUpdateResult:
    return await service.update_issue_note(issue_id, journal_id, request)


@router.post(
    "/{issue_id}/relations",
    operation_id="create_issue_relation",
    response_model=IssueRelationCreateResult,
    description=(
        "Create exactly one relation between two visible issues. Defaults to relates; delay "
        "is allowed only for precedes/follows. Redmine normalizes inverse directions and can "
        "reschedule successor dates for scheduling relations; both issues can gain journals. "
        "Requires the restricted writer and Manage issue relations on the source project. "
        "Reports acceptance separately from normalized same-ID relation read-back, which does "
        "not verify date or journal effects. Reconcile uncertain creates before retrying."
    ),
)
async def create_issue_relation(
    request: IssueRelationCreateRequest,
    service: Annotated[IssueService, Depends(get_issues)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the source issue")],
) -> IssueRelationCreateResult:
    return await service.create_issue_relation(issue_id, request)


@router.post(
    "/{issue_id}/watchers",
    operation_id="add_issue_watcher",
    response_model=IssueWatcherResult,
    description=(
        "Add one watcher principal to a visible issue. Requires the restricted writer and Add "
        "issue watchers. Redmine can accept ineligible users without adding them; empty success "
        "does not prove membership. Independently checks the visible watcher expansion when "
        "View issue watchers permits it. Hidden or failed read-back leaves verification "
        "unavailable. Membership may already exist; reconcile uncertain writes before retrying."
    ),
)
async def add_issue_watcher(
    request: IssueWatcherAddRequest,
    service: Annotated[IssueService, Depends(get_issues)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the issue")],
) -> IssueWatcherResult:
    return await service.add_issue_watcher(issue_id, request.user_id)


@router.delete(
    "/{issue_id}/watchers/{user_id}",
    operation_id="remove_issue_watcher",
    response_model=IssueWatcherResult,
    description=(
        "Remove one principal's direct watcher entry from a visible issue. Requires the "
        "restricted writer and Delete issue watchers; View issue watchers is needed only for "
        "membership verification. Empty success may be a no-op. Reports acceptance separately "
        "from absence in an explicit watcher list; hidden or failed read-back is unavailable. "
        "Users may still watch through groups. Reconcile uncertain writes before retrying."
    ),
)
async def remove_issue_watcher(
    service: Annotated[IssueService, Depends(get_issues)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the issue")],
    user_id: Annotated[int, Path(ge=1, description="ID of the watcher principal to remove")],
) -> IssueWatcherResult:
    return await service.remove_issue_watcher(issue_id, user_id)
