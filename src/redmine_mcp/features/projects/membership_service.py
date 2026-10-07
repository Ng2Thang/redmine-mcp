"""Ordered batch orchestration with whole-batch preflight before any mutation."""

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError, validated_query
from redmine_mcp.common.read_budget import (
    MEMBERSHIP_BATCH_DEFAULTS,
    ReadBudget,
    ReadBudgetPolicy,
    current_budget,
)
from redmine_mcp.features.projects.membership_models import (
    AddMembershipItem,
    AddProjectMembersRequest,
    DeleteMembershipItem,
    DeleteProjectMembersRequest,
    ListProjectMembersRequest,
    ListProjectMembersResult,
    MembershipAction,
    MembershipBatchResult,
    MembershipError,
    MembershipWriteResult,
    ProjectMembersResult,
    UpdateMembershipItem,
    UpdateProjectMembersRequest,
)
from redmine_mcp.features.projects.membership_ports import (
    MembershipAuthorizer,
    MembershipGateway,
)

BatchItem = AddMembershipItem | UpdateMembershipItem | DeleteMembershipItem
STOP_CODES = frozenset(
    {
        "scan_budget_exceeded",
        "scope_required",
        "read_operation_timeout",
        "upstream_timeout",
        "upstream_unavailable",
        "upstream_busy",
    }
)


def safe_error(exc: ApplicationError) -> MembershipError:
    return MembershipError(code=exc.code, message=exc.message, status=exc.status)


def stopped_error(message: str) -> MembershipError:
    return MembershipError(code="batch_not_executed", message=message)


def stops_batch(error: MembershipError | None) -> bool:
    return error is not None and (
        error.status == http_status.HTTP_401_UNAUTHORIZED
        or error.status
        in (
            http_status.HTTP_502_BAD_GATEWAY,
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            http_status.HTTP_504_GATEWAY_TIMEOUT,
        )
        or error.code in STOP_CODES
    )


