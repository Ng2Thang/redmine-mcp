import json
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi import status as http_status

from tests.helpers import ISSUE, mcp_session


@pytest.mark.asyncio
async def test_defaults_pagination_and_combined_filters(
    rest_client: httpx.AsyncClient, upstream: dict[str, Any]
) -> None:
    upstream["body"] = {"issues": [ISSUE], "total_count": 10}
    default = await rest_client.get("/api/v1/issues", params={"limit": 1, "offset": 2})
    assert default.status_code == http_status.HTTP_200_OK
    assert default.json()["items"][0]["id"] == 42
    assert (default.json()["total"], default.json()["limit"], default.json()["offset"]) == (
        10,
        1,
        2,
    )
    assert dict(upstream["requests"][-1].url.params) == {
        "limit": "1",
        "offset": "2",
        "status_id": "open",
        "sort": "id:asc",
    }

    filtered = await rest_client.get(
        "/api/v1/issues",
        params={
            "project_id": 7,
            "status_id": "*",
            "assigned_to_id": "me",
            "tracker_id": 2,
            "parent_id": 3,
            "updated_since": "2026-01-02T03:04:05+07:00",
            "sort": "updated_on:desc",
        },
    )
    assert filtered.status_code == http_status.HTTP_200_OK
    request = upstream["requests"][-1]
    assert request.url.path == "/issues.json"
    assert dict(request.url.params) == {
        "limit": "25",
        "offset": "0",
        "status_id": "*",
        "sort": "updated_on:desc",
        "project_id": "7",
        "assigned_to_id": "me",
        "tracker_id": "2",
        "parent_id": "3",
        "updated_on": ">=2026-01-01T20:04:05Z",
    }
    assert "updated_on=%3E%3D2026-01-01T20%3A04%3A05Z" in str(request.url)


@pytest.mark.asyncio
@pytest.mark.parametrize("sort", ["id:asc", "id:desc", "updated_on:asc", "updated_on:desc"])
async def test_supported_sorts(
    rest_client: httpx.AsyncClient, upstream: dict[str, Any], sort: str
) -> None:
    upstream["body"] = {"issues": [], "total_count": 0}
    response = await rest_client.get("/api/v1/issues", params={"sort": sort})
    assert response.status_code == http_status.HTTP_200_OK
    assert response.json()["items"] == []
    assert upstream["requests"][-1].url.params["sort"] == sort


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("tracker_id", "0"),
        ("tracker_id", ""),
        ("parent_id", "-1"),
        ("parent_id", ""),
        ("updated_since", ""),
        ("updated_since", "2026-01-02T03:04:05"),
        ("updated_since", "2026-01-02"),
        ("updated_since", "1234567890"),
        ("updated_since", "2026-99-02T03:04:05Z"),
        ("sort", ""),
        ("sort", "subject:asc"),
    ],
)
async def test_invalid_inputs_rejected_before_upstream(
    rest_client: httpx.AsyncClient, upstream: dict[str, Any], name: str, value: str
) -> None:
    response = await rest_client.get("/api/v1/issues", params={name: value})
    assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_CONTENT
    assert all(request.url.path == "/users/current.json" for request in upstream["requests"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "body", "expected_status", "code"),
    [
        (http_status.HTTP_403_FORBIDDEN, {}, http_status.HTTP_403_FORBIDDEN, "access_denied"),
        (http_status.HTTP_404_NOT_FOUND, {}, http_status.HTTP_404_NOT_FOUND, "resource_not_found"),
        (
            http_status.HTTP_200_OK,
            {"issues": [{}], "total_count": 1},
            http_status.HTTP_502_BAD_GATEWAY,
            "upstream_response",
        ),
        (
            http_status.HTTP_200_OK,
            {"unexpected": []},
            http_status.HTTP_502_BAD_GATEWAY,
            "upstream_response",
        ),
    ],
)
async def test_list_errors(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    status: int,
    body: dict[str, Any],
    expected_status: int,
    code: str,
) -> None:
    upstream.update(status=status, body=body)
    response = await rest_client.get("/api/v1/issues")
    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == code


@pytest.mark.asyncio
async def test_list_timeout(rest_client: httpx.AsyncClient, upstream: dict[str, Any]) -> None:
    upstream["exception"] = httpx.ReadTimeout("offline timeout")
    response = await rest_client.get("/api/v1/issues")
    assert response.status_code == http_status.HTTP_504_GATEWAY_TIMEOUT
    assert response.json()["error"]["code"] == "upstream_timeout"


@pytest.mark.asyncio
async def test_mcp_contract_and_error(app: FastAPI, upstream: dict[str, Any]) -> None:
    upstream["body"] = {"issues": [ISSUE], "total_count": 1}
    async with mcp_session(app) as session:
        tools = await session.list_tools()
        listed = next(tool for tool in tools.tools if tool.name == "list_issues")
        assert {"tracker_id", "parent_id", "updated_since", "sort"} <= set(
            listed.inputSchema["properties"]
        )
        assert listed.inputSchema["properties"]["sort"]["default"] == "id:asc"
        result = await session.call_tool(
            "list_issues", {"tracker_id": 2, "sort": "updated_on:desc"}
        )
        assert not result.isError
        assert json.loads(result.content[0].text)["items"][0]["id"] == 42
        assert upstream["requests"][-1].url.params["tracker_id"] == "2"
        assert upstream["requests"][-1].url.params["sort"] == "updated_on:desc"
        upstream["status"] = http_status.HTTP_403_FORBIDDEN
        error = await session.call_tool("list_issues", {})
        assert error.isError
        assert "access_denied" in str(error.content)
