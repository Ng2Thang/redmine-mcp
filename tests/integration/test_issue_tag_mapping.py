"""Issue detail preserves tag names and distinguishes unavailable from empty tags."""

import json
from typing import Any

import httpx
import pytest

from tests.helpers import mcp_session


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("shape", ["absent", "null", "empty", "populated"])
async def test_issue_detail_tag_mapping(
    writer_app: Any, synthetic: Any, boundary: str, shape: str
) -> None:
    if shape != "absent":
        synthetic.issues[42]["tags"] = {
            "null": None,
            "empty": [],
            "populated": ["日本語", "A,B", "beta"],
        }[shape]
    if boundary == "mcp":
        async with mcp_session(writer_app) as session:
            result = await session.call_tool("get_issue", {"issue_id": 42, "include": ""})
        assert not result.isError
        data = json.loads(result.content[0].text)
    else:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=writer_app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-redmine-key"},
        ) as client:
            response = await client.get("/api/v1/issues/42", params={"include": ""})
        assert response.status_code == 200
        data = response.json()
    assert (
        data["tags"]
        == {
            "absent": None,
            "null": None,
            "empty": [],
            "populated": ["A,B", "beta", "日本語"],
        }[shape]
    )
    tag_observations = [o for o in data["visibility"]["observations"] if o["path"] == "/tags"]
    assert tag_observations == (
        [{"path": "/tags", "state": "not_returned"}] if shape == "absent" else []
    )
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("tags", [[""], [" "], ["dup", "dup"], [42], "tag", {}])
async def test_malformed_assigned_tags_are_not_silently_discarded(
    writer_app: Any, synthetic: Any, tags: Any
) -> None:
    synthetic.issues[42]["tags"] = tags
    async with mcp_session(writer_app) as session:
        result = await session.call_tool("get_issue", {"issue_id": 42, "include": ""})
    assert result.isError and synthetic.writes == 0
