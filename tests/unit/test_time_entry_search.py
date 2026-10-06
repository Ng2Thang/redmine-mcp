"""Task 035 service validation must precede gateway dispatch."""

from datetime import date, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from redmine_mcp.common import InvalidInputError
from redmine_mcp.features.time_entries import TimeEntryService
from redmine_mcp.features.users.capability_service import read_tool

pytestmark = pytest.mark.asyncio


async def test_general_capability_needs_only_time_entry_permission() -> None:
    general = read_tool("list_time_entries", {"view_time_entries"})
    assert general.state == "conditional"
    assert read_tool("list_issue_time_entries", {"view_time_entries"}).state == "unknown"
    assert read_tool("list_time_entries", {"view_issues"}).state == "unknown"
    assert "No issue preflight" in general.reason


@pytest.mark.parametrize(
    "params",
    [{"project_id": value} for value in [0, -1, True, "7"]]
    + [{"issue_id": value} for value in [0, -1, True, "42"]]
    + [{"user_id": value} for value in [0, -1, True, "8", "all"]]
    + [
        {"include_subprojects": True},
        {"include_subprojects": "false"},
        {"limit": 0},
        {"limit": 101},
        {"limit": True},
        {"offset": -1},
        {"offset": False},
        {"spent_from": "2026-09-01"},
        {"spent_to": datetime(2026, 9, 30)},
        {"spent_from": date(2026, 10, 1), "spent_to": date(2026, 9, 30)},
    ],
)
async def test_invalid_search_does_not_dispatch(params: dict[str, Any]) -> None:
    reader = AsyncMock()
    with pytest.raises(InvalidInputError):
        await TimeEntryService(reader).list_time_entries(**params)
    reader.list_time_entries.assert_not_awaited()


@pytest.mark.parametrize("user_id", [None, 8, "me"])
async def test_service_forwards_typed_filters_and_defaults(user_id: Any) -> None:
    reader = AsyncMock()
    service = TimeEntryService(reader)
    assert await service.list_time_entries(user_id=user_id) is reader.list_time_entries.return_value
    reader.list_time_entries.assert_awaited_once_with(
        project_id=None,
        include_subprojects=False,
        user_id=user_id,
        issue_id=None,
        spent_from=None,
        spent_to=None,
        limit=25,
        offset=0,
    )
    reader.reset_mock()
    await service.list_time_entries(
        project_id=7,
        include_subprojects=True,
        user_id=user_id,
        issue_id=42,
        spent_from=date(2026, 9, 1),
        spent_to=date(2026, 9, 30),
        limit=100,
        offset=100,
    )
    reader.list_time_entries.assert_awaited_once_with(
        project_id=7,
        include_subprojects=True,
        user_id=user_id,
        issue_id=42,
        spent_from=date(2026, 9, 1),
        spent_to=date(2026, 9, 30),
        limit=100,
        offset=100,
    )
