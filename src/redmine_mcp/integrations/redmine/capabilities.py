"""Read partial capability evidence and resolve real write targets using the caller's key."""

from typing import Any

from redmine_mcp.auth.capabilities import (
    ISSUE_EDIT_PERMISSIONS,
    ISSUE_UPDATE_PERMISSIONS,
    UPLOAD_PERMISSIONS,
)
from redmine_mcp.auth.capability_models import (
    CapabilityProfile,
    MembershipRole,
    PermissionClause,
    PermissionExpression,
    ProjectInventory,
    ProjectMembership,
    RolePermissions,
    WriteIntent,
)
from redmine_mcp.common import ApplicationError, require_positive_id
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.attachments.models import AttachmentContainerRequest
from redmine_mcp.integrations.redmine.attachment_updates import RedmineAttachmentUpdates
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.responses import (
    resource_object,
    response_items,
    response_object,
    response_page,
)


def invalid_response() -> ApplicationError:
    return ApplicationError(codes_text.UPSTREAM_RESPONSE, redmine_text.UNEXPECTED_DATA, 502)


def positive_id(value: Any) -> int:
    if type(value) is not int or value < 1:
        raise invalid_response()
    return value


def reference_id(record: dict[str, Any], field: str) -> int:
    return positive_id(response_object(record.get(field)).get("id"))


def optional_reference_id(record: dict[str, Any], field: str) -> int | None:
    return None if record.get(field) is None else reference_id(record, field)


def target_id(value: int | None) -> int:
    if value is None:
        raise ApplicationError(codes_text.INVALID_PARAMETERS, "Missing authorization target", 422)
    require_positive_id(value, "target_id")
    return value


def own_alternatives(
    permissions: frozenset[str], own_permission: str, author_id: int | None, user_id: int
) -> frozenset[str]:
    # An omitted author cannot establish that an own-resource permission is inapplicable.
    return (
        permissions - {own_permission}
        if author_id is not None and author_id != user_id
        else permissions
    )