class ProjectMembershipService:
    def __init__(
        self,
        gateway: MembershipGateway,
        authorizer: MembershipAuthorizer,
        *,
        budget_policy: ReadBudgetPolicy = MEMBERSHIP_BATCH_DEFAULTS,
    ) -> None:
        self.gateway = gateway
        self.authorizer = authorizer
        self.budget_policy = budget_policy

    async def list_members(
        self, project_ids: list[int], limit: int = 25, offset: int = 0
    ) -> ListProjectMembersResult:
        query = validated_query(
            ListProjectMembersRequest,
            {"project_ids": project_ids, "limit": limit, "offset": offset},
        )
        results: list[ProjectMembersResult] = []
        stopped = False
        for project_id in query.project_ids:
            result = ProjectMembersResult(project_id=project_id, outcome="not_executed")
            results.append(result)
            if stopped:
                result.error = stopped_error("Shared read failure stopped this batch")
                continue
            try:
                result.page = await self.gateway.list_members(project_id, limit, offset)
                result.outcome = "read"
            except ApplicationError as exc:
                result.outcome = "rejected"
                result.error = safe_error(exc)
                # A project's page scope does not prevent reading other selected projects.
                stopped = exc.code != "scope_required" and stops_batch(result.error)
        return ListProjectMembersResult(results=results)

    async def _permission(self, action: MembershipAction, result: MembershipWriteResult) -> None:
        operation = {
            "add": "add_project_members",
            "update": "update_project_members",
            "delete": "delete_project_members",
        }[action]
        result.permission_state = await self.authorizer.project_operation(
            operation, result.project_id
        )
        if result.permission_state == "denied":
            raise ApplicationError(
                "permission_denied",
                "Project member management denied",
                http_status.HTTP_403_FORBIDDEN,
            )

    async def _target(
        self,
        action: MembershipAction,
        item: BatchItem,
        result: MembershipWriteResult,
        *,
        proved_projects: set[int] | None = None,
        proved_users: set[int] | None = None,
    ) -> None:
        if proved_projects is None or item.project_id not in proved_projects:
            await self.gateway.prove_project(item.project_id)
            if proved_projects is not None:
                proved_projects.add(item.project_id)
        if isinstance(item, AddMembershipItem):
            if proved_users is None or item.user_id not in proved_users:
                await self.gateway.prove_user(item.user_id)
                if proved_users is not None:
                    proved_users.add(item.user_id)
            existing = await self.gateway.existing(item.project_id, item.user_id)
            if existing is not None:
                result.membership_id = existing.id
                result.observed_membership = existing
                result.observed_present = True
                raise ApplicationError(
                    "membership_already_exists",
                    "Membership exists; use update explicitly",
                    http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                )
        else:
            member = await self.gateway.membership(item.membership_id)
            if member.project.id != item.project_id:
                raise ApplicationError(
                    "invalid_parameters",
                    "Membership project mismatch",
                    http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                )
            if member.user is None:
                raise ApplicationError(
                    "invalid_parameters",
                    "Group writes are unsupported",
                    http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                )
            result.user_id = member.user.id
            if action == "delete" and any(role.inherited for role in member.roles):
                raise ApplicationError(
                    "inherited_membership",
                    "Inherited memberships cannot be deleted",
                    http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                )

    async def manage(
        self, action: MembershipAction, items: list[BatchItem]
    ) -> MembershipBatchResult:
        # Validate before upstream access even when called outside the REST adapter.
        data = {"items": [item.model_dump() for item in items]}
        if action == "add":
            validated_query(AddProjectMembersRequest, data)
        elif action == "update":
            validated_query(UpdateProjectMembersRequest, data)
        else:
            validated_query(DeleteProjectMembersRequest, data)
        # Count all preflight/rechecks/read-backs in one bounded scope. Avoid an outer
        # cancellation deadline that would erase receipts after a mutation succeeded.
        token = current_budget.set(ReadBudget(self.budget_policy))
        try:
            return await self._manage(action, items)
        finally:
            current_budget.reset(token)

    async def _manage(
        self, action: MembershipAction, items: list[BatchItem]
    ) -> MembershipBatchResult:
        results = [
            MembershipWriteResult(
                index=index,
                project_id=item.project_id,
                membership_id=item.membership_id
                if isinstance(item, DeleteMembershipItem)
                else None,
                user_id=item.user_id if isinstance(item, AddMembershipItem) else None,
                requested_role_ids=item.role_ids
                if isinstance(item, (AddMembershipItem, UpdateMembershipItem))
                else None,
            )
            for index, item in enumerate(items)
        ]
        roles: set[int] | None = None
        proved_projects: set[int] = set()
        proved_users: set[int] = set()
        stopped = False
        failed = False
        for item, result in zip(items, results, strict=True):
            if stopped:
                result.error = stopped_error("Preflight could not complete")
                continue
            try:
                await self._permission(action, result)
                await self._target(
                    action,
                    item,
                    result,
                    proved_projects=proved_projects,
                    proved_users=proved_users,
                )
                if result.requested_role_ids is not None:
                    if roles is None:
                        roles = await self.gateway.role_ids()
                    if not set(result.requested_role_ids) <= roles:
                        raise ApplicationError(
                            "invalid_parameters",
                            "Unknown role ID",
                            http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                        )
            except ApplicationError as exc:
                failed = True
                result.outcome = "rejected"
                result.error = safe_error(exc)
                stopped = stops_batch(result.error)
        if failed:
            for result in results:
                if result.outcome == "not_executed" and result.error is None:
                    result.error = stopped_error("Another item failed whole-batch preflight")
            return MembershipBatchResult(phase="preflight_failed", results=results)
        # Execution must obtain fresh proof even for targets already seen in preflight.
        proved_projects.clear()
        proved_users.clear()
        stopped = False
        for item, result in zip(items, results, strict=True):
            if stopped:
                result.error = stopped_error("Shared execution failure stopped this batch")
                continue
            try:
                # Refresh request-local evidence: earlier writes may revoke the caller's roles.
                self.authorizer.refresh()
                await self._permission(action, result)
                await self._target(action, item, result)
                await self.gateway.write(action, result)
                stopped = result.outcome == "uncertain" or stops_batch(result.error)
            except ApplicationError as exc:
                result.outcome = "rejected"
                result.error = safe_error(exc)
                stopped = stops_batch(result.error)
        return MembershipBatchResult(phase="executed", results=results)
