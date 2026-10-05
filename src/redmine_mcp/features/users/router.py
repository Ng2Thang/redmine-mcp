from typing import Annotated

from fastapi import APIRouter, Depends, Query

from redmine_mcp.api import get_auth_context, get_users, require_read_access
from redmine_mcp.api.dependencies import get_project_capabilities
from redmine_mcp.auth import AuthContext
from redmine_mcp.features import UserService
from redmine_mcp.features.users.capability_models import MyProjectCapabilities
from redmine_mcp.features.users.capability_service import ProjectCapabilityService
from redmine_mcp.features.users.models import CurrentUser

router = APIRouter(
    prefix="/api/v1/users", tags=["users"], dependencies=[Depends(require_read_access)]
)


@router.get(
    "/current",
    operation_id="get_current_user",
    response_model=CurrentUser,
    description=(
        "Identify the Redmine user associated with the requesting API key. "
        "Returns ID, login, first and last name, nullable email, and visible project "
        "memberships with roles and inherited flags. Takes no arguments and always "
        "requests memberships. Memberships follow Redmine project visibility; they "
        "are not a complete list of accessible projects or effective permissions. "
        "An omitted email is null with a visibility observation. Credentials and "
        "additional account metadata are excluded."
    ),
)
async def get_current_user(
    service: Annotated[UserService, Depends(get_users)],
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> CurrentUser:
    """Read the requesting user's basic profile and visible memberships."""
    return await service.get_current_user(context.principal.redmine_user_id)


@router.get(
    "/current/project-capabilities",
    operation_id="list_my_project_capabilities",
    response_model=MyProjectCapabilities,
    description=(
        "List visible projects with the requesting user's unique membership roles, merged "
        "project permissions and candidate tools. Permissions are the sorted unique union "
        "across all readable roles; any role can contribute a permission. "
        "Project read tools use feature-specific permission rules for issues, versions, "
        "categories, files, time entries and attachment containers. Visible project detail "
        "and positive read evidence are conditional; target visibility is checked on invocation. "
        "Uses the authenticated API key, not a user argument. "
        "For a named destination, resolve its ID with list_projects and pass project_id. "
        "Pass operation_id to return only that tool and matching projects; filters combine. "
        "Operation filtering defaults to conditional evidence; include_unknown=true also "
        "retains unknown candidates. Filtering happens before pagination. Filtered requests "
        "omit global tools. Without filters, all caller-visible projects are paginated. "
        "Disabled or denied writes are omitted. Conditional and unknown tools may still fail "
        "on invocation; Redmine owns final authorization. Global tools are listed separately. "
        "Tool entries contain operation_id and state by default. Set include_reasons=true "
        "only when explanations are requested. "
        "Use limit and offset for pagination. Permission evidence is known, partial or unknown; "
        "unknown permissions are null, and partial permissions include only readable roles."
    ),
)
async def list_my_project_capabilities(
    service: Annotated[ProjectCapabilityService, Depends(get_project_capabilities)],
    limit: Annotated[int, Query(ge=1, le=100, description="Projects per page")] = 25,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    include_reasons: Annotated[
        bool, Query(description="Include tool state explanations only when requested")
    ] = False,
    project_id: Annotated[
        int | None, Query(ge=1, description="Inspect only this caller-visible project")
    ] = None,
    operation_id: Annotated[
        str | None, Query(description="Return only projects matching this project-scoped tool")
    ] = None,
    include_unknown: Annotated[
        bool, Query(description="Include unknown candidates when filtering by operation_id")
    ] = False,
) -> MyProjectCapabilities:
    return await service.list_capabilities(
        limit,
        offset,
        include_reasons=include_reasons,
        project_id=project_id,
        operation_id=operation_id,
        include_unknown=include_unknown,
    )