class RedmineCapabilities:
    def __init__(self, client: RedmineClient, containers: RedmineAttachmentUpdates) -> None:
        self.client = client
        self.containers = containers

    async def profile(self) -> CapabilityProfile:
        data = await self.client.get("users/current.json", {"include": "memberships"})
        user = response_object(data.get("user"))
        user_id = positive_id(user.get("id"))
        admin = user.get("admin")
        if "admin" in user and type(admin) is not bool:
            raise invalid_response()
        if "memberships" not in user:
            return CapabilityProfile(user_id, admin, None)
        memberships: list[ProjectMembership] = []
        seen: set[int] = set()
        for item in response_items(user, "memberships"):
            project_id = reference_id(item, "project")
            if project_id in seen:
                raise invalid_response()
            seen.add(project_id)
            roles: list[MembershipRole] = []
            for role in response_items(item, "roles"):
                inherited = role.get("inherited", False)
                if type(inherited) is not bool:
                    raise invalid_response()
                name = role.get("name")
                if name is not None and (not isinstance(name, str) or not name.strip()):
                    raise invalid_response()
                roles.append(MembershipRole(positive_id(role.get("id")), inherited, name))
            memberships.append(ProjectMembership(project_id, tuple(roles)))
        return CapabilityProfile(user_id, admin, tuple(memberships))

    async def role(self, role_id: int) -> RolePermissions | None:
        try:
            data = await self.client.get(f"roles/{role_id}.json", {})
        except ApplicationError as exc:
            if exc.status in (403, 404):
                return None
            raise
        role = resource_object(data.get("role"), role_id)
        permissions = role.get("permissions")
        if not isinstance(permissions, list) or any(
            not isinstance(item, str) or not item.strip() for item in permissions
        ):
            raise invalid_response()
        visibility: list[str | None] = []
        for field in ("issues_visibility", "time_entries_visibility", "users_visibility"):
            value = role.get(field)
            if value is not None and not isinstance(value, str):
                raise invalid_response()
            visibility.append(value)
        return RolePermissions(role_id, frozenset(permissions), *visibility)

    async def visible_projects(self) -> ProjectInventory:
        ids: dict[int, None] = {}
        offset = 0
        total: int | None = None
        probe = await self.client.get("projects.json", {"limit": 1, "offset": 0})
        metadata = response_page(probe, "projects", 1, 0, require_metadata=True)
        if self.client.pagination.describe(metadata.total, 100).requires_narrowing:
            return ProjectInventory((), False)
        for _ in range(self.client.policy.max_query_pages):
            data = await self.client.get("projects.json", {"limit": 100, "offset": offset})
            page = response_page(data, "projects", 100, offset, require_metadata=True)
            if self.client.pagination.describe(page.total, 100).requires_narrowing:
                return ProjectInventory(tuple(ids), False)
            if total is not None and page.total != total:
                return ProjectInventory(tuple(ids), False)
            total = page.total
            if not page.items and offset < total:
                raise invalid_response()
            new_ids = [positive_id(item.get("id")) for item in page.items]
            if len(set(new_ids)) != len(new_ids) or any(item in ids for item in new_ids):
                return ProjectInventory(tuple(ids), False)
            ids.update(dict.fromkeys(new_ids))
            if len(ids) > total:
                raise invalid_response()
            if len(ids) == total:
                return ProjectInventory(tuple(ids), True)
            offset += len(page.items)
        return ProjectInventory(tuple(ids), False)

    async def _project(self, project_id: int) -> int:
        data = await self.client.get(f"projects/{project_id}.json", {})
        resource_object(data.get("project"), project_id)
        return project_id

    async def _issue(self, issue_id: int, *, journals: bool = False) -> dict[str, Any]:
        data = await self.client.get(
            f"issues/{issue_id}.json", {"include": "journals"} if journals else {}
        )
        issue = resource_object(data.get("issue"), issue_id)
        reference_id(issue, "project")
        return issue

    async def _attachment_clause(self, intent: WriteIntent, user_id: int) -> PermissionClause:
        if intent.container_type is None:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS, "Missing attachment container", 422
            )
        container_id = target_id(intent.container_id)
        request = AttachmentContainerRequest(
            container_type=intent.container_type, container_id=container_id
        )
        await self.containers.require_container(target_id(intent.attachment_id), request)
        if intent.container_type == "issue":
            issue = await self._issue(container_id)
            permissions = own_alternatives(
                ISSUE_EDIT_PERMISSIONS,
                "edit_own_issues",
                optional_reference_id(issue, "author"),
                user_id,
            )
            return PermissionClause(reference_id(issue, "project"), permissions)
        project_id = container_id
        if intent.container_type == "version":
            data = await self.client.get(f"versions/{container_id}.json", {})
            project_id = reference_id(resource_object(data.get("version"), container_id), "project")
        return PermissionClause(project_id, frozenset({"manage_files"}))

    async def resolve(self, intent: WriteIntent, user_id: int) -> PermissionExpression:
        operation = intent.operation
        if operation == "upload_attachment":
            return PermissionExpression(((PermissionClause(None, UPLOAD_PERMISSIONS),),))
        if operation in ("update_attachment", "delete_attachment"):
            return PermissionExpression(((await self._attachment_clause(intent, user_id),),))
        if operation == "add_project_file":
            project_id = await self._project(target_id(intent.project_id))
            return PermissionExpression(
                ((PermissionClause(project_id, frozenset({"manage_files"})),),)
            )
        if operation == "create_project_version":
            project_id = await self._project(target_id(intent.project_id))
            return PermissionExpression(
                ((PermissionClause(project_id, frozenset({"manage_versions"})),),)
            )
        if operation == "create_issue":
            project_id = await self._project(target_id(intent.project_id))
            clauses = [PermissionClause(project_id, frozenset({"add_issues"}))]
            if intent.copy_from is not None:
                source = await self._issue(target_id(intent.copy_from))
                clauses.append(
                    PermissionClause(reference_id(source, "project"), frozenset({"copy_issues"}))
                )
            return PermissionExpression((tuple(clauses),))
        if operation == "delete_issue_relation":
            relation_id = target_id(intent.relation_id)
            data = await self.client.get(f"relations/{relation_id}.json", {})
            relation = resource_object(data.get("relation"), relation_id)
            endpoints = [positive_id(relation.get(field)) for field in ("issue_id", "issue_to_id")]
            branches = []
            for endpoint in endpoints:
                issue = await self._issue(endpoint)
                branches.append(
                    (
                        PermissionClause(
                            reference_id(issue, "project"), frozenset({"manage_issue_relations"})
                        ),
                    )
                )
            return PermissionExpression(tuple(branches))
        issue = await self._issue(
            target_id(intent.issue_id), journals=operation == "update_issue_note"
        )
        project_id = reference_id(issue, "project")
        if operation == "update_issue":
            if intent.project_id is not None:
                await self._project(target_id(intent.project_id))
            permissions = own_alternatives(
                ISSUE_UPDATE_PERMISSIONS,
                "edit_own_issues",
                optional_reference_id(issue, "author"),
                user_id,
            )
        elif operation == "update_issue_note":
            journal_id = target_id(intent.journal_id)
            journals = response_items(issue, "journals")
            for item in journals:
                positive_id(item.get("id"))
            journal = next((item for item in journals if item["id"] == journal_id), None)
            if journal is None:
                raise ApplicationError(
                    codes_text.RESOURCE_NOT_FOUND, redmine_text.RESOURCE_UNAVAILABLE, 404
                )
            permissions = own_alternatives(
                frozenset({"edit_issue_notes", "edit_own_issue_notes"}),
                "edit_own_issue_notes",
                optional_reference_id(journal, "user"),
                user_id,
            )
        elif operation == "create_issue_relation":
            permissions = frozenset({"manage_issue_relations"})
        elif operation == "add_issue_watcher":
            permissions = frozenset({"add_issue_watchers"})
        else:
            permissions = frozenset({"delete_issue_watchers"})
        return PermissionExpression(((PermissionClause(project_id, permissions),),))
