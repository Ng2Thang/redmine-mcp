"""TOOL-042 strict update inputs and service dispatch boundaries."""

from datetime import date, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from redmine_mcp.auth.capabilities import CapabilityService
from redmine_mcp.auth.capability_models import (
    CapabilityProfile,
    MembershipRole,
    ProjectMembership,
    RolePermissions,
    WriteIntent,
)
from redmine_mcp.common import ApplicationError
from redmine_mcp.features.time_entries.service import TimeEntryService
from redmine_mcp.features.time_entries.write_models import TimeEntryUpdateRequest


@pytest.mark.parametrize(
    "values",
    [
        {},
        *[{"hours": value} for value in (None, 0, -1, True, "1", float("nan"), float("inf"))],
        *[
            {"spent_on": value}
            for value in (
                None,
                "",
                "2026-02-29",
                "2026-1-2",
                "2026-10-08T00:00:00Z",
                date(2026, 10, 8),
                datetime(2026, 10, 8),
                8,
            )
        ],
        *[{"activity_id": value} for value in (None, 0, -1, True, "9", 9.0)],
        *[{"comments": value} for value in (None, 42, [], "x" * 1025)],
        *[
            {"hours": 1, field: value}
            for field, value in (
                ("user_id", 3),
                ("author_id", 3),
                ("project_id", 7),
                ("issue_id", 42),
                ("custom_fields", []),
                ("entries", []),
            )
        ],
    ],
)
def test_invalid_update_input(values: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        TimeEntryUpdateRequest.model_validate(values)


@pytest.mark.parametrize(
    "values",
    [
        {"hours": 1},
        {"hours": 0.125},
        {"spent_on": "2028-02-29"},
        {"activity_id": 9},
        {"comments": ""},
        {"comments": "x" * 1024},
        {"hours": 8, "spent_on": "2026-10-08", "activity_id": 10, "comments": " note "},
    ],
)
def test_supplied_fields_only_and_string_preservation(values: dict[str, Any]) -> None:
    request = TimeEntryUpdateRequest.model_validate(values)
    assert request.model_dump(mode="json", exclude_unset=True) == values


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["issue_id", "time_entry_id", "caller_id"])
@pytest.mark.parametrize("value", [0, -1, True, "3", 3.0])
async def test_bad_identity_prevents_authorization_and_dispatch(field: str, value: Any) -> None:
    updater, authorizer = AsyncMock(), AsyncMock()
    ids = {"issue_id": 42, "time_entry_id": 1, "caller_id": 3, field: value}
    service = TimeEntryService(
        AsyncMock(), updater=updater, authorizer=authorizer, caller_id=ids["caller_id"]
    )
    with pytest.raises(ApplicationError):
        await service.update_time_entry(
            ids["issue_id"], ids["time_entry_id"], TimeEntryUpdateRequest(hours=1)
        )
    authorizer.authorize.assert_not_awaited()
    updater.update_time_entry.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("denied", [False, True])
async def test_authorization_targets_exact_entry(denied: bool) -> None:
    updater, authorizer = AsyncMock(), AsyncMock()
    service = TimeEntryService(AsyncMock(), updater=updater, authorizer=authorizer, caller_id=3)
    request = TimeEntryUpdateRequest(comments="")
    if denied:
        authorizer.authorize.side_effect = ApplicationError("permission_denied", "denied", 403)
        with pytest.raises(ApplicationError):
            await service.update_time_entry(42, 1, request)
        updater.update_time_entry.assert_not_awaited()
    else:
        assert (
            await service.update_time_entry(42, 1, request)
            is updater.update_time_entry.return_value
        )
        updater.update_time_entry.assert_awaited_once_with(42, 1, request)
    authorizer.authorize.assert_awaited_once_with(
        WriteIntent("update_time_entry", issue_id=42, time_entry_id=1)
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permissions,expected",
    [
        (["edit_time_entries"], "conditional"),
        (["edit_own_time_entries"], "conditional"),
        (["log_time"], "denied"),
        ([], "denied"),
        (None, "unknown"),
    ],
)
async def test_project_candidates_require_edit_evidence(permissions: Any, expected: str) -> None:
    reader = AsyncMock()
    reader.profile.return_value = CapabilityProfile(
        3, False, (ProjectMembership(7, (MembershipRole(4),)),)
    )
    reader.role.return_value = (
        None
        if permissions is None
        else RolePermissions(4, frozenset(permissions), None, None, None)
    )
    assert await CapabilityService(reader, 3).project_operation("update_time_entry", 7) == expected
