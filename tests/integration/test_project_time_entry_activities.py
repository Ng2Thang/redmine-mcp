"""Activity discovery preserves visibility and strict native collection contracts."""

import json
from typing import Any

import httpx
import pytest

from tests.helpers import mcp_session

ROUTE = "/api/v1/projects/7/time-entry-activities"


async def invoke(app: Any, boundary: str, project_id: int = 7) -> tuple[int, dict[str, Any]]:
    if boundary == "mcp":
        async with mcp_session(app) as session:
            result = await session.call_tool(
                "list_project_time_entry_activities", {"project_id": project_id}
            )
        return (422, {}) if result.isError else (200, json.loads(result.content[0].text))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-redmine-key"},
    ) as client:
        response = await client.get(f"/api/v1/projects/{project_id}/time-entry-activities")
    return response.status_code, response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("shape", ["populated", "empty", "hidden"])
async def test_native_activity_choices_and_visibility(
    application_factory: Any, synthetic: Any, boundary: str, shape: str
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.url.path == "/projects/7.json":
            data = response.json()
            if shape == "empty":
                data["project"]["time_entry_activities"] = []
            elif shape == "hidden":
                data["project"].pop("time_entry_activities", None)
            return httpx.Response(200, json=data)
        return response

    synthetic.respond = respond
    async with application_factory() as app:
        status, data = await invoke(app, boundary)
    assert status == 200 and synthetic.writes == 0
    assert data["items"] == (
        [{"id": 9, "name": "Development"}, {"id": 10, "name": "Review"}]
        if shape == "populated"
        else []
    )
    assert data["visibility"]["observations"] == (
        [{"path": "/items", "state": "not_returned"}] if shape == "hidden" else []
    )
    project_calls = [r for r in synthetic.requests if r.url.path == "/projects/7.json"]
    assert len(project_calls) == 1
    assert dict(project_calls[0].url.params) == {"include": "time_entry_activities"}


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("project_id", [0, -1])
async def test_invalid_activity_project_is_rejected_locally(
    application_factory: Any, synthetic: Any, boundary: str, project_id: int
) -> None:
    async with application_factory() as app:
        status, _ = await invoke(app, boundary, project_id)
    assert status == 422 and synthetic.writes == 0
    assert not any(r.url.path.startswith("/projects/") for r in synthetic.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("failure", [403, 404, 500])
async def test_native_activity_errors_are_not_empty_success(
    application_factory: Any, synthetic: Any, boundary: str, failure: int
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.url.path == "/projects/7.json":
            return httpx.Response(failure, json={"secret": "must-not-leak"})
        return response

    synthetic.respond = respond
    async with application_factory(redmine_read_retry_max_attempts=1) as app:
        status, data = await invoke(app, boundary)
    assert status == (422 if boundary == "mcp" else {500: 502}.get(failure, failure))
    assert "must-not-leak" not in json.dumps(data) and synthetic.writes == 0
