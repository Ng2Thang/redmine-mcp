"""TOOL-033 validation, orchestration and dispatch-deadline regressions."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from pydantic import ValidationError

from redmine_mcp.auth.capabilities import CapabilityService
from redmine_mcp.auth.capability_models import (
    CapabilityProfile,
    MembershipRole,
    RolePermissions,
)
from redmine_mcp.auth.capability_models import (
    ProjectMembership as CallerMembership,
)
from redmine_mcp.common import ApplicationError
from redmine_mcp.common.read_budget import ReadBudget, ReadBudgetPolicy, current_budget
from redmine_mcp.features.projects.membership_models import (
    AddMembershipItem,
    AddProjectMembersRequest,
    DeleteProjectMembersRequest,
    ListProjectMembersRequest,
    ProjectMembership,
    UpdateProjectMembersRequest,
)
from redmine_mcp.features.projects.membership_service import ProjectMembershipService
from redmine_mcp.integrations.redmine.transport import AdmittedTransport
from tests.membership_helpers import membership


@pytest.mark.parametrize("value", [0, -1, True, "7", 7.0, None])
@pytest.mark.parametrize("field", ["project_id", "user_id", "role_ids"])
def test_strict_write_ids(value: Any, field: str) -> None:
    values = {"project_id": 7, "user_id": 10, "role_ids": [4]}
    values[field] = [value] if field == "role_ids" else value
    with pytest.raises(ValidationError):
        AddMembershipItem.model_validate(values)


@pytest.mark.parametrize(
    "model", [AddProjectMembersRequest, UpdateProjectMembersRequest, DeleteProjectMembersRequest]
)
@pytest.mark.parametrize("case", ["empty", "eleven", "duplicate", "extra", "bad_id"])
def test_batch_bounds_and_unique_targets(model: Any, case: str) -> None:
    item = {"project_id": 7, "membership_id": 20}
    if model is AddProjectMembersRequest:
        item = {"project_id": 7, "user_id": 10, "role_ids": [4]}
    elif model is UpdateProjectMembersRequest:
        item["role_ids"] = [4]
    values = {"items": [item]}
    if case == "empty":
        values["items"] = []
    elif case == "eleven":
        key = "user_id" if model is AddProjectMembersRequest else "membership_id"
        values["items"] = [{**item, key: n} for n in range(1, 12)]
    elif case == "duplicate":
        values["items"] = [item, item.copy()]
    elif case == "extra":
        values["items"] = [{**item, "group_id": 12}]
    else:
        values["items"] = [{**item, "project_id": True}]
    with pytest.raises(ValidationError):
        model.model_validate(values)


@pytest.mark.parametrize("model", [AddProjectMembersRequest, UpdateProjectMembersRequest])
@pytest.mark.parametrize("roles", [[], [4, 4], [True], [0]])
def test_requested_roles_are_nonempty_unique_ids(model: Any, roles: Any) -> None:
    item = {"project_id": 7, "role_ids": roles}
    item["user_id" if model is AddProjectMembersRequest else "membership_id"] = 20
    with pytest.raises(ValidationError):
        model.model_validate({"items": [item]})


@pytest.mark.parametrize("projects", [[], [7, 7], list(range(1, 12)), [True], ["7"], [0]])
def test_list_scope_validation(projects: Any) -> None:
    with pytest.raises(ValidationError):
        ListProjectMembersRequest(project_ids=projects)


@pytest.mark.parametrize("group", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
def test_repeated_native_roles_keep_any_inheritance(group: bool, reverse: bool) -> None:
    raw = membership(group=group)
    roles = [raw["roles"][0], {**raw["roles"][0], "inherited": True}]
    raw["roles"] = list(reversed(roles)) if reverse else roles
    member = ProjectMembership.model_validate(raw)
    assert len(member.roles) == 1 and member.roles[0].inherited is True
    assert (member.group is not None) is group


@pytest.mark.parametrize(
    "change",
    [
        {"user": None},
        {"group": {"id": 12, "name": "Group"}},
        {"roles": None},
        {"roles": [{"id": 4, "name": "Role", "inherited": "true"}]},
        {"roles": [{"id": 4, "name": "A"}, {"id": 4, "name": "B"}]},
    ],
)
def test_malformed_native_membership(change: Any) -> None:
    with pytest.raises(ValidationError):
        ProjectMembership.model_validate({**membership(), **change})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation", ["add_project_members", "update_project_members", "delete_project_members"]
)
@pytest.mark.parametrize(
    "permissions,admin,expected",
    [
        (["manage_members"], False, "conditional"),
        (["view_members"], False, "denied"),
        (None, False, "unknown"),
        ([], True, "conditional"),
    ],
)
async def test_manage_members_permission(
    operation: str, permissions: Any, admin: bool, expected: str
) -> None:
    reader = AsyncMock()
    reader.profile.return_value = CapabilityProfile(
        3, admin, (CallerMembership(7, (MembershipRole(4, True), MembershipRole(5))),)
    )
    reader.role.return_value = (
        None
        if permissions is None
        else RolePermissions(4, frozenset(permissions), None, None, None)
    )
    service = CapabilityService(reader, 3)
    assert await service.project_operation(operation, 7) == expected
    service.refresh()
    reader.role.return_value = RolePermissions(4, frozenset(), None, None, None)
    assert await service.project_operation(operation, 7) == ("conditional" if admin else "denied")
    assert reader.profile.await_count == 2


@pytest.mark.asyncio
async def test_permission_merge_uses_all_caller_roles() -> None:
    reader = AsyncMock()
    reader.profile.return_value = CapabilityProfile(
        3, False, (CallerMembership(7, (MembershipRole(4), MembershipRole(5, True))),)
    )
    reader.role.side_effect = lambda n: RolePermissions(
        n, frozenset({"manage_members"} if n == 5 else set()), None, None, None
    )
    assert (
        await CapabilityService(reader, 3).project_operation("add_project_members", 7)
        == "conditional"
    )


@pytest.mark.asyncio
async def test_whole_batch_permission_preflight_and_budget_reset() -> None:
    gateway, authorizer = AsyncMock(), AsyncMock()
    gateway.existing.return_value = None
    gateway.role_ids.return_value = {4}
    authorizer.project_operation.side_effect = ["conditional", "denied"]
    items = [AddMembershipItem(project_id=p, user_id=10, role_ids=[4]) for p in (7, 8)]
    outer = ReadBudget(ReadBudgetPolicy())
    token = current_budget.set(outer)
    try:
        result = await ProjectMembershipService(gateway, authorizer).manage("add", items)
        assert current_budget.get() is outer
    finally:
        current_budget.reset(token)
    assert result.phase == "preflight_failed"
    assert [r.outcome for r in result.results] == ["not_executed", "rejected"]
    gateway.write.assert_not_awaited()
    authorizer.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_interruption_propagates_and_no_later_item_or_rollback() -> None:
    gateway, authorizer = AsyncMock(), AsyncMock()
    authorizer.refresh = Mock()
    gateway.existing.return_value = None
    gateway.role_ids.return_value = {4}
    authorizer.project_operation.return_value = "conditional"
    started = asyncio.Event()

    async def interrupted(action: Any, result: Any) -> None:
        started.set()
        await asyncio.Event().wait()

    gateway.write.side_effect = interrupted
    service = ProjectMembershipService(gateway, authorizer)
    task = asyncio.create_task(
        service.manage(
            "add", [AddMembershipItem(project_id=7, user_id=n, role_ids=[4]) for n in (12, 13)]
        )
    )
    await asyncio.wait_for(started.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    gateway.write.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code,status,expected",
    [
        ("scope_required", 422, ["rejected", "read"]),
        ("access_denied", 403, ["rejected", "read"]),
        ("invalid_credentials", 401, ["rejected", "not_executed"]),
        ("scan_budget_exceeded", 422, ["rejected", "not_executed"]),
    ],
)
async def test_list_local_and_shared_failures(code: str, status: int, expected: Any) -> None:
    from redmine_mcp.common import Page

    gateway = AsyncMock()
    gateway.list_members.side_effect = [
        ApplicationError(code, "Safe error", status),
        Page(items=[], total=0, limit=25, offset=0),
    ]
    result = await ProjectMembershipService(gateway, AsyncMock()).list_members([7, 8])
    assert [r.outcome for r in result.results] == expected
    assert gateway.list_members.await_count == (2 if expected[1] == "read" else 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
async def test_deadline_expired_while_queued_never_dispatches_and_releases_permit(
    method: str,
) -> None:
    acquired = asyncio.Event()

    class ObservableSemaphore(asyncio.Semaphore):
        async def acquire(self) -> bool:
            acquired.set()
            return await super().acquire()

    semaphore = ObservableSemaphore(0)
    inner = AsyncMock(spec=httpx.AsyncBaseTransport)
    transport = AdmittedTransport(inner, semaphore, 2)
    budget = ReadBudget(ReadBudgetPolicy(deadline_seconds=90))
    request = httpx.Request(method, "http://redmine.invalid/memberships/20.json")
    token = current_budget.set(budget)
    try:
        task = asyncio.create_task(transport.handle_async_request(request))
        await asyncio.wait_for(acquired.wait(), 2)
        budget.started -= 100
        semaphore.release()
        with pytest.raises(ApplicationError) as error:
            await task
        assert error.value.code == "read_operation_timeout"
        assert request.extensions["redmine_dispatched"] is False
        inner.handle_async_request.assert_not_awaited()
        await asyncio.wait_for(semaphore.acquire(), 2)
        semaphore.release()
    finally:
        current_budget.reset(token)
