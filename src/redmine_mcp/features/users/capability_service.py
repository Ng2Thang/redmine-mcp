"""Read the caller's project evidence without probing or executing tools."""

import asyncio
from typing import Literal

from fastapi import status as http_status

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS
from redmine_mcp.auth.capabilities import CapabilityService
from redmine_mcp.common import (
    ApplicationError,
    Page,
    PageRequest,
    require_positive_id,
    validated_query,
)
from redmine_mcp.common.pagination import PaginationGuard
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.projects.models import Project
from redmine_mcp.features.projects.ports import ProjectReader
from redmine_mcp.features.users.capability_models import (
    MyProjectCapabilities,
    ProjectCapability,
    ProjectRoleCapability,
    ToolCapability,
)
from redmine_mcp.features.users.capability_rules import PROJECT_READ_RULES

GLOBAL_READ_OPERATIONS = frozenset(
    {
        "get_current_user",
        "list_my_project_capabilities",
        "list_projects",
        "list_issue_statuses",
        "list_issue_priorities",
        "list_document_categories",
        "list_trackers",
    }
)


def read_tool(
    operation: str, permissions: set[str] | None = None, *, admin: bool = False
) -> ToolCapability:
    rule = PROJECT_READ_RULES.get(operation)
    if rule is not None and permissions is not None:
        if admin or any(branch <= permissions for branch in rule.branches):
            return ToolCapability(
                operation_id=operation,
                state="conditional",
                reason=(
                    "The caller is a Redmine administrator. "
                    if admin
                    else "Necessary project read evidence exists. "
                )
                + rule.constraint,
            )
        return ToolCapability(
            operation_id=operation,
            state="unknown",
            reason=(
                "Readable membership roles do not establish the required read permissions; "
                "Redmine decides access on invocation."
            ),
        )
    return ToolCapability(
        operation_id=operation,
        state="unknown",
        reason=(
            "Registered global read tool; access is checked by Redmine on invocation."
            if operation in GLOBAL_READ_OPERATIONS
            else "Project visibility alone does not establish resource access."
        ),
    )


