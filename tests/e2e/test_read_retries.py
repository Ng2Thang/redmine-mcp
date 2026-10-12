"""PREP-027 read-only compatibility against the owned pinned synthetic environment."""

import json
from typing import Any

import httpx
import pytest

from redmine_mcp.app import create_app
from redmine_mcp.auth import READ_OPERATIONS
from redmine_mcp.config import Settings
from tests.helpers import mcp_session
from tools.testing.e2e_config import URL


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.asyncio
async def test_retry_reader_preserves_native_issue_and_identity(
    live_manifest: Any, boundary: str
) -> None:
    key = live_manifest["users"]["a"]["key"]
    async with httpx.AsyncClient(
        base_url=URL + "/",
        headers={"X-Redmine-API-Key": key},
        trust_env=False,
    ) as native:
        response = await native.get("issues.json", params={"limit": 1, "status_id": "*"})
        assert response.status_code == 200
        issues = response.json()["issues"]
        assert issues, "Owned caller has no visible synthetic issue"
        issue_id = issues[0]["id"]
        expected = await native.get(
            f"issues/{issue_id}.json", params={"include": "journals,attachments"}
        )
        assert expected.status_code == 200
    app = create_app(Settings(_env_file=None, redmine_url=URL))
    async with app.router.lifespan_context(app):
        if boundary == "rest":
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": key},
            ) as client:
                result = await client.get(f"/api/v1/issues/{issue_id}")
                assert result.status_code == 200
                actual = result.json()
                disabled = await client.get("/api/v1/attachments/9/content")
                assert disabled.status_code == 403
        else:
            async with mcp_session(app, key) as session:
                catalog = await session.list_tools()
                assert {tool.name for tool in catalog.tools} == set(READ_OPERATIONS)
                result = await session.call_tool("get_issue", {"issue_id": issue_id})
                assert not result.isError
                actual = json.loads(result.content[0].text)
    expected_issue = expected.json()["issue"]
    assert actual["id"] == expected_issue["id"]
    assert actual["subject"] == expected_issue["subject"]
    assert actual["project"]["id"] == expected_issue["project"]["id"]
