"""Own-time creation contracts at REST/MCP boundaries using stateful native mocks."""

import copy
import json
from typing import Any

import httpx
import pytest

from tests.helpers import mcp_session

BASE = {"hours": 1.5, "spent_on": "2026-10-01"}
ROUTE = "/api/v1/issues/42/time-entries"
UPSTREAM = "/time_entries.json"


async def invoke(
    app: Any, boundary: str, payload: dict[str, Any], *, key: str = "offline-redmine-key"
) -> tuple[int, dict[str, Any]]:
    if boundary == "mcp":
        async with mcp_session(app, key) as session:
            result = await session.call_tool("create_time_entry", {"issue_id": 42, **payload})
        if result.isError:
            return 422, {"error": result.content[0].text}
        return 200, json.loads(result.content[0].text)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": key},
    ) as client:
        response = await client.post(ROUTE, json=payload)
    return response.status_code, response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "payload,expected_hours",
    [
        (BASE, 1.5),
        ({**BASE, "hours": 0.125}, 0.13),
        ({**BASE, "hours": 1.234}, 1.23),
        ({**BASE, "comments": ""}, 1.5),
        ({**BASE, "activity_id": 10, "comments": " exact "}, 1.5),
    ],
)
async def test_create_payload_caller_credit_and_independent_readback(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    payload: dict[str, Any],
    expected_hours: float,
) -> None:
    before = copy.deepcopy(synthetic.time_entries)
    status, result = await invoke(writer_app, boundary, payload)
    assert status == 200 and result["outcome"] == "accepted"
    assert result["upstream_accepted"] is True and result["verification"] == "matched"
    assert result["resource_id"] == 3
    assert result["observed_time_entry"]["hours"] == expected_hours
    assert result["observed_time_entry"]["user"]["id"] == 3
    assert result["observed_time_entry"]["issue_id"] == 42
    assert set(result["field_verification"]) == set(payload) | {
        "project_id",
        "issue_id",
        "user_id",
    }
    assert set(result["field_verification"].values()) == {"matched"}
    writes = [r for r in synthetic.requests if r.method != "GET"]
    assert len(writes) == 1 and writes[0].method == "POST" and writes[0].url.path == UPSTREAM
    assert dict(writes[0].url.params) == {"project_id": "7"}
    assert json.loads(writes[0].content) == {
        "time_entry": {**payload, "project_id": 7, "issue_id": 42}
    }
    assert writes[0].headers["X-Redmine-API-Key"] == "offline-redmine-key"
    assert synthetic.time_entries[:2] == before
    after = synthetic.requests[synthetic.requests.index(writes[0]) + 1 :]
    # The MCP SDK may refresh discovery after the call to validate its output schema.
    # Count time-entry reads independently of those authentication/capability GETs.
    time_reads = [
        r for r in after if r.method == "GET" and r.url.path.startswith("/time_entries")
    ]
    assert [r.url.path for r in time_reads] == ["/time_entries/3.json"]
    assert not time_reads[0].url.params
    assert time_reads[0].headers["X-Redmine-API-Key"] == "offline-redmine-key"


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_identical_independent_calls_create_distinct_entries(
    writer_app: Any, synthetic: Any, boundary: str
) -> None:
    results = [await invoke(writer_app, boundary, BASE) for _ in range(2)]
    assert [status for status, _ in results] == [200, 200]
    assert [data["resource_id"] for _, data in results] == [3, 4]
    assert synthetic.writes == 2 and len(synthetic.time_entries) == 4


