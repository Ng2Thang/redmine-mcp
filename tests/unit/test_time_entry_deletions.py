"""TOOL-043 service, receipt and response-cleanup regression boundaries."""

from typing import Any
from unittest.mock import AsyncMock

import httpx
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
from redmine_mcp.features.time_entries.write_models import TimeEntryDeleteResult
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.time_entry_deletions import RedmineTimeEntryDeletions
from redmine_mcp.integrations.redmine.write import RedmineWriter, WriteReceipt


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["issue_id", "time_entry_id", "caller_id"])
@pytest.mark.parametrize("value", [0, -1, True, "3", 3.0])
async def test_invalid_identity_prevents_authorization_and_delete(field: str, value: Any) -> None:
    deleter, authorizer = AsyncMock(), AsyncMock()
    ids = {"issue_id": 42, "time_entry_id": 1, "caller_id": 3, field: value}
    service = TimeEntryService(
        AsyncMock(), deleter=deleter, authorizer=authorizer, caller_id=ids["caller_id"]
    )
    with pytest.raises(ApplicationError):
        await service.delete_time_entry(ids["issue_id"], ids["time_entry_id"])
    authorizer.authorize.assert_not_awaited()
    deleter.delete_time_entry.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("missing", ["deleter", "caller"])
async def test_missing_configuration_prevents_delete(missing: str) -> None:
    deleter = AsyncMock()
    service = TimeEntryService(
        AsyncMock(),
        deleter=None if missing == "deleter" else deleter,
        caller_id=None if missing == "caller" else 3,
    )
    with pytest.raises(RuntimeError):
        await service.delete_time_entry(42, 1)
    deleter.delete_time_entry.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("denied", [False, True])
async def test_authorization_targets_exact_entry(denied: bool) -> None:
    deleter, authorizer = AsyncMock(), AsyncMock()
    service = TimeEntryService(AsyncMock(), deleter=deleter, authorizer=authorizer, caller_id=3)
    if denied:
        authorizer.authorize.side_effect = ApplicationError("permission_denied", "denied", 403)
        with pytest.raises(ApplicationError):
            await service.delete_time_entry(42, 1)
        deleter.delete_time_entry.assert_not_awaited()
    else:
        assert await service.delete_time_entry(42, 1) is deleter.delete_time_entry.return_value
        deleter.delete_time_entry.assert_awaited_once_with(42, 1)
    authorizer.authorize.assert_awaited_once_with(
        WriteIntent("delete_time_entry", issue_id=42, time_entry_id=1)
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
    assert await CapabilityService(reader, 3).project_operation("delete_time_entry", 7) == expected


@pytest.mark.parametrize(
    "field,value",
    [
        ("resource_id", True),
        ("issue_id", "42"),
        ("observed_present", 1),
        ("verification", "matched"),
    ],
)
def test_receipt_rejects_invalid_id_or_observation(field: str, value: Any) -> None:
    with pytest.raises(ValidationError):
        TimeEntryDeleteResult.model_validate(
            {
                "outcome": "accepted",
                "upstream_accepted": True,
                "resource_id": 1,
                "issue_id": 42,
                field: value,
            }
        )


def visible_client() -> Any:
    client = AsyncMock()
    client.get.side_effect = [
        {
            "time_entry": {
                "id": 1,
                "issue": {"id": 42},
                "project": {"id": 7, "name": "P"},
                "user": {"id": 3, "name": "U"},
                "hours": 1,
                "spent_on": "2026-10-01",
            }
        },
        {"issue": {"id": 42, "project": {"id": 7}}},
        ApplicationError("resource_not_found", "not found", 404),
    ]
    return client


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [204, 500, None])
async def test_uncertain_transport_receipt_with_received_204_preserves_acceptance(
    status: int | None,
) -> None:
    writer = AsyncMock()
    writer.write_json.return_value = WriteReceipt("uncertain", status)
    result = await RedmineTimeEntryDeletions(visible_client(), writer).delete_time_entry(42, 1)
    assert result.outcome == ("accepted" if status == 204 else "uncertain")
    assert result.upstream_accepted is (True if status == 204 else None)
    assert result.verification == "not_found" and result.observed_present is False
    writer.write_json.assert_awaited_once_with(
        "DELETE", "time_entries/1.json", accepted_statuses=(204,)
    )


@pytest.mark.asyncio
async def test_actual_response_close_error_after_204_does_not_lose_acceptance() -> None:
    requests = []

    class BrokenCleanup(httpx.AsyncByteStream):
        async def __aiter__(self) -> Any:
            yield b""

        async def aclose(self) -> None:
            raise httpx.ReadError("private cleanup failure")

    async def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(204, stream=BrokenCleanup())

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        writer = RedmineWriter(http, "offline-key", ReadPolicy())
        result = await RedmineTimeEntryDeletions(visible_client(), writer).delete_time_entry(42, 1)
    assert result.outcome == "accepted" and result.upstream_accepted is True
    assert result.verification == "not_found" and len(requests) == 1
    assert requests[0].method == "DELETE" and requests[0].content == b""
