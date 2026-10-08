import json
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from tests.helpers import ISSUE, mcp_session


def issue_requests(upstream: dict[str, Any]) -> list[httpx.Request]:
    return [r for r in upstream["requests"] if r.url.path == "/issues.json"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,operator,values",
    [
        ("open", "o", [""]),
        ("closed", "c", [""]),
        ("*", "*", [""]),
        ("2", "=", ["2"]),
    ],
)
@pytest.mark.parametrize("assignee", ["me", "3"])
async def test_complete_structured_translation(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    status: str,
    operator: str,
    values: list[str],
    assignee: str,
) -> None:
    upstream["body"] = {"issues": [ISSUE], "total_count": 1}
    response = await rest_client.get(
        "/api/v1/issues",
        params={
            "tags_any": ["notification", "urgent"],
            "project_id": 7,
            "status_id": status,
            "assigned_to_id": assignee,
            "tracker_id": 2,
            "parent_id": 3,
            "category_id": 4,
            "fixed_version_id": 5,
            "updated_since": "2026-01-02T03:04:05+07:00",
            "include_subprojects": "false",
            "include": "attachments,relations",
            "sort": "updated_on:desc",
            "limit": 2,
        },
    )
    assert response.status_code == 200
    assert "tags" not in response.json()["items"][0]
    request = issue_requests(upstream)[0]
    params = request.url.params
    assert request.headers["X-Redmine-API-Key"] == "offline-redmine-key"
    assert params.get_list("fields[]") == [
        "issue_tags",
        "status_id",
        "assigned_to_id",
        "tracker_id",
        "parent_id",
        "category_id",
        "fixed_version_id",
        "updated_on",
        "subproject_id",
    ]
    expected = {
        "issue_tags": ("=", ["notification", "urgent"]),
        "status_id": (operator, values),
        "assigned_to_id": ("=", [assignee]),
        "tracker_id": ("=", ["2"]),
        "parent_id": ("=", ["3"]),
        "category_id": ("=", ["4"]),
        "fixed_version_id": ("=", ["5"]),
        "updated_on": (">=", ["2026-01-01T20:04:05Z"]),
        "subproject_id": ("!*", [""]),
    }
    for field, (op, vals) in expected.items():
        assert params[f"operators[{field}]"] == op
        assert params.get_list(f"values[{field}][]") == vals
        assert field not in params
    assert {
        k: params[k] for k in ("project_id", "sort", "limit", "offset", "include", "set_filter")
    } == {
        "project_id": "7",
        "sort": "updated_on:desc",
        "limit": "2",
        "offset": "0",
        "include": "attachments,relations",
        "set_filter": "1",
    }


