"""Native response and interruption regressions without application startup."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from redmine_mcp.features.projects.membership_models import MembershipWriteResult
from redmine_mcp.integrations.redmine.project_memberships import RedmineProjectMemberships
from redmine_mcp.integrations.redmine.write import WriteReceipt
from tests.membership_helpers import membership


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["add", "update"])
async def test_native_repeated_roles_normalized_in_accepted_readback(action: str) -> None:
    raw = membership()
    raw["roles"].append({**raw["roles"][0], "inherited": True})
    client, writer = AsyncMock(), AsyncMock()
    client.get.return_value = {"membership": raw}
    writer.write_json.return_value = WriteReceipt("accepted", payload={"membership": raw})
    gateway = RedmineProjectMemberships(client, writer)
    result = MembershipWriteResult(
        index=0, project_id=7, membership_id=20, user_id=10, requested_role_ids=[4]
    )
    await gateway.write(action, result)
    assert result.outcome == "accepted" and result.verification == "matched"
    assert result.observed_membership is not None
    assert len(result.observed_membership.roles) == 1
    assert result.observed_membership.roles[0].inherited is True
    writer.write_json.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        {"id": True},
        {"project": {"id": 8, "name": "Other"}},
        {"user": {"id": 11, "name": "Other"}},
        {"roles": None},
    ],
)
async def test_invalid_create_receipt_keeps_acceptance_without_false_verification(
    change: Any,
) -> None:
    client, writer = AsyncMock(), AsyncMock()
    writer.write_json.return_value = WriteReceipt(
        "accepted", payload={"membership": {**membership(), **change}}
    )
    result = MembershipWriteResult(index=0, project_id=7, user_id=10, requested_role_ids=[4])
    await RedmineProjectMemberships(client, writer).write("add", result)
    assert result.outcome == "accepted" and result.verification == "unavailable"
    assert result.error is not None and result.error.code == "upstream_response"
    client.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancellation_marks_inflight_result_uncertain_and_propagates() -> None:
    client, writer = AsyncMock(), AsyncMock()
    started = asyncio.Event()

    async def dispatch(*args: Any, **kwargs: Any) -> Any:
        started.set()
        await asyncio.Event().wait()

    writer.write_json.side_effect = dispatch
    gateway = RedmineProjectMemberships(client, writer)
    result = MembershipWriteResult(
        index=0, project_id=7, membership_id=20, user_id=10, requested_role_ids=[4]
    )
    task = asyncio.create_task(gateway.write("update", result))
    await asyncio.wait_for(started.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert result.outcome == "uncertain"
    assert result.error is not None and result.error.code == "write_interrupted"
    assert result.verification == "unavailable"
    writer.write_json.assert_awaited_once()
    client.get.assert_not_awaited()
