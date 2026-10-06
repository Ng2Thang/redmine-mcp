from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import Field

from redmine_mcp.api import require_read_access, require_write_access
from redmine_mcp.api.dependencies import get_project_members
from redmine_mcp.features.projects.membership_models import (
    AddProjectMembersRequest,
    DeleteProjectMembersRequest,
    ListProjectMembersResult,
    MembershipBatchResult,
    UpdateProjectMembersRequest,
)
from redmine_mcp.features.projects.membership_service import ProjectMembershipService

Service = Annotated[ProjectMembershipService, Depends(get_project_members)]
router = APIRouter(prefix="/api/v1/projects", tags=["project memberships"])


@router.get(
    "/memberships",
    operation_id="list_project_members",
    response_model=ListProjectMembersResult,
    dependencies=[Depends(require_read_access)],
    description="List independent membership pages for one to ten projects. Includes users, "
    "groups and inherited roles. Redmine 7.0.2 public view_members remains subject to project "
    "access; manage_members is not required. Inspect each project's pagination_policy.",
)
async def list_project_members(
    service: Service,
    project_ids: Annotated[
        list[Annotated[int, Field(gt=0)]],
        Query(min_length=1, max_length=10, description="Unique positive numeric project IDs"),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ListProjectMembersResult:
    return await service.list_members(project_ids, limit, offset)


@router.post(
    "/memberships/batch",
    operation_id="add_project_members",
    response_model=MembershipBatchResult,
    dependencies=[Depends(require_write_access)],
    description="Add one to ten user memberships after whole-batch preflight. Existing "
    "memberships are explicitly rejected. Requires enabled writer, operation allowlist and "
    "project manage_members. Acceptance differs from read-back verification. Reconcile "
    "uncertain or interrupted outcomes; no automatic retries or rollback.",
)
async def add_project_members(
    request: AddProjectMembersRequest, service: Service
) -> MembershipBatchResult:
    return await service.manage("add", list(request.items))


@router.put(
    "/memberships/batch",
    operation_id="update_project_members",
    response_model=MembershipBatchResult,
    dependencies=[Depends(require_write_access)],
    description="Set requested roles on one to ten user memberships after whole-batch "
    "preflight. Validate the supplied project against the actual membership. Redmine preserves "
    "inherited and protected roles. Requires enabled writer, operation allowlist and project "
    "manage_members. Compare requested and observed roles; no automatic retries or rollback.",
)
async def update_project_members(
    request: UpdateProjectMembersRequest, service: Service
) -> MembershipBatchResult:
    return await service.manage("update", list(request.items))


@router.delete(
    "/memberships/batch",
    operation_id="delete_project_members",
    response_model=MembershipBatchResult,
    dependencies=[Depends(require_write_access)],
    description="Delete one to ten eligible user memberships after whole-batch preflight. "
    "Groups and inherited memberships are rejected. Requires enabled writer, operation "
    "allowlist and project manage_members; Redmine enforces managed-role restrictions. Native "
    "deletion may affect descendants and assignment defaults. Read-back must prove visible "
    "absence; a 404 or lost access is insufficient. No automatic retries or rollback.",
)
async def delete_project_members(
    request: DeleteProjectMembersRequest, service: Service
) -> MembershipBatchResult:
    return await service.manage("delete", list(request.items))
