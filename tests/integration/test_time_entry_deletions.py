"""TOOL-043 exact deletion, permissions, receipts and REST/MCP contracts offline."""

import copy
import hashlib
import json
from typing import Any

import httpx
import pytest

from tests.helpers import mcp_session

UPSTREAM = "/time_entries/1.json"
KEY = "offline-redmine-key"


async def invoke(
    app: Any,
    boundary: str = "rest",
    *,
    key: str = KEY,
    issue_id: Any = 42,
    entry_id: Any = 1,
    extra: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    if boundary == "mcp":
        async with mcp_session(app, key) as session:
            result = await session.call_tool(
                "delete_time_entry",
                {"issue_id": issue_id, "time_entry_id": entry_id, **(extra or {})},
            )
        if result.isError:
            return 422, {"error": result.content[0].text}
        return 200, json.loads(result.content[0].text)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": key},
    ) as client:
        response = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{entry_id}")
    return response.status_code, response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_delete_exact_entry_preserves_control_and_duplicate_is_error(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
) -> None:
    control = copy.deepcopy(synthetic.time_entries[1])
    status, result = await invoke(writer_app, boundary)
    assert status == 200
    assert result == {
        "outcome": "accepted",
        "upstream_accepted": True,
        "resource_id": 1,
        "issue_id": 42,
        "verification": "not_found",
        "observed_present": False,
    }
    assert synthetic.time_entries == [control]
    writes = [r for r in synthetic.requests if r.method != "GET"]
    assert len(writes) == 1 and writes[0].method == "DELETE"
    assert writes[0].url.path == UPSTREAM and writes[0].content == b""
    assert not writes[0].url.params and writes[0].headers["X-Redmine-API-Key"] == KEY
    status, _ = await invoke(writer_app, boundary)
    assert status == (404 if boundary == "rest" else 422) and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("field", ["issue_id", "entry_id"])
@pytest.mark.parametrize("value", [0, -1, True, "bad"])
async def test_invalid_path_never_reads_entry_or_deletes(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    field: str,
    value: Any,
) -> None:
    status, _ = await invoke(writer_app, boundary, **{field: value})
    assert status == 422 and synthetic.writes == 0
    assert not any(r.url.path == UPSTREAM for r in synthetic.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("extra", [{"entries": [1, 2]}, {"confirm": True}, {"hours": 1}])
async def test_extra_mcp_arguments_never_dispatch(
    writer_app: Any,
    synthetic: Any,
    extra: dict[str, Any],
) -> None:
    status, _ = await invoke(writer_app, "mcp", extra=extra)
    assert status == 422 and synthetic.writes == 0
    assert not any(r.url.path == UPSTREAM for r in synthetic.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("id", True, 502),
        ("issue", {"id": 43}, 422),
        ("issue", None, 422),
        ("issue", {"id": "42"}, 502),
        ("project", {"id": 8, "name": "Other"}, 422),
        ("project", None, 502),
        ("user", None, 502),
        ("user", {"id": True, "name": "Bad"}, 502),
    ],
)
async def test_wrong_or_malformed_entry_prevents_delete(
    writer_app: Any,
    synthetic: Any,
    field: str,
    value: Any,
    expected: int,
) -> None:
    synthetic.time_entries[0][field] = value
    status, _ = await invoke(writer_app)
    assert status == expected and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("target", [UPSTREAM, "/issues/42.json"])
@pytest.mark.parametrize("observation", ["403", "404", "wrong_id", "malformed"])
async def test_inaccessible_or_invalid_preflight_prevents_delete(
    writer_app: Any,
    synthetic: Any,
    target: str,
    observation: str,
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.url.path != target:
            return response
        if observation in ("403", "404"):
            return httpx.Response(int(observation))
        data = response.json()
        resource = "time_entry" if target == UPSTREAM else "issue"
        if observation == "wrong_id":
            data[resource]["id"] = 999
        else:
            data[resource] = []
        return httpx.Response(200, json=data)

    synthetic.respond = respond
    status, _ = await invoke(writer_app)
    assert status == (int(observation) if observation in ("403", "404") else 502)
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "credited,permissions,expected",
    [
        (3, ["view_time_entries", "edit_own_time_entries"], 200),
        (8, ["view_time_entries", "edit_own_time_entries"], 403),
        (8, ["view_time_entries", "edit_time_entries"], 200),
        (3, ["view_time_entries", "log_time"], 403),
        (3, ["edit_time_entries"], 403),
    ],
)
async def test_credited_ownership_and_view_edit_boundaries(
    writer_app: Any,
    synthetic: Any,
    credited: int,
    permissions: list[str],
    expected: int,
) -> None:
    synthetic.time_entries[0]["user"]["id"] = credited
    synthetic.time_entries[0]["author"] = {"id": 3, "name": "Submitting caller"}
    synthetic.permissions = permissions
    before = copy.deepcopy(synthetic.time_entries)
    status, _ = await invoke(writer_app)
    assert status == expected and synthetic.writes == (1 if expected == 200 else 0)
    if expected != 200:
        assert synthetic.time_entries == before


