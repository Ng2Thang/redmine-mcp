from typing import Annotated

from fastapi import APIRouter, Depends

from redmine_mcp.api import get_issues, require_write_access
from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.issues.write_models import IssueCreateRequest, IssueCreateResult

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
