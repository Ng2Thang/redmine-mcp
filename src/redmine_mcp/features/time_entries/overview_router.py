from typing import Annotated

from fastapi import APIRouter, Depends, Query

from redmine_mcp.api import get_time_entries, require_read_access
from redmine_mcp.common import Page
from redmine_mcp.features.issues.models import IssueDate
from redmine_mcp.features.time_entries.models import TimeEntry
from redmine_mcp.features.time_entries.queries import TimeEntryUserId
from redmine_mcp.features.time_entries.service import TimeEntryService

router = APIRouter(
    prefix="/api/v1/time-entries",
    tags=["time entries"],
    dependencies=[Depends(require_read_access)],
)


@router.get(
    "",
    operation_id="list_time_entries",
    response_model=Page[TimeEntry],
    description=(
        "List spent-time entries visible to the requesting Redmine user across projects. "
        "An issue is not required: project-only entries are included. Filter by project, "
        "credited user, exact issue or inclusive spent_from/spent_to calendar dates. "
        "Dates select the log's spent_on, not the issue's schedule. user_id='me' selects "
        "the requesting user; the credited user may differ from the submitter or assignee. "
        "Resolve project IDs with list_projects and caller identity with get_current_user. "
        "Without project_id, all caller-visible projects are included. A project filter "
        "excludes subprojects unless include_subprojects=true; true requires project_id. "
        "Entries are ordered by spent_on ascending with Redmine's entry-ID tie breaker. "
        "Each entry includes its project, user, hours, spent_on and nullable issue_id, "
        "activity and comments. An absent issue reference does not establish its cause. "
        "Check pagination_policy before continuation; requires_narrowing=true means a "
        "preview. Narrow project, user, issue or date filters and stop on scope_required "
        "or scan_budget_exceeded. After complete permitted pagination, deduplicate entry "
        "IDs and sum hours using decimal arithmetic, optionally grouped by project, user, "
        "activity or day. Report incomplete totals as partial or unavailable. Page total "
        "counts entries, not hours. All results and totals are caller-visible; complete "
        "pagination does not establish access to all users' logs. Paging is not a snapshot."
    ),
)
async def list_time_entries(
    service: Annotated[TimeEntryService, Depends(get_time_entries)],
    project_id: Annotated[int | None, Query(ge=1, description="Filter by project ID")] = None,
    include_subprojects: Annotated[
        bool, Query(description="Include descendants of project_id; requires project_id")
    ] = False,
    user_id: Annotated[
        TimeEntryUserId | None, Query(description="Credited user ID, or 'me' for the caller")
    ] = None,
    issue_id: Annotated[
        int | None, Query(ge=1, description="Filter entries directly on this issue")
    ] = None,
    spent_from: Annotated[
        IssueDate | None, Query(description="Inclusive first spent_on date (YYYY-MM-DD)")
    ] = None,
    spent_to: Annotated[
        IssueDate | None, Query(description="Inclusive last spent_on date (YYYY-MM-DD)")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Entries per page")] = 25,
    offset: Annotated[int, Query(ge=0, description="Offset for permitted pagination")] = 0,
) -> Page[TimeEntry]:
    return await service.list_time_entries(
        project_id=project_id,
        include_subprojects=include_subprojects,
        user_id=user_id,
        issue_id=issue_id,
        spent_from=spent_from,
        spent_to=spent_to,
        limit=limit,
        offset=offset,
    )