@pytest.mark.asyncio
@pytest.mark.parametrize("native_edit", [False, True])
async def test_unknown_role_evidence_keeps_native_authority(
    writer_app: Any,
    synthetic: Any,
    native_edit: bool,
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/roles/"):
            synthetic.requests.append(request)
            return httpx.Response(403)
        return await original(request)

    synthetic.respond = respond
    synthetic.write_failure = None if native_edit else 403
    status, _ = await invoke(writer_app)
    assert status == (200 if native_edit else 403) and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("failure", [400, 401, 403, 404, 422, 429])
async def test_native_rejections_are_sanitized_single_attempt(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    failure: int,
) -> None:
    before = copy.deepcopy(synthetic.time_entries)
    synthetic.write_failure = failure
    status, result = await invoke(writer_app, boundary)
    assert status == (422 if boundary == "mcp" else {400: 422, 429: 502}.get(failure, failure))
    assert synthetic.writes == 1 and "must-not-leak" not in json.dumps(result)
    assert synthetic.time_entries == before


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("failure", [500, 503, 504, httpx.ReadTimeout("must-not-leak")])
async def test_ambiguous_uncommitted_dispatch_remains_uncertain_and_present(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    failure: Any,
) -> None:
    synthetic.write_failure = failure
    status, result = await invoke(writer_app, boundary)
    assert status == 200 and result["outcome"] == "uncertain"
    assert result["upstream_accepted"] is None and result["resource_id"] == 1
    assert result["verification"] == "still_present" and result["observed_present"] is True
    assert synthetic.writes == 1 and "must-not-leak" not in json.dumps(result)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["pool", "pre_dispatch"])
async def test_known_pre_dispatch_failure_preserves_state(
    writer_app: Any,
    synthetic: Any,
    failure: str,
) -> None:
    original = synthetic.respond
    before = copy.deepcopy(synthetic.time_entries)

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            synthetic.requests.append(request)
            if failure == "pool":
                raise httpx.PoolTimeout("must-not-leak")
            request.extensions["redmine_dispatched"] = False
            raise httpx.ConnectError("must-not-leak")
        return await original(request)

    synthetic.respond = respond
    status, result = await invoke(writer_app)
    assert status == (503 if failure == "pool" else 502)
    assert synthetic.time_entries == before and synthetic.writes == 0
    assert "must-not-leak" not in json.dumps(result)


@pytest.mark.asyncio
@pytest.mark.parametrize("observation", ["403", "timeout", "malformed", "wrong_id", "present"])
async def test_readback_never_negates_accepted_delete(
    writer_app: Any,
    synthetic: Any,
    observation: str,
) -> None:
    original = synthetic.respond
    entry = copy.deepcopy(synthetic.time_entries[0])

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.method == "GET" and request.url.path == UPSTREAM and synthetic.writes:
            if observation == "403":
                return httpx.Response(403)
            if observation == "timeout":
                raise httpx.ReadTimeout("must-not-leak")
            if observation == "malformed":
                return httpx.Response(200, json={"time_entry": []})
            if observation == "wrong_id":
                entry["id"] = 2
            return httpx.Response(200, json={"time_entry": entry})
        return response

    synthetic.respond = respond
    status, result = await invoke(writer_app)
    assert status == 200 and result["outcome"] == "accepted" and result["upstream_accepted"] is True
    assert result["verification"] == (
        "still_present" if observation == "present" else "unavailable"
    )
    assert result["observed_present"] is (True if observation == "present" else None)
    assert synthetic.writes == 1 and all(row["id"] != 1 for row in synthetic.time_entries)


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [200, 201, 500])
async def test_committed_delete_and_get404_never_promote_uncertainty(
    writer_app: Any,
    synthetic: Any,
    status_code: int,
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        return httpx.Response(status_code, json={}) if request.method == "DELETE" else response

    synthetic.respond = respond
    status, result = await invoke(writer_app)
    assert (
        status == 200 and result["outcome"] == "uncertain" and result["upstream_accepted"] is None
    )
    assert result["verification"] == "not_found" and result["observed_present"] is False
    assert synthetic.writes == 1 and all(row["id"] != 1 for row in synthetic.time_entries)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "config,expected",
    [
        ({}, 403),
        (
            {
                "redmine_write_enabled": True,
                "redmine_writer_auth_mode": "personal_key",
                "redmine_writer_operations": "update_time_entry",
            },
            403,
        ),
        (
            {
                "redmine_write_enabled": True,
                "redmine_writer_auth_mode": "personal_key",
                "redmine_writer_operations": "delete_time_entry",
                "redmine_writer_user_ids": "8",
            },
            403,
        ),
        (
            {
                "redmine_write_enabled": True,
                "redmine_writer_auth_mode": "pinned_key",
                "redmine_writer_operations": "delete_time_entry",
                "redmine_writer_user_ids": "3",
                "redmine_writer_key_sha256": hashlib.sha256(KEY.encode()).hexdigest(),
            },
            200,
        ),
        (
            {
                "redmine_write_enabled": True,
                "redmine_writer_auth_mode": "personal_key",
                "redmine_writer_operations": "allowed_all",
            },
            200,
        ),
    ],
)
async def test_reader_operation_user_pinned_and_allowed_all_gates(
    application_factory: Any,
    synthetic: Any,
    config: dict[str, Any],
    expected: int,
) -> None:
    async with application_factory(**config) as app:
        status, _ = await invoke(app)
    assert status == expected and synthetic.writes == (1 if expected == 200 else 0)


