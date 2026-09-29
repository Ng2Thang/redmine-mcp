from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from redmine_mcp.api.dependencies import get_issues
from redmine_mcp.api.security import require_token
from redmine_mcp.common.pagination import Page
from redmine_mcp.features.issues.models import Issue
from redmine_mcp.features.issues.service import IssueService

router = APIRouter(prefix="/api/v1/issues", tags=["issues"], dependencies=[Depends(require_token)])


@router.get("", operation_id="list_issues", response_model=Page[Issue], description=(
    "Find issues visible to the Redmine account shared by this server. "
    "Use this tool to search or list issues; use get_issue when you need one "
    "issue's journals and attachment metadata. The default status is open; "
    "use '*' to include all statuses. assigned_to_id='me' means the shared "
    "server account, not the individual MCP user. Results are paginated."
))
async def list_issues(
    service: Annotated[IssueService, Depends(get_issues)],
    project_id: Annotated[int | None, Query(ge=1, description="Filter issues by project ID")] = None,
    status_id: Annotated[str, Query(pattern=r"^(open|closed|\*|[1-9][0-9]*)$", description="Filter issues by status (open, closed, *, or a specific status ID)")] = "open",
    assigned_to_id: Annotated[str | None, Query(pattern=r"^(me|[1-9][0-9]*)$", description="Filter issues by assignee ID ('me' for the shared server account)")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of issues to return per page")] = 25,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
) -> Page[Issue]:
    """List visible issues. Status defaults to open; '*' means all.
    Assignee 'me' means the shared server account, not the individual MCP user.
    Full journals and attachment metadata are available through get_issue.
    """
    return await service.list_issues(project_id, status_id, assigned_to_id, limit, offset)


@router.get("/{issue_id}", operation_id="get_issue", response_model=Issue , description=(
    "Read an issue, its visible journals, custom fields and attachment metadata."
))
async def get_issue(
    service: Annotated[IssueService, Depends(get_issues)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the issue to retrieve")],
) -> Issue:
    """Read an issue, its visible journals, custom fields and attachment metadata."""
    return await service.get_issue(issue_id)
