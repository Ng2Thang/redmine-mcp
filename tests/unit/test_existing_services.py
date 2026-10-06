"""Existing service and validation regressions, preserved from prep-004."""

import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from redmine_mcp.auth import READ_OPERATIONS, AuthenticationService, AuthorizationPolicy, Principal
from redmine_mcp.common import ApplicationError, InvalidInputError
from redmine_mcp.features.issues import IssueService
from redmine_mcp.features.projects import ProjectService
from redmine_mcp.features.time_entries import TimeEntryService
from redmine_mcp.integrations.redmine.responses import response_page

pytestmark = pytest.mark.asyncio


async def test_foundation_001_explicit_permission_policy() -> None:
    policy = AuthorizationPolicy(READ_OPERATIONS)
    for operation in READ_OPERATIONS:
        policy.authorize(Principal(3), f"read:{operation}")
    policy.authorize(Principal(3), "mcp:connect")
    for principal, permission in [
        (Principal(3), "read:unknown"),
        (Principal(3), "write:issues"),
        (Principal(True), "mcp:connect"),
    ]:
        with pytest.raises(ApplicationError) as error:
            policy.authorize(principal, permission)
        assert error.value.status == 403


@pytest.mark.parametrize(
    "changes",
    [
        {"total_count": "1"},
        {"total_count": True},
        {"total_count": -1},
        {"issues": [None]},
        {"issues": [{}, {}]},
        {"limit": True},
        {"limit": 2},
        {"offset": "0"},
        {"offset": 1},
    ],
)
async def test_foundation_006_strict_page_envelope(changes: dict[str, Any]) -> None:
    with pytest.raises(ApplicationError) as error:
        response_page({"issues": [{}], "total_count": 1, **changes}, "issues", 1, 0)
    assert (error.value.status, error.value.code) == (502, "upstream_response")


async def test_foundation_006_pages_do_not_infer_snapshot_completeness() -> None:
    assert response_page({"issues": [], "total_count": 5}, "issues", 1, 99).items == []
    assert response_page({"issues": [{}], "total_count": 0}, "issues", 2, 0).total == 0
    with pytest.raises(ApplicationError):
        response_page({"issues": [], "total_count": 0}, "issues", 1, 0, require_metadata=True)


@pytest.mark.parametrize(
    "params",
    [
        {"project_id": True},
        {"limit": False},
        {"offset": -1},
        {"limit": 101},
        {"status_id": "garbage"},
        {"sort": "subject:asc"},
        {"category_id": 1},
        {"include_subprojects": False},
        {"include_subprojects": "false"},
        {"updated_since": datetime(2026, 10, 1)},
        {"fixed_version_id": 0},
    ],
)
async def test_foundation_008_invalid_service_search_never_dispatch(params: dict[str, Any]) -> None:
    reader = AsyncMock()
    with pytest.raises(InvalidInputError):
        await IssueService(reader).list_issues(**params)
    reader.list_issues.assert_not_awaited()


@pytest.mark.parametrize("value", [True, 0, -1, "3"])
async def test_foundation_008_invalid_service_ids(value: Any) -> None:
    reader = AsyncMock()
    for call in [
        IssueService(reader).get_issue(value),
        ProjectService(reader).get_project(value),
        TimeEntryService(reader).list_issue_time_entries(value),
    ]:
        with pytest.raises(InvalidInputError):
            await call
    assert reader.mock_calls == []


@pytest.mark.parametrize("include", [("journals", "journals"), ("unknown",), ["journals"]])
async def test_foundation_008_invalid_service_includes(include: Any) -> None:
    reader = AsyncMock()
    with pytest.raises(InvalidInputError):
        await IssueService(reader).get_issue(42, include)
    reader.get_issue.assert_not_awaited()


async def test_foundation_010_concurrent_normalized_identity_binding() -> None:
    class Identity:
        async def current_principal(self, key: str) -> Principal:
            await asyncio.sleep(0)
            return Principal({"synthetic-a": 3, "synthetic-b": 8}[key])

    service = AuthenticationService(Identity())
    contexts = await asyncio.gather(
        service.authenticate(" synthetic-a "), service.authenticate("synthetic-b")
    )
    assert [(c.principal.redmine_user_id, c.api_key) for c in contexts] == [
        (3, "synthetic-a"),
        (8, "synthetic-b"),
    ]
    assert all(c.api_key not in repr(c) for c in contexts)