@pytest.mark.asyncio
async def test_schema_annotations_discovery_and_capability_report(
    writer_app: Any,
    synthetic: Any,
) -> None:
    async with mcp_session(writer_app) as session:
        tool = next(t for t in (await session.list_tools()).tools if t.name == "delete_time_entry")
        assert tool.annotations.readOnlyHint is False and tool.annotations.destructiveHint is True
        assert tool.annotations.idempotentHint is False and tool.annotations.openWorldHint is True
        assert set(tool.inputSchema["required"]) == {"issue_id", "time_entry_id"}
        assert set(tool.inputSchema["properties"]) == {"issue_id", "time_entry_id"}
        assert tool.inputSchema["additionalProperties"] is False
        assert tool.inputSchema["properties"]["time_entry_id"]["type"] == "integer"
    async with mcp_session(writer_app, "offline-reader-key") as session:
        assert "delete_time_entry" not in {t.name for t in (await session.list_tools()).tools}
    operation = writer_app.openapi()["paths"][
        "/api/v1/issues/{issue_id}/time-entries/{time_entry_id}"
    ]["delete"]
    assert "requestBody" not in operation
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": KEY},
    ) as client:
        report = await client.get(
            "/api/v1/users/current/project-capabilities", params={"project_id": 7}
        )
    assert report.status_code == 200
    tools = report.json()["items"][0]["tools"]
    assert (
        next(t for t in tools if t["operation_id"] == "delete_time_entry")["state"] == "conditional"
    )
    assert synthetic.writes == 0


@pytest.mark.asyncio
async def test_uncertain_write_and_visibility404_cannot_prove_physical_absence(
    writer_app: Any,
    synthetic: Any,
) -> None:
    original = synthetic.respond
    synthetic.write_failure = 500

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.method == "GET" and request.url.path == UPSTREAM and synthetic.writes:
            return httpx.Response(404)
        return response

    synthetic.respond = respond
    status, result = await invoke(writer_app)
    assert status == 200 and result["outcome"] == "uncertain"
    assert result["upstream_accepted"] is None and result["verification"] == "not_found"
    assert result["observed_present"] is False and synthetic.writes == 1
    assert any(row["id"] == 1 for row in synthetic.time_entries)


@pytest.mark.asyncio
async def test_readback_budget_exhaustion_keeps_accepted_receipt(
    writer_app: Any,
    synthetic: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from redmine_mcp.common import ApplicationError
    from redmine_mcp.integrations.redmine.client import RedmineClient

    original = RedmineClient.get

    async def budget_failure(self: Any, path: str, *args: Any, **kwargs: Any) -> Any:
        if synthetic.writes and path == "time_entries/1.json":
            raise ApplicationError("scan_budget_exceeded", "Owned budget exhausted", 422)
        return await original(self, path, *args, **kwargs)

    monkeypatch.setattr(RedmineClient, "get", budget_failure)
    status, result = await invoke(writer_app)
    assert status == 200 and result["outcome"] == "accepted"
    assert result["upstream_accepted"] is True and result["verification"] == "unavailable"
    assert result["observed_present"] is None and synthetic.writes == 1