@pytest.mark.asyncio
async def test_mocked_native_any_paging_and_unknown(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    # Emulates native filtering; does not establish the real plugin's ANY semantics.
    assignments = {41: {"A"}, 42: {"B"}, 43: {"A", "B"}, 44: {"C"}}

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/current.json":
            return httpx.Response(200, json={"user": {"id": 3}})
        assert request.url.path == "/issues.json" and request.method == "GET"
        params = request.url.params
        names = set(params.get_list("values[issue_tags][]"))
        ids = [n for n, tags in assignments.items() if names & tags]
        limit, offset = int(params["limit"]), int(params["offset"])
        return httpx.Response(
            200,
            json={
                "issues": [{**ISSUE, "id": n} for n in ids[offset : offset + limit]],
                "total_count": len(ids),
                "limit": limit,
                "offset": offset,
            },
        )

    upstream["handler"] = respond
    for offset, ids in [(0, [41, 42]), (2, [43])]:
        response = await rest_client.get(
            "/api/v1/issues",
            params={
                "tags_any": ["A", "B"],
                "limit": 2,
                "offset": offset,
            },
        )
        assert response.status_code == 200
        assert response.json()["total"] == 3
        assert [row["id"] for row in response.json()["items"]] == ids
    requests = issue_requests(upstream)
    assert [(r.url.params["limit"], r.url.params["offset"]) for r in requests] == [
        ("2", "0"),
        ("1", "0"),
        ("2", "2"),
    ]
    assert all(r.url.params.get_list("values[issue_tags][]") == ["A", "B"] for r in requests)
    unknown = await rest_client.get("/api/v1/issues", params={"tags_any": "missing"})
    assert unknown.status_code == 200
    assert unknown.json()["items"] == [] and unknown.json()["total"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "names",
    [
        [""],
        [" "],
        [" A"],
        ["A "],
        ["a\nb"],
        ["a\x00b"],
        ["a\u200bb"],
        ["a%"],
        ["a_b"],
        ["a\\b"],
        ["A", "A"],
        ["a" * 256],
        [str(n) for n in range(21)],
    ],
)
async def test_rest_invalid_before_issue_query(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    names: list[str],
) -> None:
    response = await rest_client.get("/api/v1/issues", params={"tags_any": names})
    assert response.status_code == 422
    assert not issue_requests(upstream)


@pytest.mark.asyncio
async def test_omitted_unchanged_and_delimiters_preserved(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    upstream["body"] = {"issues": [], "total_count": 0}
    response = await rest_client.get("/api/v1/issues", params={"project_id": 7})
    assert response.status_code == 200
    assert dict(issue_requests(upstream)[-1].url.params) == {
        "project_id": "7",
        "status_id": "open",
        "limit": "25",
        "offset": "0",
        "sort": "id:asc",
    }
    response = await rest_client.get(
        "/api/v1/issues", params={"tags_any": ["A,B", "A|B", "日本語"]}
    )
    assert response.status_code == 200
    params = issue_requests(upstream)[-1].url.params
    assert params.get_list("values[issue_tags][]") == ["A,B", "A|B", "日本語"]
    assert params.get_list("fields[]") == ["issue_tags", "status_id"]
    assert "subproject_id" not in params


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,body,expected,code",
    [
        (401, {}, 401, "invalid_credentials"),
        (403, {}, 403, "access_denied"),
        (404, {}, 404, "resource_not_found"),
        (422, {}, 502, "upstream_error"),
        (200, {"issues": [{}], "total_count": 1}, 502, "upstream_response"),
        (200, {"issues": [], "total_count": -1}, 502, "upstream_response"),
    ],
)
async def test_upstream_errors(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    status: int,
    body: dict[str, Any],
    expected: int,
    code: str,
) -> None:
    upstream.update(status=status, body=body)
    response = await rest_client.get("/api/v1/issues", params={"tags_any": "A"})
    assert response.status_code == expected
    assert response.json()["error"]["code"] == code


@pytest.mark.asyncio
async def test_mcp_array_schema_and_encoding(app: FastAPI, upstream: dict[str, Any]) -> None:
    upstream["body"] = {"issues": [ISSUE], "total_count": 1}
    async with mcp_session(app) as session:
        tools = await session.list_tools()
        tool = next(t for t in tools.tools if t.name == "list_issues")
        schema = tool.inputSchema["properties"]["tags_any"]
        assert schema["type"] == "array" and "anyOf" not in schema
        assert schema["minItems"] == 1 and schema["maxItems"] == 20
        assert schema["uniqueItems"] is True
        assert "tags_any" not in tool.inputSchema.get("required", [])
        result = await session.call_tool("list_issues", {"tags_any": ["A,B", "A|B"]})
        assert not result.isError
        data = json.loads(result.content[0].text)
        assert data["total"] == 1 and "tags" not in data["items"][0]
        assert issue_requests(upstream)[-1].url.params.get_list("values[issue_tags][]") == [
            "A,B",
            "A|B",
        ]
        for value in [None, [], "A", [True], [1], ["A", "A"], ["a%"], ["a_b"], [" A"]]:
            before = len(issue_requests(upstream))
            invalid = await session.call_tool("list_issues", {"tags_any": value})
            assert invalid.isError
            assert len(issue_requests(upstream)) == before
        omitted = await session.call_tool("list_issues", {})
        assert not omitted.isError
        assert "fields[]" not in issue_requests(upstream)[-1].url.params
