"""TOOL-042 state, permissions, faults and REST/MCP contracts without network access."""

import copy
import json
from typing import Any

import httpx
import pytest

from tests.helpers import mcp_session

ROUTE = "/api/v1/issues/42/time-entries/1"
UPSTREAM = "/time_entries/1.json"
KEY = "offline-redmine-key"


async def invoke(
    app: Any,
    boundary: str,
    payload: dict[str, Any],
    *,
    key: str = KEY,
    issue_id: int = 42,
    entry_id: int = 1,
) -> tuple[int, Any]:
    if boundary == "mcp":
        async with mcp_session(app, key) as session:
            result = await session.call_tool(
                "update_time_entry", {"issue_id": issue_id, "time_entry_id": entry_id, **payload}
            )
        if result.isError:
            return 422, {"error": result.content[0].text}
        return 200, json.loads(result.content[0].text)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": key},
    ) as client:
        response = await client.put(
            f"/api/v1/issues/{issue_id}/time-entries/{entry_id}", json=payload
        )
    return response.status_code, response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "payload",
    [
        {"hours": 1.234},
        {"spent_on": "2028-02-29"},
        {"activity_id": 10},
        {"comments": ""},
        {"hours": 0.125, "spent_on": "2026-10-07", "activity_id": 9, "comments": " exact "},
    ],
)
async def test_partial_update_preserves_identity_omissions_and_control(
    writer_app: Any, synthetic: Any, boundary: str, payload: dict[str, Any]
) -> None:
    before = copy.deepcopy(synthetic.time_entries)
    status, result = await invoke(writer_app, boundary, payload)
    assert status == 200 and result["outcome"] == "accepted"
    assert result["upstream_accepted"] is True and result["verification"] == "matched"
    assert result["resource_id"] == 1 and result["issue_id"] == 42
    assert set(result["field_verification"]) == set(payload) | {"issue_id", "project_id", "user_id"}
    assert set(result["field_verification"].values()) == {"matched"}
    writes = [r for r in synthetic.requests if r.method != "GET"]
    assert len(writes) == 1 and writes[0].url.path == UPSTREAM and writes[0].method == "PUT"
    assert json.loads(writes[0].content) == {"time_entry": payload}
    assert writes[0].headers["X-Redmine-API-Key"] == KEY
    assert not writes[0].url.params
    assert len(synthetic.time_entries) == 2 and synthetic.time_entries[1] == before[1]
    changed = {"activity" if field == "activity_id" else field for field in payload}
    for field in before[0].keys() - changed:
        assert synthetic.time_entries[0][field] == before[0][field]
    if "hours" in payload:
        assert (
            result["observed_time_entry"]["hours"] == {1.234: 1.23, 0.125: 0.13}[payload["hours"]]
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"hours": None},
        {"hours": 0},
        {"hours": "2"},
        {"hours": True},
        {"spent_on": "2026-02-29"},
        {"spent_on": None},
        {"activity_id": None},
        {"activity_id": True},
        {"comments": None},
        {"comments": "x" * 1025},
        {"hours": 1, "user_id": 8},
        {"hours": 1, "issue_id_new": 43},
    ],
)
async def test_invalid_input_never_reads_target_or_writes(
    writer_app: Any, synthetic: Any, boundary: str, payload: dict[str, Any]
) -> None:
    status, _ = await invoke(writer_app, boundary, payload)
    assert status == 422 and synthetic.writes == 0
    assert not any(r.url.path == UPSTREAM for r in synthetic.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("id", 2, 404),
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
async def test_wrong_or_malformed_target_prevents_put(
    writer_app: Any, synthetic: Any, field: str, value: Any, expected: int
) -> None:
    synthetic.time_entries[0][field] = value
    status, _ = await invoke(writer_app, "rest", {"hours": 1})
    assert status == expected and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [("id", 43), ("project", {"id": "7"})])
async def test_malformed_issue_prevents_put(
    writer_app: Any, synthetic: Any, field: str, value: Any
) -> None:
    synthetic.issues[42][field] = value
    status, _ = await invoke(writer_app, "rest", {"hours": 1})
    assert status == 502 and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("target", [UPSTREAM, "/issues/42.json"])