@pytest.mark.asyncio
async def test_distinct_personal_keys_never_share_credited_caller(
    writer_app: Any, synthetic: Any
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.url.path == "/roles/5.json":
            data = response.json()
            data["role"]["permissions"] = ["log_time", "view_time_entries"]
            return httpx.Response(200, json=data)
        return response

    synthetic.respond = respond
    for key, caller_id in (("offline-redmine-key", 3), ("offline-reader-key", 8)):
        status, data = await invoke(writer_app, "mcp", BASE, key=key)
        assert status == 200 and data["verification"] == "matched"
        assert data["observed_time_entry"]["user"]["id"] == caller_id
    assert [row["user"]["id"] for row in synthetic.time_entries[2:]] == [3, 8]
    assert synthetic.writes == 2


@pytest.mark.asyncio
async def test_creation_schema_and_annotations_express_the_public_contract(writer_app: Any) -> None:
    async with mcp_session(writer_app) as session:
        tool = next(t for t in (await session.list_tools()).tools if t.name == "create_time_entry")
    assert {"issue_id", "hours", "spent_on"} <= set(tool.inputSchema["required"])
    assert not {"user_id", "author_id", "project_id", "custom_fields"} & set(
        tool.inputSchema["properties"]
    )
    assert tool.inputSchema.get("additionalProperties") is False
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.idempotentHint is False
    assert tool.annotations.openWorldHint is True


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"hours": 1},
        {"spent_on": "2026-10-01"},
        *[{**BASE, "hours": value} for value in (None, 0, -1, True, "2")],
        *[{**BASE, "spent_on": value} for value in (None, "2026-02-29", "2026-1-2")],
        *[{**BASE, "activity_id": value} for value in (None, True, 0, "9")],
        *[{**BASE, "comments": value} for value in (None, 42, "x" * 1025)],
    ],
)
async def test_invalid_creation_never_reads_issue_or_dispatches_post(
    writer_app: Any, synthetic: Any, boundary: str, payload: dict[str, Any]
) -> None:
    status, _ = await invoke(writer_app, boundary, payload)
    assert status == 422 and synthetic.writes == 0
    assert not any(r.url.path == "/issues/42.json" for r in synthetic.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("field", ["user_id", "author_id", "project_id", "custom_fields"])
async def test_rejects_fields_that_move_or_recredit_time(
    writer_app: Any, synthetic: Any, boundary: str, field: str
) -> None:
    status, _ = await invoke(writer_app, boundary, {**BASE, field: 8})
    assert status == 422 and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("permissions,expected", [(["log_time"], 200), ([], 403)])
async def test_create_permission_is_independent_of_time_read_or_edit(
    writer_app: Any, synthetic: Any, permissions: list[str], expected: int
) -> None:
    synthetic.permissions = permissions
    if permissions:
        synthetic.readback_failure = True
    status, result = await invoke(writer_app, "rest", BASE)
    assert status == expected and synthetic.writes == (1 if expected == 200 else 0)
    if expected == 200:
        assert result["outcome"] == "accepted" and result["upstream_accepted"] is True
        assert result["verification"] == "unavailable"


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [403, 404])
async def test_inaccessible_issue_never_creates_time(
    writer_app: Any, synthetic: Any, failure: int
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        return httpx.Response(failure) if request.url.path == "/issues/42.json" else response

    synthetic.respond = respond
    status, _ = await invoke(writer_app, "rest", BASE)
    assert status == failure and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,value", [("id", 43), ("id", True), ("project", None), ("project", {"id": "7"})]
)
async def test_malformed_issue_cannot_supply_creation_project(
    writer_app: Any, synthetic: Any, field: str, value: Any
) -> None:
    synthetic.issues[42][field] = value
    status, _ = await invoke(writer_app, "rest", BASE)
    assert status == 502 and synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("failure", [400, 401, 403, 404, 422, 429])
async def test_native_rejections_never_retry_or_expose_upstream_body(
    writer_app: Any, synthetic: Any, boundary: str, failure: int
) -> None:
    synthetic.write_failure = failure
    status, data = await invoke(writer_app, boundary, BASE)
    assert status == (422 if boundary == "mcp" else {400: 422, 429: 502}.get(failure, failure))
    assert synthetic.writes == 1 and len(synthetic.time_entries) == 2
    assert "must-not-leak" not in json.dumps(data)


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("failure", [500, 503, 504, httpx.ReadTimeout("must-not-leak")])
async def test_unidentified_dispatch_is_uncertain_without_name_or_list_reconciliation(
    writer_app: Any, synthetic: Any, boundary: str, failure: Any
) -> None:
    synthetic.write_failure = failure
    status, data = await invoke(writer_app, boundary, BASE)
    assert status == 200 and data["outcome"] == "uncertain"
    assert data["upstream_accepted"] is None and data["resource_id"] is None
    assert data["verification"] == "unavailable" and synthetic.writes == 1
    assert not any(
        r.method == "GET" and r.url.path.startswith("/time_entries") for r in synthetic.requests
    )
    assert "must-not-leak" not in json.dumps(data)


