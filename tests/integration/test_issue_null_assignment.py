"""Native null translation for REST and MCP, including an assigned copy source."""

import json

import httpx
import pytest

from tests.helpers import mcp_session

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("operation", ["update_issue", "create_issue"])
async def test_explicit_null_is_native_empty_id_and_omission_stays_omitted(
    writer_app,
    synthetic,
    boundary,
    operation,
):
    synthetic.issues[42]["assigned_to"] = {"id": 8, "name": "Previous assignee"}
    for supplied in (False, True):
        payload = {"subject": "changed", **({"assigned_to_id": None} if supplied else {})}
        payload.update(
            {"issue_id": 42} if operation == "update_issue" else {"project_id": 7, "copy_from": 42}
        )
        if boundary == "mcp":
            async with mcp_session(writer_app) as session:
                result = await session.call_tool(operation, payload)
                assert not result.isError
        else:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(writer_app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": "offline-redmine-key"},
            ) as client:
                body = {k: v for k, v in payload.items() if k != "issue_id"}
                response = await client.request(
                    "PUT" if operation == "update_issue" else "POST",
                    "/api/v1/issues/42" if operation == "update_issue" else "/api/v1/issues",
                    json=body,
                )
                assert response.status_code == 200
        request = [r for r in synthetic.requests if r.method != "GET"][-1]
        native = json.loads(request.content)["issue"]
        assert (
            (native.get("assigned_to_id") == "") if supplied else ("assigned_to_id" not in native)
        )
    assert synthetic.writes == 2
