import json
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi import status as http_status

from tests.helpers import ISSUE, PROJECT, mcp_session


@pytest.mark.asyncio
async def test_rest_success_and_upstream_mapping(
    rest_client: httpx.AsyncClient, upstream: dict[str, Any]
) -> None:
    upstream["body"] = {"projects": [PROJECT], "total_count": 1}
    response = await rest_client.get("/api/v1/projects", params={"limit": 1, "offset": 2})
    assert response.status_code == http_status.HTTP_200_OK
    assert response.json()["items"][0]["identifier"] == "demo"
    assert response.json()["limit"] == 1
    assert upstream["requests"][-1].url.path == "/projects.json"
    assert upstream["requests"][-1].headers["X-Redmine-API-Key"] == "offline-redmine-key"
    assert dict(upstream["requests"][-1].url.params) == {"limit": "1", "offset": "2"}
    upstream["body"] = {"issues": [ISSUE], "total_count": 1}
    response = await rest_client.get("/api/v1/issues")
    assert response.status_code == http_status.HTTP_200_OK
    assert response.json()["items"][0]["id"] == 42
    assert dict(upstream["requests"][-1].url.params) == {
        "limit": "25",
        "offset": "0",
        "status_id": "open",
        "sort": "id:asc",
    }
    upstream["body"] = {"issue": ISSUE}
    response = await rest_client.get("/api/v1/issues/42")
    assert response.status_code == http_status.HTTP_200_OK
    assert response.json()["id"] == 42
    assert upstream["requests"][-1].url.path == "/issues/42.json"
    assert upstream["requests"][-1].url.params["include"] == "journals,attachments"


@pytest.mark.asyncio
async def test_rest_auth_and_validation_before_upstream(
    app: FastAPI, rest_client: httpx.AsyncClient, upstream: dict[str, Any]
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as anonymous:
        assert (
            await anonymous.get("/api/v1/projects")
        ).status_code == http_status.HTTP_401_UNAUTHORIZED
    assert (
        await rest_client.get("/api/v1/projects", headers={"X-Redmine-API-Key": ""})
    ).status_code == http_status.HTTP_401_UNAUTHORIZED
    assert (
        await rest_client.get("/api/v1/projects", headers={"X-Redmine-API-Key": "incorrect-token"})
    ).status_code == http_status.HTTP_401_UNAUTHORIZED
    assert (
        await rest_client.get("/api/v1/issues", params={"limit": 0})
    ).status_code == http_status.HTTP_422_UNPROCESSABLE_CONTENT
    assert (
        await rest_client.get("/api/v1/issues/0")
    ).status_code == http_status.HTTP_422_UNPROCESSABLE_CONTENT
    assert all(request.url.path == "/users/current.json" for request in upstream["requests"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "body", "expected_status", "code"),
    [
        (http_status.HTTP_403_FORBIDDEN, {}, http_status.HTTP_403_FORBIDDEN, "access_denied"),
        (http_status.HTTP_404_NOT_FOUND, {}, http_status.HTTP_404_NOT_FOUND, "resource_not_found"),
        (
            http_status.HTTP_200_OK,
            {"issue": {}},
            http_status.HTTP_502_BAD_GATEWAY,
            "upstream_response",
        ),
        (
            http_status.HTTP_200_OK,
            {"invalid": []},
            http_status.HTTP_502_BAD_GATEWAY,
            "upstream_response",
        ),
    ],
)
async def test_rest_upstream_errors(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    status: int,
    body: dict[str, Any],
    expected_status: int,
    code: str,
) -> None:
    upstream.update(status=status, body=body)
    response = await rest_client.get("/api/v1/issues/42")
    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == code


@pytest.mark.asyncio
async def test_rest_timeout(rest_client: httpx.AsyncClient, upstream: dict[str, Any]) -> None:
    upstream["exception"] = httpx.ReadTimeout("offline timeout")
    response = await rest_client.get("/api/v1/issues/42")
    assert response.status_code == http_status.HTTP_504_GATEWAY_TIMEOUT
    assert response.json()["error"]["code"] == "upstream_timeout"


@pytest.mark.asyncio
async def test_mcp_discovery_invocation_and_error(app: FastAPI, upstream: dict[str, Any]) -> None:
    upstream["body"] = {"projects": [PROJECT], "total_count": 1}
    async with mcp_session(app) as session:
        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} >= {"list_projects", "list_issues", "get_issue"}
        result = await session.call_tool("list_projects", {"limit": 1, "offset": 0})
        assert not result.isError
        assert json.loads(result.content[0].text)["items"][0]["id"] == 7
        invalid = await session.call_tool("list_issues", {"limit": 0})
        assert invalid.isError
        assert "Input validation error" in str(invalid.content)
        upstream["status"] = http_status.HTTP_403_FORBIDDEN
        error = await session.call_tool("get_issue", {"issue_id": 42})
        assert error.isError
        assert "access_denied" in str(error.content)


@pytest.mark.asyncio
@pytest.mark.parametrize("token", [None, "incorrect-token"])
async def test_mcp_rejects_bad_api_key(app: FastAPI, token: str | None) -> None:
    with pytest.raises(ExceptionGroup) as error:
        async with mcp_session(app, token):
            pass
    assert "401 Unauthorized" in repr(error.value)
