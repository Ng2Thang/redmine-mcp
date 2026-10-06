"""Task 035 general logs, bounded reads and real MCP SDK contracts."""

import json
from collections import defaultdict
from decimal import Decimal
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from tests.helpers import ISSUE, mcp_session

pytestmark = pytest.mark.asyncio

ENTRY = {
    "id": 1,
    "project": {"id": 7, "name": "Demo"},
    "user": {"id": 8, "name": "Credited"},
    "hours": 1.25,
    "spent_on": "2026-09-01",
    "activity": {"id": 2, "name": "Development"},
    "comments": "Project-only work",
}


def page(
    rows: list[dict[str, Any]], *, total: int | None = None, limit: int = 25, offset: int = 0
) -> dict[str, Any]:
    return {
        "time_entries": rows,
        "total_count": len(rows) if total is None else total,
        "limit": limit,
        "offset": offset,
    }


@pytest.mark.parametrize("issue", ["omitted", None, {"id": 42}])
async def test_project_only_and_nullable_fields(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    issue: Any,
) -> None:
    row = {**ENTRY}
    if issue != "omitted":
        row["issue"] = issue
    upstream["body"] = page([row])
    result = await rest_client.get("/api/v1/time-entries")
    assert result.status_code == 200
    body = result.json()
    assert body["items"][0] == {
        **{k: v for k, v in ENTRY.items()},
        "issue_id": 42 if isinstance(issue, dict) else None,
    }
    assert body["visibility"]["scope"] == "requesting_redmine_user"
    assert [req.url.path for req in upstream["requests"]] == [
        "/users/current.json",
        "/time_entries.json",
    ]
    upstream["body"] = page([{k: v for k, v in row.items() if k not in {"activity", "comments"}}])
    mapped = (await rest_client.get("/api/v1/time-entries")).json()["items"][0]
    assert mapped["activity"] is None and mapped["comments"] is None
    upstream["body"] = page([])
    assert (await rest_client.get("/api/v1/time-entries")).json()["items"] == []


@pytest.mark.parametrize(
    "changes",
    [
        {"id": True},
        {"id": 0},
        {"id": "1"},
        {"project": None},
        {"project": {}},
        {"project": {"id": "7", "name": "Demo"}},
        {"user": None},
        {"user": {}},
        {"user": {"id": 0, "name": "Credited"}},
        {"hours": None},
        {"hours": "1.25"},
        {"hours": True},
        {"hours": -1},
        {"hours": float("nan")},
        {"hours": float("inf")},
        {"spent_on": None},
        {"spent_on": "2026-02-30"},
        {"spent_on": "2026-09-01T00:00:00Z"},
        {"activity": {}},
        {"activity": {"id": True, "name": "Bad"}},
        {"comments": []},
        {"issue": {}},
        {"issue": {"id": "42"}},
        {"issue": {"id": 0}},
    ],
)
async def test_malformed_rows_are_sanitized(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    changes: dict[str, Any],
) -> None:
    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/current.json":
            return httpx.Response(200, json={"user": {"id": 3}})
        return httpx.Response(
            200,
            content=json.dumps(
                page(
                    [
                        {**ENTRY, **changes, "secret": "hidden-time-secret"},
                    ]
                )
            ),
        )

    upstream["handler"] = respond
    result = await rest_client.get("/api/v1/time-entries")
    assert result.status_code == 502
    assert result.json()["error"]["code"] == "upstream_response"
    assert "hidden-time-secret" not in result.text


