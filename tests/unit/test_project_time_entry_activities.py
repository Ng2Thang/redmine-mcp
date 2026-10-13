"""Project activities distinguish hidden, empty and malformed native choices."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.projects.service import ProjectService
from redmine_mcp.integrations.redmine.projects import RedmineProjects


@pytest.mark.asyncio
@pytest.mark.parametrize("project_id", [0, -1, True, "7", 7.0, None])
async def test_invalid_project_never_calls_reader(project_id: Any) -> None:
    reader = AsyncMock()
    with pytest.raises(ApplicationError):
        await ProjectService(reader).list_project_time_entry_activities(project_id)
    reader.list_project_time_entry_activities.assert_not_awaited()


@pytest.mark.asyncio
async def test_exact_project_is_forwarded() -> None:
    reader = AsyncMock()
    result = await ProjectService(reader).list_project_time_entry_activities(7)
    assert result is reader.list_project_time_entry_activities.return_value
    reader.list_project_time_entry_activities.assert_awaited_once_with(7)


@pytest.mark.asyncio
@pytest.mark.parametrize("returned", [False, True])
async def test_hidden_choices_are_distinct_from_known_empty(returned: bool) -> None:
    client = AsyncMock()
    project: dict[str, Any] = {"id": 7}
    if returned:
        project["time_entry_activities"] = []
    client.get.return_value = {"project": project}
    result = await RedmineProjects(client).list_project_time_entry_activities(7)
    assert result.items == []
    assert [(o.path, o.state) for o in result.visibility.observations] == (
        [] if returned else [("/items", "not_returned")]
    )
    client.get.assert_awaited_once_with("projects/7.json", {"include": "time_entry_activities"})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rows",
    [
        None,
        {},
        "activities",
        [None],
        [{"id": True, "name": "Bad"}],
        [{"id": "9", "name": "Bad"}],
        [{"id": 0, "name": "Bad"}],
        [{"id": 9}],
        [{"id": 9, "name": ""}],
        [{"id": 9, "name": "Dev"}, {"id": 9, "name": "Duplicate"}],
    ],
)
async def test_malformed_or_duplicate_activities_are_upstream_errors(rows: Any) -> None:
    client = AsyncMock()
    client.get.return_value = {"project": {"id": 7, "time_entry_activities": rows}}
    with pytest.raises(ApplicationError) as error:
        await RedmineProjects(client).list_project_time_entry_activities(7)
    assert error.value.status == 502
