"""Task 034 list/detail parity and caller-side estimate reporting."""

import json
from decimal import Decimal
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from tests.helpers import ISSUE, mcp_session

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("field", ["estimated_hours", "total_estimated_hours"])
@pytest.mark.parametrize("value", ["omitted", None, 0, 12, 1.25])
@pytest.mark.parametrize("detail", [False, True])
async def test_estimate_presence_and_list_detail_parity(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    field: str,
    value: Any,
    detail: bool,
) -> None:
    row = {**ISSUE}
    if value != "omitted":
        row[field] = value
    upstream["body"] = {"issue": row} if detail else {"issues": [row], "total_count": 1}
    response = await rest_client.get("/api/v1/issues/42" if detail else "/api/v1/issues")
    assert response.status_code == 200
    body = response.json()
    mapped = body if detail else body["items"][0]
    assert mapped[field] == (None if value == "omitted" else value)
    paths = {item["path"] for item in body["visibility"]["observations"]}
    path = f"/{field}" if detail else f"/items/0/{field}"
    assert (path in paths) == (value == "omitted")
    assert [request.url.path for request in upstream["requests"]] == [
        "/users/current.json",
        "/issues/42.json" if detail else "/issues.json",
    ]


@pytest.mark.parametrize("field", ["estimated_hours", "total_estimated_hours"])
@pytest.mark.parametrize("value", ["12", True, -1, {}, float("inf"), float("nan")])
@pytest.mark.parametrize("detail", [False, True])
async def test_malformed_estimates_are_sanitized(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    field: str,
    value: Any,
    detail: bool,
) -> None:
    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/current.json":
            return httpx.Response(200, json={"user": {"id": 3}})
        row = {**ISSUE, field: value, "secret": "hidden-estimate-secret"}
        body = {"issue": row} if detail else {"issues": [row], "total_count": 1}
        return httpx.Response(200, content=json.dumps(body))

    upstream["handler"] = respond
    response = await rest_client.get("/api/v1/issues/42" if detail else "/api/v1/issues")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "upstream_response"
    assert "hidden-estimate-secret" not in response.text


async def test_sdk_preserves_estimates_without_detail_fanout(
    app: FastAPI,
    upstream: dict[str, Any],
) -> None:
    upstream["body"] = {
        "issues": [{**ISSUE, "estimated_hours": 12, "total_estimated_hours": 24}],
        "total_count": 1,
    }
    async with mcp_session(app) as session:
        result = await session.call_tool("list_issues", {"project_id": 7, "status_id": "*"})
        assert not result.isError
        row = json.loads(result.content[0].text)["items"][0]
        assert (row["estimated_hours"], row["total_estimated_hours"]) == (12, 24)
    assert all(request.url.path != "/issues/42.json" for request in upstream["requests"])
    request = next(req for req in upstream["requests"] if req.url.path == "/issues.json")
    assert request.url.params["status_id"] == "*"


async def test_complete_pages_deduplicate_and_separate_unavailable_rollups(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    rows = [
        {**ISSUE, "id": i, "estimated_hours": 12, "total_estimated_hours": 24} for i in range(1, 9)
    ]
    rows += [
        rows[0],
        {**ISSUE, "id": 9, "estimated_hours": None},
        {**ISSUE, "id": 10},
        {**ISSUE, "id": 11, "estimated_hours": 0},
    ]

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/current.json":
            return httpx.Response(200, json={"user": {"id": 3}})
        limit, offset = int(request.url.params["limit"]), int(request.url.params["offset"])
        return httpx.Response(
            200,
            json={
                "issues": rows[offset : offset + limit],
                "total_count": len(rows),
                "limit": limit,
                "offset": offset,
            },
        )

    upstream["handler"] = respond
    unique: dict[int, Any] = {}
    for offset in range(0, len(rows), 4):
        response = await rest_client.get("/api/v1/issues", params={"limit": 4, "offset": offset})
        assert response.status_code == 200
        page = response.json()
        assert not page["pagination_policy"]["requires_narrowing"]
        unique.update({row["id"]: row for row in page["items"]})
    available = [row for row in unique.values() if row["estimated_hours"] is not None]
    assert sum((Decimal(str(row["estimated_hours"])) for row in available), Decimal(0)) == 96
    assert [row["id"] for row in unique.values() if row["estimated_hours"] is None] == [9, 10]
    # Rollups include descendants, so summing them alongside direct estimates is unsafe.
    assert unique[1]["total_estimated_hours"] == 24


async def test_decimal_preview_is_partial_when_scope_requires_narrowing(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    upstream["body"] = {
        "issues": [
            {**ISSUE, "id": 1, "estimated_hours": 0.1},
            {**ISSUE, "id": 2, "estimated_hours": 0.2},
        ],
        "total_count": 26,
        "limit": 2,
        "offset": 0,
    }
    response = await rest_client.get("/api/v1/issues", params={"limit": 2})
    assert response.status_code == 200
    body = response.json()
    partial = sum((Decimal(str(row["estimated_hours"])) for row in body["items"]), Decimal(0))
    assert partial == Decimal("0.3")
    assert body["total"] > len(body["items"])
    assert body["pagination_policy"]["requires_narrowing"]
    assert all(req.url.path != "/issues/42.json" for req in upstream["requests"])
