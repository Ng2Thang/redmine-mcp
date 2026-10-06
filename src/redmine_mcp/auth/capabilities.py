"""Request-local necessary permission checks with explicit partial-evidence handling."""

import asyncio

from redmine_mcp.auth.capability_models import (
    CapabilityProfile,
    CapabilityState,
    PermissionClause,
    PermissionExpression,
    RolePermissions,
    WriteIntent,
)
from redmine_mcp.auth.capability_ports import CapabilityReader
from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import auth as auth_text
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text

ISSUE_EDIT_PERMISSIONS = frozenset({"edit_issues", "edit_own_issues"})
ISSUE_UPDATE_PERMISSIONS = ISSUE_EDIT_PERMISSIONS | {"add_issue_notes"}
UPLOAD_PERMISSIONS = frozenset(
    {
        "add_issues",
        "edit_issues",
        "edit_own_issues",
        "copy_issues",
        "add_issue_notes",
        "manage_news",
        "add_documents",
        "edit_documents",
        "manage_files",
        "edit_wiki_pages",
        "add_messages",
        "edit_messages",
        "edit_own_messages",
    }
)
OPERATION_PERMISSIONS: dict[str, frozenset[str]] = {
    "upload_attachment": UPLOAD_PERMISSIONS,
    "add_project_file": frozenset({"manage_files"}),
    "create_project_version": frozenset({"manage_versions"}),
    "add_project_members": frozenset({"manage_members"}),
    "update_project_members": frozenset({"manage_members"}),
    "delete_project_members": frozenset({"manage_members"}),
    "update_attachment": ISSUE_EDIT_PERMISSIONS | {"manage_files"},
    "delete_attachment": ISSUE_EDIT_PERMISSIONS | {"manage_files"},
    "create_issue": frozenset({"add_issues"}),
    "update_issue": ISSUE_UPDATE_PERMISSIONS,
    "update_issue_note": frozenset({"edit_issue_notes", "edit_own_issue_notes"}),
    "create_issue_relation": frozenset({"manage_issue_relations"}),
    "delete_issue_relation": frozenset({"manage_issue_relations"}),
    "add_issue_watcher": frozenset({"add_issue_watchers"}),
    "remove_issue_watcher": frozenset({"delete_issue_watchers"}),
}


def combine(states: tuple[CapabilityState, ...], *, conjunction: bool) -> CapabilityState:
    if conjunction:
        if "denied" in states:
            return "denied"
        return "unknown" if "unknown" in states else "conditional"
    if "conditional" in states:
        return "conditional"
    return "unknown" if "unknown" in states else "denied"


class CapabilityService:
    def __init__(
        self, reader: CapabilityReader, expected_user_id: int | None, deadline_seconds: float = 60
    ) -> None:
        self.reader = reader
        self.expected_user_id = expected_user_id
        self.deadline_seconds = deadline_seconds
        self._profile: CapabilityProfile | None = None
        self._roles: dict[int, RolePermissions | None] = {}

    def refresh(self) -> None:
        """Discard evidence that an earlier batch write may have invalidated."""
        self._profile = None
        self._roles.clear()

    async def profile(self) -> CapabilityProfile:
        if self._profile is None:
            profile = await self.reader.profile()
            if self.expected_user_id is not None and profile.user_id != self.expected_user_id:
                raise ApplicationError(
                    codes_text.UPSTREAM_RESPONSE, redmine_text.INVALID_RESPONSE, 502
                )
            self._profile = profile
        return self._profile

    async def clause(self, clause: PermissionClause) -> CapabilityState:
        profile = await self.profile()
        if profile.admin is True:
            return "conditional"
        if profile.memberships is None:
            return "unknown"
        memberships = tuple(
            item
            for item in profile.memberships
            if clause.project_id is None or item.project_id == clause.project_id
        )
        # Global roles include non-member defaults/overrides that the API cannot fully inventory.
        incomplete = profile.admin is None or clause.project_id is None or not memberships
        for membership in memberships:
            for role in membership.roles:
                permissions = await self.role(role.role_id)
                if permissions is None:
                    incomplete = True
                elif permissions.permissions & clause.alternatives:
                    return "conditional"
        return "unknown" if incomplete else "denied"

    async def role(self, role_id: int) -> RolePermissions | None:
        """Deduplicate role evidence only for the lifetime of this request."""
        if role_id not in self._roles:
            self._roles[role_id] = await self.reader.role(role_id)
        return self._roles[role_id]

    async def project_operation(self, operation: str, project_id: int | None) -> CapabilityState:
        """Necessary permission evidence, shared by discovery and capability reports."""
        return await self.clause(PermissionClause(project_id, OPERATION_PERMISSIONS[operation]))

    async def evaluate(self, expression: PermissionExpression) -> CapabilityState:
        branches: list[CapabilityState] = []
        for branch in expression.branches:
            clauses = tuple([await self.clause(clause) for clause in branch])
            branches.append(combine(clauses, conjunction=True))
        return combine(tuple(branches), conjunction=False)

    async def authorize(self, intent: WriteIntent) -> None:
        try:
            async with asyncio.timeout(self.deadline_seconds):
                profile = await self.profile()
                expression = await self.reader.resolve(intent, profile.user_id)
                if await self.evaluate(expression) == "denied":
                    raise ApplicationError(
                        codes_text.PERMISSION_DENIED, auth_text.PERMISSION_DENIED, 403
                    )
        except TimeoutError:
            raise ApplicationError(
                codes_text.UPSTREAM_TIMEOUT, redmine_text.TIMED_OUT, 504
            ) from None

    async def candidates(self, operations: tuple[str, ...]) -> frozenset[str]:
        try:
            async with asyncio.timeout(self.deadline_seconds):
                profile = await self.profile()
                if profile.admin is True:
                    return frozenset(operations)
                inventory = await self.reader.visible_projects()
                candidates: set[str] = set()
                for operation in operations:
                    if operation == "upload_attachment":
                        state = await self.project_operation(operation, None)
                    else:
                        states = tuple(
                            [
                                await self.project_operation(operation, project_id)
                                for project_id in inventory.project_ids
                            ]
                        )
                        if not inventory.complete or profile.admin is None:
                            states += ("unknown",)
                        state = combine(states, conjunction=False)
                    if state != "denied":
                        candidates.add(operation)
                return frozenset(candidates)
        except TimeoutError:
            raise ApplicationError(
                codes_text.UPSTREAM_TIMEOUT, redmine_text.TIMED_OUT, 504
            ) from None