@pytest.mark.parametrize("failure", [403, 404])
async def test_inaccessible_preflight_never_dispatches(
    writer_app: Any, synthetic: Any, target: str, failure: int
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        return httpx.Response(failure) if request.url.path == target else response

    synthetic.respond = respond
    status, _ = await invoke(writer_app, "rest", {"hours": 1})
    assert status == failure and synthetic.writes == 0


@pytest.mark.asyncio
async def test_wrong_response_identity_never_dispatches(writer_app: Any, synthetic: Any) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.url.path == UPSTREAM:
            data = response.json()
            data["time_entry"]["id"] = 999
            return httpx.Response(200, json=data)
        return response

    synthetic.respond = respond
    status, _ = await invoke(writer_app, "rest", {"hours": 1})
    assert status == 502 and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("native_edit", [False, True])
async def test_incomplete_role_evidence_leaves_final_authority_upstream(
    writer_app: Any, synthetic: Any, native_edit: bool
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/roles/"):
            synthetic.requests.append(request)
            return httpx.Response(403)
        return await original(request)

    synthetic.respond = respond
    synthetic.write_failure = None if native_edit else 403
    status, _ = await invoke(writer_app, "rest", {"hours": 1})
    assert status == (200 if native_edit else 403) and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id,permissions,expected",
    [
        (3, ["view_time_entries", "edit_own_time_entries"], 200),
        (8, ["view_time_entries", "edit_own_time_entries"], 403),
        (8, ["view_time_entries", "edit_time_entries"], 200),
        (3, ["view_time_entries", "log_time"], 403),
        (3, ["edit_time_entries"], 403),
    ],
)
async def test_ownership_is_credited_user_and_view_and_edit_are_required(
    writer_app: Any, synthetic: Any, user_id: int, permissions: list[str], expected: int
) -> None:
    synthetic.time_entries[0]["user"]["id"] = user_id
    synthetic.time_entries[0]["author"] = {"id": 3, "name": "Submitting caller"}
    synthetic.permissions = permissions
    status, _ = await invoke(writer_app, "rest", {"comments": "changed"})
    assert status == expected and synthetic.writes == (1 if expected == 200 else 0)


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("failure", [400, 401, 403, 404, 422, 429])
async def test_native_rejections_are_sanitized_and_single_attempt(
    writer_app: Any, synthetic: Any, boundary: str, failure: int
) -> None:
    synthetic.write_failure = failure
    status, result = await invoke(writer_app, boundary, {"hours": 1})
    assert status == (422 if boundary == "mcp" else {400: 422, 429: 502}.get(failure, failure))
    assert synthetic.writes == 1 and "must-not-leak" not in json.dumps(result)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [500, 503, 504, httpx.ReadTimeout("must-not-leak")])
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_dispatched_failures_preserve_uncertainty(
    writer_app: Any, synthetic: Any, boundary: str, failure: Any
) -> None:
    synthetic.write_failure = failure
    status, result = await invoke(writer_app, boundary, {"hours": 1})
    assert status == 200 and result["outcome"] == "uncertain"
    assert result["upstream_accepted"] is None and result["resource_id"] == 1
    assert result["verification"] == "mismatch" and synthetic.writes == 1
    assert "must-not-leak" not in json.dumps(result)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [httpx.PoolTimeout("must-not-leak"), "pre_dispatch"])
