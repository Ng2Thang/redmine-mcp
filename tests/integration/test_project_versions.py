"""Offline REST/MCP version creation with stateful and failure-injecting Redmine mocks."""

import copy
import json
from typing import Any

import httpx
import pytest

from tests.helpers import mcp_session

ROUTE = "/api/v1/projects/7/versions"
VERSION = {
    "id": 100,
    "project": {"id": 7, "name": "Demo"},
    "name": "sprint-01",
    "status": "open",
    "sharing": "none",
    "description": "original",
    "due_date": "2026-10-20",
}


async def invoke(app: Any, boundary: str, payload: dict[str, Any]) -> tuple[int, Any]:
    if boundary == "mcp":
        async with mcp_session(app) as session:
            result = await session.call_tool("create_project_version", {"project_id": 7, **payload})
        text = result.content[0].text
        if result.isError:
            return 422, {"error": {"message": text}}
        return 200, json.loads(text)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-redmine-key"},
    ) as client:
        response = await client.post(ROUTE, json=payload)
        return response.status_code, response.json()


def override_response(
    monkeypatch: Any, synthetic: Any, method: str, path: str, response: httpx.Response
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.method == method and request.url.path == path:
            synthetic.requests.append(request)
            if method != "GET":
                synthetic.writes += 1
            return response
        return await original(request)

    monkeypatch.setattr(synthetic, "respond", respond)


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "optional",
    [{}, {"description": None, "due_date": None}, {"description": "", "due_date": "2028-02-29"}],
)
async def test_exact_payload_and_readback(
    writer_app: Any, synthetic: Any, boundary: str, optional: dict[str, Any]
) -> None:
    status, result = await invoke(writer_app, boundary, {"name": " Sprint-01 ", **optional})
    assert status == 200
    assert result["outcome"] == "accepted" and result["verification"] == "matched"
    assert result["upstream_accepted"] is True and result["error"] is None
    writes = [r for r in synthetic.requests if r.method == "POST"]
    assert len(writes) == 1
    assert json.loads(writes[0].content) == {
        "version": {
            "name": " Sprint-01 ",
            "status": "open",
            "sharing": "none",
            **{k: v for k, v in optional.items() if v is not None},
        }
    }
    assert result["observed_version"] == synthetic.versions[result["resource_id"]]
    assert any(r.url.path == f"/versions/{result['resource_id']}.json" for r in synthetic.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_duplicate_returns_existing_data_and_error_without_update(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
) -> None:
    synthetic.versions[100] = copy.deepcopy(VERSION)
    status, result = await invoke(
        writer_app,
        boundary,
        {"name": "sprint-01", "description": "changed", "due_date": "2026-11-01"},
    )
    assert status == 200 and result["outcome"] == "existing"
    assert result["resource_id"] == 100 and result["upstream_accepted"] is False
    assert result["error"]["code"] == "version_already_exists"
    assert "Supplied fields were not applied" in result["error"]["message"]
    assert result["observed_version"] == VERSION
    assert synthetic.versions == {100: VERSION} and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {"versions": [], "total_count": 0},
        {"versions": [{**VERSION, "project": {"id": 8, "name": "Other"}}], "total_count": 1},
        {"versions": [{**VERSION, "name": "Sprint-01"}], "total_count": 1},
        {"versions": [VERSION, {**VERSION, "id": 101}], "total_count": 2},
        {"versions": [VERSION, VERSION], "total_count": 2},
        {"versions": [VERSION], "total_count": 2},
        {"versions": [VERSION], "total_count": True},
        {"versions": [VERSION, {}], "total_count": 2},
        {"versions": [VERSION], "total_count": "1"},
    ],
)
async def test_unreliable_duplicate_lookup_preserves_validation_error(
    writer_app: Any,
    synthetic: Any,
    monkeypatch: Any,
    body: Any,
) -> None:
    synthetic.write_failure = 422
    override_response(
        monkeypatch, synthetic, "GET", "/projects/7/versions.json", httpx.Response(200, json=body)
    )
    status, result = await invoke(writer_app, "rest", {"name": "sprint-01"})
    assert status == 422 and result["error"]["code"] == "invalid_parameters"
    assert "must-not-leak" not in json.dumps(result) and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [400, 401, 403, 404, 503])