@pytest.mark.parametrize(
    "params",
    [
        {"project_id": "0"},
        {"issue_id": "-1"},
        {"user_id": "0"},
        {"user_id": "all"},
        {"include_subprojects": "true"},
        {"include_subprojects": "invalid"},
        {"spent_from": "2026-9-1"},
        {"spent_to": "2026-02-30"},
        {"spent_from": "2026-09-01T00:00:00Z"},
        {"spent_from": "2026-10-01", "spent_to": "2026-09-30"},
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
async def test_invalid_rest_input_prevents_resource_access(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    params: dict[str, Any],
) -> None:
    result = await rest_client.get("/api/v1/time-entries", params=params)
    assert result.status_code == 422
    assert all(req.url.path == "/users/current.json" for req in upstream["requests"])


@pytest.mark.parametrize("descendants", [False, True])
@pytest.mark.parametrize("user_id", [8, "me"])
async def test_combined_native_filters_and_continuation_probe(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    descendants: bool,
    user_id: Any,
) -> None:
    upstream["body"] = page([{**ENTRY, "issue": {"id": 42}}], total=3, limit=1, offset=1)
    result = await rest_client.get(
        "/api/v1/time-entries",
        params={
            "project_id": 7,
            "include_subprojects": str(descendants).lower(),
            "user_id": user_id,
            "issue_id": 42,
            "spent_from": "2026-09-01",
            "spent_to": "2026-09-30",
            "limit": 1,
            "offset": 1,
        },
    )
    assert result.status_code == 200
    expected = {
        "project_id": "7",
        "subproject_id": "*" if descendants else "!*",
        "user_id": str(user_id),
        "issue_id": "42",
        "from": "2026-09-01",
        "to": "2026-09-30",
        "sort": "spent_on:asc",
        "limit": "1",
        "offset": "1",
    }
    resources = [req for req in upstream["requests"] if req.url.path != "/users/current.json"]
    assert [req.url.path for req in resources] == ["/time_entries.json"] * 2
    assert dict(resources[0].url.params) == {**expected, "offset": "0"}
    assert dict(resources[1].url.params) == expected


@pytest.mark.parametrize(
    "filters,expected",
    [
        ({}, {}),
        ({"spent_from": "2026-09-01"}, {"from": "2026-09-01"}),
        ({"spent_to": "2026-09-30"}, {"to": "2026-09-30"}),
        ({"project_id": 7}, {"project_id": "7", "subproject_id": "!*"}),
    ],
)
async def test_default_and_single_bound_mapping(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    filters: dict[str, Any],
    expected: dict[str, str],
) -> None:
    upstream["body"] = page([])
    assert (await rest_client.get("/api/v1/time-entries", params=filters)).status_code == 200
    assert dict(upstream["requests"][-1].url.params) == {
        "limit": "25",
        "offset": "0",
        "sort": "spent_on:asc",
        **expected,
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"total_count": None},
        {"total_count": True},
        {"total_count": "1"},
        {"limit": 24},
        {"offset": 1},
        {"time_entries": [None]},
    ],
)
async def test_invalid_page_metadata(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    changes: dict[str, Any],
) -> None:
    upstream["body"] = {**page([ENTRY]), **changes}
    assert (await rest_client.get("/api/v1/time-entries")).status_code == 502


@pytest.mark.parametrize("missing", ["total_count", "limit", "offset"])
async def test_required_page_metadata(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    missing: str,
) -> None:
    upstream["body"] = {k: v for k, v in page([]).items() if k != missing}
    assert (await rest_client.get("/api/v1/time-entries")).status_code == 502


