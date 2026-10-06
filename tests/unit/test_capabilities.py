"""Partial permission evidence must never become an invented effective grant."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from redmine_mcp.auth.capabilities import CapabilityService
from redmine_mcp.auth.capability_models import (
    CapabilityProfile,
    MembershipRole,
    PermissionClause,
    ProjectInventory,
    ProjectMembership,
    RolePermissions,
)
from redmine_mcp.common import ApplicationError
from redmine_mcp.common.pagination import Page
from redmine_mcp.features.projects.models import Project
from redmine_mcp.features.users.capability_service import ProjectCapabilityService


def reader_for(permissions: Any, *, admin: Any = False, memberships: Any = True) -> Any:
    reader = AsyncMock()
    reader.profile.return_value = CapabilityProfile(
        3, admin, (ProjectMembership(7, (MembershipRole(4),)),) if memberships else ()
    )
    reader.role.return_value = (
        None
        if permissions is None
        else RolePermissions(4, frozenset(permissions), None, None, None)
    )
    reader.visible_projects.return_value = ProjectInventory((7,), True)
    return reader


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permissions,admin,memberships,expected",
    [
        ([], False, True, "denied"),
        (["add_issues"], False, True, "conditional"),
        (None, False, True, "unknown"),
        ([], False, False, "unknown"),
        ([], None, True, "unknown"),
        ([], True, True, "conditional"),
    ],
)
async def test_complete_and_partial_permission_evidence(
    permissions: Any, admin: Any, memberships: Any, expected: Any
) -> None:
    reader = reader_for(permissions, admin=admin, memberships=memberships)
    service = CapabilityService(reader, 3)
    clause = PermissionClause(7, frozenset({"add_issues"}))
    assert await service.clause(clause) == expected
    assert await service.clause(clause) == expected
    reader.profile.assert_awaited_once()
    assert reader.role.await_count <= 1


@pytest.mark.asyncio
async def test_identity_mismatch_is_rejected() -> None:
    with pytest.raises(ApplicationError) as error:
        await CapabilityService(reader_for([]), 8).profile()
    assert error.value.status == 502


@pytest.mark.asyncio
async def test_incomplete_inventory_preserves_candidates() -> None:
    reader = reader_for([])
    reader.visible_projects.return_value = ProjectInventory((), False)
    assert await CapabilityService(reader, 3).candidates(("create_issue",)) == {"create_issue"}


@pytest.mark.asyncio
async def test_capability_report_deduplicates_roles_merges_permissions_and_hides_reasons() -> None:
    reader = reader_for(["add_issues", "view_issues"])
    reader.profile.return_value = CapabilityProfile(
        3,
        False,
        (
            ProjectMembership(
                7,
                (
                    MembershipRole(4, True, "Author"),
                    MembershipRole(4, False, "Author"),
                    MembershipRole(5, False, "Files"),
                ),
            ),
        ),
    )

    async def role(role_id: Any) -> Any:
        return RolePermissions(
            role_id,
            frozenset({"add_issues", "view_issues"} if role_id == 4 else {"manage_files"}),
            None,
            None,
            None,
        )

    reader.role.side_effect = role
    projects = AsyncMock()
    projects.get_project.return_value = Project(id=7, identifier="demo", name="Demo", status=1)
    service = ProjectCapabilityService(
        projects, CapabilityService(reader, 3), ("create_issue", "add_project_file")
    )
    result = await service.list_capabilities(project_id=7)
    item = result.items[0]
    assert [r.id for r in item.roles] == [4, 5]
    assert item.roles[0].inherited is False
    assert item.permissions == ["add_issues", "manage_files", "view_issues"]
    assert all(tool.reason is None for tool in item.tools)
    assert reader.role.await_count == 2
    assert result.global_tools == []


@pytest.mark.asyncio
async def test_filtered_capability_inventory_stops_at_probe() -> None:
    projects = AsyncMock()
    projects.list_projects.return_value = Page(items=[], total=1000000, limit=1, offset=0)
    service = ProjectCapabilityService(projects, CapabilityService(reader_for([]), 3), ())
    with pytest.raises(ApplicationError) as error:
        await service.list_capabilities(operation_id="get_issue")
    assert error.value.code == "scope_required"
    projects.list_projects.assert_awaited_once_with(limit=1, offset=0)