async def test_other_upstream_errors_do_not_lookup_duplicates(
    writer_app: Any,
    synthetic: Any,
    failure: int,
) -> None:
    synthetic.write_failure = failure
    status, result = await invoke(writer_app, "rest", {"name": "sprint-01"})
    assert status == {400: 422, 503: 502}.get(failure, failure)
    assert "must-not-leak" not in json.dumps(result) and synthetic.writes == 1
    assert not any(
        r.url.path == "/projects/7/versions.json" and r.method == "GET" for r in synthetic.requests
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(201, content=b"not-json"),
        httpx.Response(201, json={}),
        httpx.Response(201, json={"version": {**VERSION, "id": True}}),
        httpx.Response(201, json={"version": {"id": 100}}),
        httpx.Response(201, json={"version": {**VERSION, "project": {"id": 8, "name": "Other"}}}),
        httpx.Response(200, json={"version": VERSION}),
        httpx.Response(204),
    ],
)
async def test_unusable_creation_response_is_uncertain(
    writer_app: Any,
    synthetic: Any,
    monkeypatch: Any,
    response: httpx.Response,
) -> None:
    override_response(monkeypatch, synthetic, "POST", "/projects/7/versions.json", response)
    status, result = await invoke(writer_app, "rest", {"name": "sprint-01"})
    assert status == 200 and result["outcome"] == "uncertain"
    assert result["upstream_accepted"] is (True if response.status_code == 201 else None)
    assert synthetic.writes == 1
    assert not any(
        r.method == "GET" and r.url.path.startswith("/versions/") for r in synthetic.requests
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_dispatched_timeout_never_retries_or_reconciles_by_name(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
) -> None:
    synthetic.write_failure = httpx.ReadTimeout("must-not-leak")
    status, result = await invoke(writer_app, boundary, {"name": "sprint-01"})
    assert status == 200 and result["outcome"] == "uncertain"
    assert result["upstream_accepted"] is None and result["resource_id"] is None
    assert synthetic.writes == 1 and "must-not-leak" not in json.dumps(result)
    assert not any(
        r.url.path == "/projects/7/versions.json" and r.method == "GET" for r in synthetic.requests
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body,expected",
    [
        ({**VERSION, "name": "changed"}, "mismatch"),
        ({**VERSION, "sharing": "descendants"}, "mismatch"),
        ({**VERSION, "description": "changed"}, "mismatch"),
        ({k: v for k, v in VERSION.items() if k != "description"}, "unavailable"),
        ({}, "unavailable"),
    ],
)
async def test_readback_does_not_erase_acceptance(
    writer_app: Any,
    synthetic: Any,
    monkeypatch: Any,
    body: Any,
    expected: str,
) -> None:
    override_response(
        monkeypatch,
        synthetic,
        "GET",
        "/versions/100.json",
        httpx.Response(200, json={"version": body}),
    )
    status, result = await invoke(
        writer_app,
        "rest",
        {"name": "sprint-01", "description": "original", "due_date": "2026-10-20"},
    )
    assert status == 200 and result["outcome"] == "accepted"
    assert result["upstream_accepted"] is True and result["verification"] == expected
    assert synthetic.versions[100] == VERSION and synthetic.writes == 1


@pytest.mark.asyncio
async def test_manage_versions_without_read_permission(
    writer_app: Any,
    synthetic: Any,
    monkeypatch: Any,
) -> None:
    synthetic.permissions = ["manage_versions"]
    override_response(monkeypatch, synthetic, "GET", "/versions/100.json", httpx.Response(403))
    override_response(
        monkeypatch, synthetic, "GET", "/projects/7/versions.json", httpx.Response(403)
    )
    status, result = await invoke(writer_app, "rest", {"name": "sprint-01"})
    assert status == 200 and result["outcome"] == "accepted"
    assert result["verification"] == "unavailable" and synthetic.writes == 1
    status, result = await invoke(writer_app, "rest", {"name": "sprint-01"})
    assert status == 422 and result["error"]["code"] == "invalid_parameters"
    assert synthetic.writes == 2 and len(synthetic.versions) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "payload",
    [
        {"name": " "},
        {"name": "x" * 61},
        {"name": "x", "due_date": "2026-02-29"},
        {"name": "x", "status": "closed"},
        {"name": "x", "sharing": "system"},
        {"name": "x", "description": "x" * 256},
    ],
)
async def test_invalid_input_never_mutates(
    writer_app: Any, synthetic: Any, boundary: str, payload: Any
) -> None:
    status, _ = await invoke(writer_app, boundary, payload)
    assert status == 422 and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("key", [None, "invalid-key"])
async def test_missing_or_invalid_credentials(writer_app: Any, synthetic: Any, key: Any) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={} if key is None else {"X-Redmine-API-Key": key},
    ) as client:
        response = await client.post(ROUTE, json={"name": "sprint-01"})
    assert response.status_code == 401 and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "settings,key",
    [
        ({"redmine_writer_operations": "create_issue"}, "offline-redmine-key"),
        ({"redmine_writer_user_ids": "8"}, "offline-redmine-key"),
        ({}, "offline-reader-key"),
    ],
)
async def test_deployment_and_user_gates(
    application_factory: Any, synthetic: Any, settings: Any, key: str
) -> None:
    config = {
        "redmine_write_enabled": True,
        "redmine_writer_auth_mode": "personal_key",
        "redmine_writer_operations": "create_project_version",
        **settings,
    }
    async with application_factory(**config) as app:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": key},
        ) as client:
            response = await client.post(ROUTE, json={"name": "x"})
        assert response.status_code == 403 and synthetic.writes == 0


@pytest.mark.asyncio
async def test_mcp_schema_annotations_and_project_capabilities(
    writer_app: Any, synthetic: Any
) -> None:
    synthetic.permissions = ["manage_versions"]
    async with mcp_session(writer_app) as session:
        tool = next(
            t for t in (await session.list_tools()).tools if t.name == "create_project_version"
        )
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.idempotentHint is False
        assert tool.annotations.openWorldHint is True
        assert {"project_id", "name"} <= set(tool.inputSchema["required"])
        assert not {"status", "sharing"} & tool.inputSchema["properties"].keys()
        result = await session.call_tool(
            "list_my_project_capabilities",
            {"project_id": 7, "operation_id": "create_project_version", "include_reasons": True},
        )
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["items"][0]["tools"][0]["state"] == "conditional"
    assert synthetic.writes == 0
