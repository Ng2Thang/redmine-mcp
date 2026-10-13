"""Creation validates input and caller identity before any time is logged."""

from datetime import date, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from redmine_mcp.auth.capabilities import CapabilityService
from redmine_mcp.auth.capability_models import WriteIntent
from redmine_mcp.common import ApplicationError
from redmine_mcp.features.time_entries.service import TimeEntryService
from redmine_mcp.features.time_entries.write_models import TimeEntryCreateRequest
from tests.unit.test_capabilities import reader_for

BASE = {"hours": 1.5, "spent_on": "2026-10-01"}


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"hours": 1},
        {"spent_on": "2026-10-01"},
        *[
            {**BASE, "hours": value}
            for value in (None, 0, -1, True, "1.5", float("nan"), float("inf"), -float("inf"))
        ],
        *[
            {**BASE, "spent_on": value}
            for value in (
                None,
                "",
                "2026-02-29",
                "2026-1-2",
                "2026-10-01T00:00:00Z",
                date(2026, 10, 1),
                datetime(2026, 10, 1),
                1,
            )
        ],
        *[{**BASE, "activity_id": value} for value in (None, 0, -1, True, "9", 9.0)],
        *[{**BASE, "comments": value} for value in (None, 42, [], "x" * 1025)],
        *[
            {**BASE, field: value}
            for field, value in (
                ("user_id", 8),
                ("author_id", 8),
                ("project_id", 7),
                ("issue_id", 42),
                ("custom_fields", []),
                ("entries", []),
            )
        ],
    ],
)
def test_invalid_creation_fields(values: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        TimeEntryCreateRequest.model_validate(values)


@pytest.mark.parametrize(
    "values",
    [
        BASE,
        {"hours": 8, "spent_on": "2028-02-29"},
        {**BASE, "hours": 0.125},
        {**BASE, "activity_id": 9},
        {**BASE, "comments": ""},
        {**BASE, "comments": "x" * 1024},
        {**BASE, "comments": " exact text ", "activity_id": 10},
    ],
)
def test_optional_omissions_and_exact_supplied_values(values: dict[str, Any]) -> None:
    request = TimeEntryCreateRequest.model_validate(values)
    assert request.model_dump(mode="json", exclude_unset=True) == values


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["issue_id", "caller_id"])
@pytest.mark.parametrize("value", [0, -1, True, "3", 3.0])
async def test_invalid_identity_prevents_authorization_and_creation(field: str, value: Any) -> None:
    creator, authorizer = AsyncMock(), AsyncMock()
    ids = {"issue_id": 42, "caller_id": 3, field: value}
    service = TimeEntryService(
        AsyncMock(), creator=creator, authorizer=authorizer, caller_id=ids["caller_id"]
    )
    with pytest.raises(ApplicationError):
        await service.create_time_entry(ids["issue_id"], TimeEntryCreateRequest(**BASE))
    authorizer.authorize.assert_not_awaited()
    creator.create_time_entry.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("missing", ["creator", "caller"])
async def test_missing_dependencies_do_not_log_time(missing: str) -> None:
    creator, authorizer = AsyncMock(), AsyncMock()
    service = TimeEntryService(
        AsyncMock(),
        creator=None if missing == "creator" else creator,
        caller_id=None if missing == "caller" else 3,
        authorizer=authorizer,
    )
    with pytest.raises(RuntimeError):
        await service.create_time_entry(42, TimeEntryCreateRequest(**BASE))
    authorizer.authorize.assert_not_awaited()
    creator.create_time_entry.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("denied", [False, True])
async def test_creation_authorizes_issue_and_uses_authenticated_caller(denied: bool) -> None:
    creator, authorizer = AsyncMock(), AsyncMock()
    service = TimeEntryService(AsyncMock(), creator=creator, authorizer=authorizer, caller_id=3)
    request = TimeEntryCreateRequest(**BASE)
    if denied:
        authorizer.authorize.side_effect = ApplicationError("permission_denied", "denied", 403)
        with pytest.raises(ApplicationError):
            await service.create_time_entry(42, request)
        creator.create_time_entry.assert_not_awaited()
    else:
        assert (
            await service.create_time_entry(42, request) is creator.create_time_entry.return_value
        )
        creator.create_time_entry.assert_awaited_once_with(42, request, 3)
    authorizer.authorize.assert_awaited_once_with(WriteIntent("create_time_entry", issue_id=42))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permissions,expected",
    [
        (["log_time"], "conditional"),
        (["view_time_entries"], "denied"),
        (["edit_time_entries"], "denied"),
        ([], "denied"),
        (None, "unknown"),
    ],
)
async def test_creation_requires_log_time_evidence(permissions: Any, expected: str) -> None:
    service = CapabilityService(reader_for(permissions), 3)
    assert await service.project_operation("create_time_entry", 7) == expected