async def test_broad_preview_stops_continuation_and_deep_offsets(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    upstream["body"] = page([ENTRY], total=251)
    first = await rest_client.get("/api/v1/time-entries")
    assert first.status_code == 200
    assert first.json()["pagination_policy"]["requires_narrowing"]
    upstream["body"] = page([ENTRY], total=251, offset=25)
    continuation = await rest_client.get("/api/v1/time-entries", params={"offset": 25})
    assert continuation.status_code == 422
    assert continuation.json()["error"]["code"] == "scope_required"
    assert "spent_on" in continuation.text
    assert upstream["requests"][-1].url.params["limit"] == "1"
    before = len(upstream["requests"])
    deep = await rest_client.get("/api/v1/time-entries", params={"offset": 250})
    assert deep.status_code == 422
    assert all(req.url.path == "/users/current.json" for req in upstream["requests"][before:])


async def test_sdk_discovery_union_invocation_and_old_preflight(
    app: FastAPI,
    upstream: dict[str, Any],
) -> None:
    upstream["body"] = page([ENTRY])
    async with mcp_session(app) as session:
        tools = (await session.list_tools()).tools
        tool = next(tool for tool in tools if tool.name == "list_time_entries")
        assert tool.annotations.readOnlyHint and tool.annotations.idempotentHint
        assert not tool.annotations.destructiveHint
        schema = tool.inputSchema["properties"]["user_id"]
        assert "type" not in schema
        assert any(branch.get("type") == "integer" for branch in schema["anyOf"])
        assert any(branch.get("const") == "me" for branch in schema["anyOf"])
        for user in [8, "me"]:
            result = await session.call_tool("list_time_entries", {"user_id": user})
            assert not result.isError
            assert json.loads(result.content[0].text)["items"][0]["issue_id"] is None
            assert upstream["requests"][-1].url.params["user_id"] == str(user)
        for user in [0, -1, True, "8", "all"]:
            before = len(upstream["requests"])
            result = await session.call_tool("list_time_entries", {"user_id": user})
            assert result.isError
            assert all(
                req.url.path == "/users/current.json" for req in upstream["requests"][before:]
            )
        upstream["responses"] = {"/issues/42.json": (200, {"issue": ISSUE})}
        upstream["body"] = page([{**ENTRY, "issue": {"id": 42}}])
        before = len(upstream["requests"])
        result = await session.call_tool("list_issue_time_entries", {"issue_id": 42})
        assert not result.isError
        assert [
            req.url.path
            for req in upstream["requests"][before:]
            if req.url.path != "/users/current.json"
        ] == [
            "/issues/42.json",
            "/time_entries.json",
        ]


async def test_complete_visible_pages_decimal_totals_and_groupings(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    rows = [
        {**ENTRY, "hours": 0.1},
        {**ENTRY, "id": 2, "hours": 0.2},
        {**ENTRY, "hours": 0.1},
        {
            **ENTRY,
            "id": 3,
            "hours": 0.3,
            "activity": None,
            "spent_on": "2026-09-30",
            "project": {"id": 9, "name": "Other"},
            "user": {"id": 3, "name": "Self"},
        },
    ]

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/current.json":
            return httpx.Response(200, json={"user": {"id": 3}})
        limit, offset = int(request.url.params["limit"]), int(request.url.params["offset"])
        return httpx.Response(
            200,
            json=page(rows[offset : offset + limit], total=len(rows), limit=limit, offset=offset),
        )

    upstream["handler"] = respond
    unique: dict[int, Any] = {}
    for offset in [0, 2]:
        response = await rest_client.get(
            "/api/v1/time-entries", params={"limit": 2, "offset": offset}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["visibility"]["scope"] == "requesting_redmine_user"
        assert not body["pagination_policy"]["requires_narrowing"]
        unique.update({row["id"]: row for row in body["items"]})
    assert sum((Decimal(str(row["hours"])) for row in unique.values()), Decimal(0)) == Decimal(
        "0.6"
    )
    for field, expected in [
        ("project", {7: Decimal("0.3"), 9: Decimal("0.3")}),
        ("user", {8: Decimal("0.3"), 3: Decimal("0.3")}),
        ("activity", {2: Decimal("0.3"), None: Decimal("0.3")}),
        ("spent_on", {"2026-09-01": Decimal("0.3"), "2026-09-30": Decimal("0.3")}),
    ]:
        grouped: defaultdict[Any, Decimal] = defaultdict(Decimal)
        for row in unique.values():
            ref = row[field]
            key = ref["id"] if isinstance(ref, dict) else ref
            grouped[key] += Decimal(str(row["hours"]))
        assert grouped == expected


async def test_stateful_own_visibility_dates_and_credited_user(
    application_factory: Any,
    synthetic: Any,
) -> None:
    # Issue scheduling differs from log dates and must not constrain time reporting.
    synthetic.issues[42].update(start_date="2026-10-01", due_date="2026-10-31")
    synthetic.own_time_entries_only = True
    async with application_factory() as app:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-reader-key"},
        ) as client:
            response = await client.get(
                "/api/v1/time-entries",
                params={
                    "spent_from": "2026-09-01",
                    "spent_to": "2026-09-30",
                    "user_id": "me",
                },
            )
            assert response.status_code == 200
            assert [row["id"] for row in response.json()["items"]] == [2]
            assert response.json()["items"][0]["issue_id"] is None
            response = await client.get("/api/v1/time-entries", params={"user_id": 3})
            assert response.status_code == 200 and response.json()["items"] == []


@pytest.mark.parametrize("transport", ["rest", "mcp"])
async def test_read_request_budget_returns_error_instead_of_complete_total(
    application_factory: Any,
    synthetic: Any,
    transport: str,
) -> None:
    # The REST read budget includes its identity check plus the continuation probe.
    async with application_factory(redmine_read_operation_max_requests=2) as app:
        before = len(synthetic.requests)
        if transport == "rest":
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": "offline-redmine-key"},
            ) as client:
                response = await client.get(
                    "/api/v1/time-entries", params={"limit": 1, "offset": 1}
                )
                assert response.status_code == 422
                assert response.json()["error"]["code"] == "scan_budget_exceeded"
        else:
            async with mcp_session(app) as session:
                result = await session.call_tool("list_time_entries", {"limit": 1, "offset": 1})
                assert result.isError
                assert "scan_budget_exceeded" in str(result.content)
        resources = [
            req for req in synthetic.requests[before:] if req.url.path == "/time_entries.json"
        ]
        assert len(resources) == 1
        assert resources[0].url.params["offset"] == "0"


async def test_openapi_additive_response_schema(rest_client: httpx.AsyncClient) -> None:
    schema = (await rest_client.get("/openapi.json")).json()
    route = schema["paths"]["/api/v1/time-entries"]["get"]
    assert route["operationId"] == "list_time_entries"
    models = schema["components"]["schemas"]
    for model in ["Issue", "IssueDetail"]:
        assert "estimated_hours" in models[model]["properties"]
        assert "total_estimated_hours" in models[model]["properties"]
    assert "issue_id" not in models["TimeEntry"]["required"]


async def test_scope_growth_after_probe_stops_complete_reporting(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/current.json":
            return httpx.Response(200, json={"user": {"id": 3}})
        limit, offset = int(request.url.params["limit"]), int(request.url.params["offset"])
        return httpx.Response(
            200, json=page([ENTRY], total=2 if offset == 0 else 251, limit=limit, offset=offset)
        )

    upstream["handler"] = respond
    response = await rest_client.get("/api/v1/time-entries", params={"offset": 25})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "scope_required"
    assert "items" not in response.json()
