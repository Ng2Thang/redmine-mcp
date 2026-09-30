import re
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import AwareDatetime, BeforeValidator

from redmine_mcp.api.dependencies import get_issues
from redmine_mcp.api.security import require_token
from redmine_mcp.common.pagination import Page
from redmine_mcp.features.issues.models import ISSUE_INCLUDES, Issue, IssueDetail
from redmine_mcp.features.issues.service import IssueService

router = APIRouter(prefix="/api/v1/issues", tags=["issues"], dependencies=[Depends(require_token)])


def require_rfc3339(value: object) -> object:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ):
        raise ValueError("Expected an RFC 3339 timestamp with timezone")
    return value


UpdatedSince = Annotated[AwareDatetime, BeforeValidator(require_rfc3339)]
IssueSort = Literal["id:asc", "id:desc", "updated_on:asc", "updated_on:desc"]


def parse_issue_includes(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    if value == "":
        return ()
    selected = tuple(value.split(","))
    if any(part not in ISSUE_INCLUDES for part in selected) or len(set(selected)) != len(selected):
        raise HTTPException(status_code=422, detail="Invalid issue include selection")
    return selected


@router.get(
    "",
    operation_id="list_issues",
    response_model=Page[Issue],
    description=(
        "Find issues visible to the Redmine account shared by this server. "
        "Use this tool to search or list issues; use get_issue when you need one "
        "issue's journals and attachment metadata. The default status is open; "
        "use '*' to include all statuses. assigned_to_id='me' means the shared "
        "server account, not the individual MCP user. Filter by tracker, parent, "
        "or last update, and choose ID or update-time ordering. Filter by category "
        "ID within a project or Target version ID. Set include_subprojects to false "
        "to restrict a project query to that project. Results are paginated. "
        "Each issue includes nullable start/due dates and permission-gated direct "
        "spent_hours and descendant-inclusive total_spent_hours. Page through all "
        "matches before summing direct spent_hours. Visibility metadata reports "
        "selected fields omitted by Redmine without asserting the cause."
    ),
)
async def list_issues(
    service: Annotated[IssueService, Depends(get_issues)],
    project_id: Annotated[
        int | None, Query(ge=1, description="Filter issues by project ID")
    ] = None,
    status_id: Annotated[
        str,
        Query(
            pattern=r"^(open|closed|\*|[1-9][0-9]*)$",
            description="Filter issues by status (open, closed, *, or a specific status ID)",
        ),
    ] = "open",
    assigned_to_id: Annotated[
        str | None,
        Query(
            pattern=r"^(me|[1-9][0-9]*)$",
            description="Filter issues by assignee ID ('me' for the shared server account)",
        ),
    ] = None,
    tracker_id: Annotated[int | None, Query(ge=1, description="Filter by tracker ID")] = None,
    parent_id: Annotated[int | None, Query(ge=1, description="Filter by parent issue ID")] = None,
    updated_since: Annotated[
        UpdatedSince | None,
        Query(description="Include issues updated at or after this RFC 3339 timestamp"),
    ] = None,
    sort: Annotated[
        IssueSort,
        Query(description="Order issues by ID or last update"),
    ] = "id:asc",
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of issues to return per page")
    ] = 25,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    category_id: Annotated[
        int | None,
        Query(ge=1, description="Filter by category ID within the selected project"),
    ] = None,
    fixed_version_id: Annotated[
        int | None,
        Query(ge=1, description="Filter by Target version ID"),
    ] = None,
    include_subprojects: Annotated[
        bool,
        Query(description="Include descendant-project issues when filtering by project"),
    ] = True,
) -> Page[Issue]:
    """List visible issues. Status defaults to open; '*' means all.
    Assignee 'me' means the shared server account, not the individual MCP user.
    Full journals and attachment metadata are available through get_issue.
    """
    if category_id is not None and project_id is None:
        raise HTTPException(status_code=422, detail="project_id is required with category_id")
    if not include_subprojects and project_id is None:
        raise HTTPException(
            status_code=422,
            detail="project_id is required when include_subprojects is false",
        )
    return await service.list_issues(
        project_id,
        status_id,
        assigned_to_id,
        limit,
        offset,
        tracker_id,
        parent_id,
        updated_since,
        sort,
        category_id,
        fixed_version_id,
        include_subprojects,
    )


@router.get(
    "/{issue_id}",
    operation_id="get_issue",
    response_model=IssueDetail,
    description=(
        "Read one visible issue. By default include journals and attachment metadata. "
        "Select children, attachments, relations, changesets, journals, watchers, or "
        "allowed_statuses with a comma-separated include; an empty include requests none. "
        "Unrequested collections appear empty and do not establish that no related data exists. "
        "The issue includes nullable start/due dates and permission-gated direct "
        "spent_hours and descendant-inclusive total_spent_hours. Visibility metadata "
        "distinguishes fields not returned from expansions not requested."
    ),
)
async def get_issue(
    service: Annotated[IssueService, Depends(get_issues)],
    issue_id: Annotated[int, Path(ge=1, description="ID of the issue to retrieve")],
    include: Annotated[
        str | None,
        Query(description="Comma-separated issue expansions; empty string requests none"),
    ] = None,
) -> IssueDetail:
    """Read an issue with selected related context."""
    return await service.get_issue(issue_id, parse_issue_includes(include))