@pytest.mark.asyncio
@pytest.mark.parametrize("fault", ["timeout", "500"])
async def test_committed_lost_receipt_does_not_create_a_duplicate(
    writer_app: Any, synthetic: Any, fault: str
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.method == "POST" and request.url.path == UPSTREAM:
            if fault == "timeout":
                raise httpx.ReadTimeout("must-not-leak")
            return httpx.Response(500)
        return response

    synthetic.respond = respond
    status, data = await invoke(writer_app, "rest", BASE)
    assert status == 200 and data["outcome"] == "uncertain"
    assert data["resource_id"] is None and synthetic.writes == 1
    assert len(synthetic.time_entries) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("fault,expected", [("pool", 503), ("before_dispatch", 502)])
async def test_known_pre_dispatch_fault_does_not_claim_acceptance(
    writer_app: Any, synthetic: Any, fault: str, expected: int
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == UPSTREAM:
            synthetic.requests.append(request)
            if fault == "pool":
                raise httpx.PoolTimeout("must-not-leak")
            request.extensions["redmine_dispatched"] = False
            raise httpx.ConnectError("must-not-leak")
        return await original(request)

    synthetic.respond = respond
    status, data = await invoke(writer_app, "rest", BASE)
    assert status == expected and len(synthetic.time_entries) == 2
    assert synthetic.writes == 0 and "must-not-leak" not in json.dumps(data)


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [None, [], {}, {"time_entry": {}}, {"time_entry": {"id": True}}])
async def test_unusable_201_does_not_invent_resource_identity(
    writer_app: Any, synthetic: Any, body: Any
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.method == "POST" and request.url.path == UPSTREAM:
            return httpx.Response(201, json=body) if body is not None else httpx.Response(201)
        return response

    synthetic.respond = respond
    status, data = await invoke(writer_app, "rest", BASE)
    assert status == 200 and data["outcome"] == "uncertain"
    assert data["upstream_accepted"] is True and data["resource_id"] is None
    assert data["verification"] == "unavailable" and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["issue", "project", "user"])
async def test_wrong_201_reference_stays_uncertain_despite_matching_independent_get(
    writer_app: Any, synthetic: Any, field: str
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.method == "POST" and request.url.path == UPSTREAM:
            body = response.json()
            body["time_entry"][field] = {"id": 999, "name": "Other"}
            return httpx.Response(201, json=body)
        return response

    synthetic.respond = respond
    status, data = await invoke(writer_app, "rest", BASE)
    assert status == 200 and data["outcome"] == "uncertain"
    assert data["upstream_accepted"] is True and data["verification"] == "matched"
    assert data["resource_id"] == 3 and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "observation,expected",
    [
        ("403", "unavailable"),
        ("404", "unavailable"),
        ("malformed", "unavailable"),
        ("wrong_id", "unavailable"),
        ("missing_comments", "unavailable"),
        ("mismatch", "mismatch"),
        ("moved", "mismatch"),
        ("recredited", "mismatch"),
    ],
)
async def test_readback_never_erases_an_accepted_creation(
    writer_app: Any, synthetic: Any, observation: str, expected: str
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.method == "GET" and request.url.path == "/time_entries/3.json":
            if observation in ("403", "404"):
                return httpx.Response(int(observation))
            data = response.json()
            entry = data["time_entry"]
            if observation == "malformed":
                data["time_entry"] = []
            elif observation == "wrong_id":
                entry["id"] = 4
            elif observation == "missing_comments":
                entry.pop("comments")
            elif observation == "mismatch":
                entry["hours"] = 9
            else:
                entry["issue" if observation == "moved" else "user"] = {"id": 43, "name": "Other"}
            return httpx.Response(200, json=data)
        return response

    synthetic.respond = respond
    status, data = await invoke(writer_app, "rest", {**BASE, "comments": "exact"})
    assert status == 200 and data["outcome"] == "accepted"
    assert data["upstream_accepted"] is True and data["resource_id"] == 3
    assert data["verification"] == expected and synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("hours,rational", [(0.125, "2/15"), (1.234, "37/30")])
async def test_redmine_six_rational_readback_matches_native_rounding(
    writer_app: Any, synthetic: Any, hours: float, rational: str
) -> None:
    original = synthetic.respond

    async def respond(request: httpx.Request) -> httpx.Response:
        response = await original(request)
        if request.url.path == "/time_entries/3.json":
            data = response.json()
            data["time_entry"]["hours"] = rational
            return httpx.Response(200, json=data)
        return response

    synthetic.respond = respond
    status, data = await invoke(writer_app, "rest", {**BASE, "hours": hours})
    assert status == 200 and data["verification"] == "matched"
    assert data["field_verification"]["hours"] == "matched"