class ProjectCapabilityService:
    def __init__(
        self,
        projects: ProjectReader,
        capabilities: CapabilityService,
        write_operations: tuple[str, ...],
        *,
        max_query_pages: int = 10,
    ) -> None:
        self.projects = projects
        self.capabilities = capabilities
        self.write_operations = write_operations
        self.pagination = PaginationGuard(max_query_pages)

    async def _write_tool(self, operation: str, project_id: int | None) -> ToolCapability | None:
        state = await self.capabilities.project_operation(operation, project_id)
        if state == "denied":
            if operation == "delete_issue_relation":
                # A relation can be authorized by either endpoint's project. This report
                # has no relation target, so a local denial cannot exclude the operation.
                return ToolCapability(
                    operation_id=operation,
                    state="unknown",
                    reason=(
                        "No necessary permission on this project; the other relation endpoint's "
                        "project may authorize deletion. Both endpoints are checked on invocation."
                    ),
                )
            return None
        return ToolCapability(
            operation_id=operation,
            state=state,
            reason=(
                (
                    "Manage versions permission evidence exists; Redmine checks the target project "
                    "and version validation on invocation. Version reads are optional and require "
                    "view_issues for verification or duplicate recovery."
                    if operation == "create_project_version"
                    else (
                        "Necessary permission evidence exists; target, tracker and workflow "
                        "checks remain."
                    )
                )
                if state == "conditional"
                else "Permission evidence is incomplete; Redmine decides on invocation."
            )
            + (
                " Manage members is necessary; managed-role authority is not exposed by "
                "the role API. Membership project, user type and inheritance are rechecked; "
                "Redmine preserves protected roles and enforces deletion restrictions."
                if operation
                in {"add_project_members", "update_project_members", "delete_project_members"}
                else ""
            ),
        )

    async def list_capabilities(
        self,
        limit: int = 25,
        offset: int = 0,
        *,
        include_reasons: bool = False,
        project_id: int | None = None,
        operation_id: str | None = None,
        include_unknown: bool = False,
    ) -> MyProjectCapabilities:
        query = validated_query(PageRequest, {"limit": limit, "offset": offset})
        self.pagination.check_depth(query.limit, query.offset, "Supply project_id to narrow scope")
        if project_id is not None:
            require_positive_id(project_id, "project_id")
        project_operations = (set(READ_OPERATIONS) - GLOBAL_READ_OPERATIONS) | (
            set(WRITE_OPERATIONS) - {"upload_attachment"}
        )
        if operation_id is not None and operation_id not in project_operations:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                "operation_id must name a project-scoped tool",
                http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        try:
            async with asyncio.timeout(self.capabilities.deadline_seconds):
                return await self._list_capabilities(
                    query,
                    include_reasons=include_reasons,
                    project_id=project_id,
                    operation_id=operation_id,
                    include_unknown=include_unknown,
                )
        except TimeoutError:
            raise ApplicationError(
                codes_text.UPSTREAM_TIMEOUT,
                redmine_text.TIMED_OUT,
                http_status.HTTP_504_GATEWAY_TIMEOUT,
            ) from None

    async def _project_page(
        self, query: PageRequest, project_id: int | None, operation_id: str | None
    ) -> Page[Project]:
        if project_id is not None:
            project = await self.projects.get_project(project_id)
            return Page[Project](items=[project], total=1, limit=query.limit, offset=query.offset)
        if operation_id is None:
            return await self.projects.list_projects(limit=query.limit, offset=query.offset)
        projects: list[Project] = []
        seen: set[int] = set()
        expected_total: int | None = None
        probe = await self.projects.list_projects(limit=1, offset=0)
        self.pagination.require_scope(probe.total, 100, "Supply project_id to narrow scope")
        for _ in range(self.pagination.max_pages):
            page = await self.projects.list_projects(limit=100, offset=len(projects))
            self.pagination.require_scope(page.total, 100, "Supply project_id to narrow scope")
            ids = [project.id for project in page.items]
            if (
                (expected_total is not None and page.total != expected_total)
                or len(set(ids)) != len(ids)
                or seen.intersection(ids)
                or (not ids and len(projects) < page.total)
                or len(projects) + len(ids) > page.total
            ):
                raise ApplicationError(
                    codes_text.UPSTREAM_RESPONSE,
                    redmine_text.UNEXPECTED_DATA,
                    http_status.HTTP_502_BAD_GATEWAY,
                )
            expected_total = page.total
            seen.update(ids)
            projects.extend(page.items)
            if len(projects) == expected_total:
                return Page[Project](
                    items=projects, total=expected_total, limit=query.limit, offset=query.offset
                )
        raise ApplicationError(
            "scope_required",
            "Project inventory exceeds the capability filter limit; supply project_id",
            http_status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    async def _list_capabilities(
        self,
        query: PageRequest,
        *,
        include_reasons: bool,
        project_id: int | None,
        operation_id: str | None,
        include_unknown: bool,
    ) -> MyProjectCapabilities:
        page = await self._project_page(query, project_id, operation_id)
        profile = await self.capabilities.profile()
        memberships = {item.project_id: item for item in profile.memberships or ()}
        items: list[ProjectCapability] = []
        for project in page.items:
            membership = memberships.get(project.id)
            roles_by_id: dict[int, ProjectRoleCapability] = {}
            permissions: set[str] = set()
            readable_roles = 0
            for role in membership.roles if membership else ():
                existing = roles_by_id.get(role.role_id)
                if existing is not None:
                    existing.inherited = existing.inherited and role.inherited
                    if existing.name is None:
                        existing.name = role.name
                    continue
                roles_by_id[role.role_id] = ProjectRoleCapability(
                    id=role.role_id,
                    name=role.name,
                    inherited=role.inherited,
                )
                evidence = await self.capabilities.role(role.role_id)
                if evidence is not None:
                    permissions.update(evidence.permissions)
                    readable_roles += 1
            permissions_state: Literal["known", "partial", "unknown"] = "unknown"
            if membership is not None and readable_roles == len(roles_by_id):
                permissions_state = "known"
            elif readable_roles:
                permissions_state = "partial"
            tools = [
                read_tool(operation, permissions, admin=profile.admin is True)
                for operation in READ_OPERATIONS
                if operation not in GLOBAL_READ_OPERATIONS
                and (operation_id is None or operation == operation_id)
            ]
            for operation in dict.fromkeys(self.write_operations):
                if operation != "upload_attachment" and (
                    operation_id is None or operation == operation_id
                ):
                    tool = await self._write_tool(operation, project.id)
                    if tool is not None:
                        tools.append(tool)
            if operation_id is not None:
                tools = [tool for tool in tools if include_unknown or tool.state == "conditional"]
                if not tools:
                    continue
            items.append(
                ProjectCapability(
                    id=project.id,
                    name=project.name,
                    roles=[roles_by_id[role_id] for role_id in sorted(roles_by_id)],
                    permissions=sorted(permissions) if permissions_state != "unknown" else None,
                    permissions_state=permissions_state,
                    membership_state="known" if membership is not None else "unknown",
                    tools=tools,
                )
            )
        global_tools = [
            read_tool(operation)
            for operation in READ_OPERATIONS
            if operation in GLOBAL_READ_OPERATIONS and operation_id is None and project_id is None
        ]
        if (
            project_id is None
            and operation_id is None
            and "upload_attachment" in self.write_operations
        ):
            tool = await self._write_tool("upload_attachment", None)
            if tool is not None:
                global_tools.append(tool)
        total = page.total
        if project_id is not None or operation_id is not None:
            total = len(items)
            items = items[query.offset : query.offset + query.limit]
        if not include_reasons:
            for project_capability in items:
                for tool in project_capability.tools:
                    tool.reason = None
            for tool in global_tools:
                tool.reason = None
        if query.offset:
            self.pagination.require_scope(total, query.limit, "Supply project_id to narrow scope")
        return MyProjectCapabilities(
            user_id=profile.user_id,
            items=items,
            total=total,
            limit=page.limit,
            offset=page.offset,
            visibility=page.visibility,
            global_tools=global_tools,
            pagination_policy=self.pagination.describe(total, query.limit),
        )
