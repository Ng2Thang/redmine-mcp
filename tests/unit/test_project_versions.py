"""Target version validation and permission boundaries without HTTP or credentials."""

from datetime import date, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from redmine_mcp.auth.capabilities import CapabilityService
from redmine_mcp.auth.capability_models import WriteIntent
from redmine_mcp.common import ApplicationError
from redmine_mcp.features.projects.models import CreateProjectVersionRequest
from redmine_mcp.features.projects.service import ProjectService
from tests.unit.test_capabilities import reader_for


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"name": ""},
        {"name": " \t\n"},
        {"name": "x" * 61},
        {"name": None},
        {"name": 7},
        {"name": "x", "description": "x" * 256},
        {"name": "x", "due_date": ""},
        {"name": "x", "due_date": "2026-02-29"},
        {"name": "x", "due_date": "2026-10-20T00:00:00Z"},
        {"name": "x", "due_date": "2026-1-2"},
        {"name": "x", "due_date": date(2026, 10, 20)},
        {"name": "x", "due_date": datetime(2026, 10, 20)},
        {"name": "x", "due_date": 0},
        {"name": "x", "status": "closed"},
        {"name": "x", "sharing": "system"},
    ],
)
def test_invalid_creation_fields(values: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        CreateProjectVersionRequest.model_validate(values)


def test_name_preservation_and_optional_fields() -> None:
    request = CreateProjectVersionRequest(name=" Sprint-01 ", description="", due_date="2028-02-29")
    assert request.model_dump(mode="json", exclude_none=True) == {
        "name": " Sprint-01 ",
        "description": "",
        "due_date": "2028-02-29",
    }
    for values in ({"name": "x"}, {"name": "x", "description": None, "due_date": None}):
        assert CreateProjectVersionRequest(**values).model_dump(mode="json", exclude_none=True) == {
            "name": "x"
        }
    assert len(CreateProjectVersionRequest(name="x" * 60, description="x" * 255).name) == 60


@pytest.mark.asyncio
@pytest.mark.parametrize("project_id", [0, -1, True, "7"])
async def test_invalid_project_prevents_authorization_and_creation(project_id: Any) -> None:
    creator, authorizer = AsyncMock(), AsyncMock()
    service = ProjectService(AsyncMock(), authorizer=authorizer, version_creator=creator)
    with pytest.raises(ApplicationError):
        await service.create_project_version(project_id, CreateProjectVersionRequest(name="x"))
    authorizer.authorize.assert_not_awaited()
    creator.create_project_version.assert_not_awaited()


@pytest.mark.asyncio
async def test_denied_destination_prevents_creation() -> None:
    creator, authorizer = AsyncMock(), AsyncMock()
    authorizer.authorize.side_effect = ApplicationError("permission_denied", "denied", 403)
    service = ProjectService(AsyncMock(), authorizer=authorizer, version_creator=creator)
    with pytest.raises(ApplicationError):
        await service.create_project_version(7, CreateProjectVersionRequest(name="x"))
    authorizer.authorize.assert_awaited_once_with(
        WriteIntent("create_project_version", project_id=7)
    )
    creator.create_project_version.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permissions,expected",
    [(["manage_versions"], "conditional"), (["view_issues"], "denied"), (None, "unknown")],
)
async def test_creation_permission_is_manage_versions(permissions: Any, expected: str) -> None:
    service = CapabilityService(reader_for(permissions), 3)
    assert await service.project_operation("create_project_version", 7) == expected
    assert await service.project_operation("create_project_version", 8) == "unknown"