async def test_known_pre_dispatch_failure_is_error(
    writer_app: Any, synthetic: Any, failure: Any
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "PUT":
            synthetic.requests.append(request)
            if failure == "pre_dispatch":
                request.extensions["redmine_dispatched"] = False
                raise httpx.ConnectError("must-not-leak")
            raise failure
        return await original(request)

    synthetic.respond = respond
    status, result = await invoke(writer_app, "rest", {"hours": 1})
    assert status == (502 if failure == "pre_dispatch" else 503)
    assert "must-not-leak" not in json.dumps(result)
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "observation",
    [
        "403",
        "404",
        "timeout",
        "malformed",
        "wrong_id",
        "missing_comments",
        "missing_activity",
        "mismatch",
        "moved",
        "recredited",
    ],
)
async def test_readback_is_independent_and_cannot_negate_acceptance(
    writer_app: Any, synthetic: Any, observation: str
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.method == "GET" and request.url.path == UPSTREAM and synthetic.writes:
            if observation in ("403", "404"):
                return httpx.Response(int(observation))
            if observation == "timeout":
                raise httpx.ReadTimeout("must-not-leak")
            if observation == "malformed":
                return httpx.Response(200, json={"time_entry": []})
            entry = response.json()["time_entry"]
            if observation == "wrong_id":
                entry["id"] = 2
            elif observation == "missing_comments":
                entry.pop("comments", None)
            elif observation == "missing_activity":
                entry.pop("activity", None)
            elif observation == "mismatch":
                entry["hours"] = 9
            elif observation == "moved":
                entry["issue"] = {"id": 43}
            elif observation == "recredited":
                entry["user"]["id"] = 8
            return httpx.Response(200, json={"time_entry": entry})
        return response

    synthetic.respond = respond
    status, result = await invoke(
        writer_app, "rest", {"hours": 1, "activity_id": 10, "comments": ""}
    )
    assert status == 200 and result["outcome"] == "accepted" and result["upstream_accepted"] is True
    expected = "mismatch" if observation in ("mismatch", "moved", "recredited") else "unavailable"
    assert result["verification"] == expected and synthetic.writes == 1
    assert synthetic.time_entries[0]["hours"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [200, 201, 500])
async def test_matched_committed_state_does_not_promote_unexpected_receipt(
    writer_app: Any, synthetic: Any, status_code: int
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        return httpx.Response(status_code, json={}) if request.method == "PUT" else response

    synthetic.respond = respond
    status, result = await invoke(writer_app, "rest", {"comments": "committed"})
    assert status == 200 and result["verification"] == "matched"
    assert result["outcome"] == "uncertain" and result["upstream_accepted"] is None
    assert synthetic.time_entries[0]["comments"] == "committed" and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "config,expected",
    [
        ({}, 403),
        (
            {
                "redmine_write_enabled": True,
                "redmine_writer_operations": "create_issue",
            },
            403,
        ),
        (
            {
                "redmine_write_enabled": True,
                "redmine_writer_operations": "update_time_entry",
            },
            200,
        ),
    ],
)
async def test_reader_and_operation_gates(
    application_factory: Any, synthetic: Any, config: dict[str, Any], expected: int
) -> None:
    async with application_factory(**config) as app:
        status, _ = await invoke(app, "rest", {"hours": 1})
    assert status == expected and synthetic.writes == (1 if expected == 200 else 0)


@pytest.mark.asyncio
async def test_schema_annotations_discovery_and_capability_report(
    writer_app: Any, synthetic: Any
) -> None:
    async with mcp_session(writer_app) as session:
        tool = next(
            tool for tool in (await session.list_tools()).tools if tool.name == "update_time_entry"
        )
        assert tool.annotations.readOnlyHint is False and tool.annotations.destructiveHint is True
        assert tool.annotations.idempotentHint is False and tool.annotations.openWorldHint is True
        assert set(tool.inputSchema["required"]) == {"issue_id", "time_entry_id"}
        assert set(tool.inputSchema["properties"]) == {
            "issue_id",
            "time_entry_id",
            "hours",
            "spent_on",
            "activity_id",
            "comments",
        }
        assert tool.inputSchema["properties"]["time_entry_id"]["type"] == "integer"
    async with mcp_session(writer_app, "offline-reader-key") as session:
        assert "update_time_entry" not in {tool.name for tool in (await session.list_tools()).tools}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": KEY},
    ) as client:
        report = await client.get(
            "/api/v1/users/current/project-capabilities", params={"project_id": 7}
        )
    assert report.status_code == 200, report.text
    tools = report.json()["items"][0]["tools"]
    assert (
        next(t for t in tools if t["operation_id"] == "update_time_entry")["state"] == "conditional"
    )
    assert synthetic.writes == 0
