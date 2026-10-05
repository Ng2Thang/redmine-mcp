from typing import Annotated

from fastapi import APIRouter, Depends, Path

from redmine_mcp.api import get_issues, require_write_access
from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.issues.write_models import (
    IssueCreateRequest,
    IssueCreateResult,
    IssueUpdateRequest,
    IssueUpdateResult,
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
