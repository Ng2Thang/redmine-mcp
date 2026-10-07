"""Cross-boundary regressions for SCHEMA-022, BODY-024 and FIELD-025."""

import base64
import copy
import json

import httpx
import pytest

from tests.helpers import mcp_session

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("assignment", [3, "me", None])
async def test_sdk_nullable_update_dispatches_once(writer_app, synthetic, assignment):
    synthetic.issues[42]["assigned_to"] = {"id": 8, "name": "Previous assignee"}
    async with mcp_session(writer_app) as session:
        result = await session.call_tool(
            "update_issue",
            {
                "issue_id": 42,
                "assigned_to_id": assignment,
                "description": None,
                "estimated_hours": None,
                "due_date": None,
            },
        )
    assert not result.isError, result
    assert json.loads(result.content[0].text)["field_verification"]["assigned_to_id"] == "matched"
    assert synthetic.writes == 1
    request = next(r for r in synthetic.requests if r.method == "PUT")
    payload = json.loads(request.content)["issue"]
    assert payload["assigned_to_id"] == ("" if assignment is None else assignment)
    assert payload["description"] is None and payload["estimated_hours"] is None


async def test_sdk_nullable_version_fields(writer_app, synthetic):
    async with mcp_session(writer_app) as session:
        result = await session.call_tool(
            "create_project_version",
            {
                "project_id": 7,
                "name": "nullable",
                "description": None,
                "due_date": None,
            },
        )
    assert not result.isError, result
    assert synthetic.writes == 1


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("operation", ["update", "copy"])
@pytest.mark.parametrize("stage", ["preflight", "readback"])
async def test_malformed_issue_zero_dispatch_or_preserved_receipt(
    writer_app,
    synthetic,
    boundary,
    operation,
    stage,
):
    original = synthetic.respond

    async def respond(request):
        response = await original(request)
        if request.method == "GET" and request.url.path.startswith("/issues/"):
            if (stage == "preflight" and synthetic.writes == 0) or (
                stage == "readback" and synthetic.writes
            ):
                raw = copy.deepcopy(response.json())
                if "issue" in raw:
                    raw["issue"]["tracker"]["id"] = True
                    return httpx.Response(200, json=raw)
        return response

    synthetic.respond = respond
    payload = (
        {"subject": "changed"}
        if operation == "update"
        else {
            "project_id": 7,
            "copy_from": 42,
            "subject": "copy",
        }
    )
    if boundary == "rest":
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(writer_app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-redmine-key"},
        ) as client:
            response = await client.request(
                "PUT" if operation == "update" else "POST",
                "/api/v1/issues/42" if operation == "update" else "/api/v1/issues",
                json=payload,
            )
        error = response.status_code != 200
        data = response.json()
    else:
        async with mcp_session(writer_app) as session:
            result = await session.call_tool(
                "update_issue" if operation == "update" else "create_issue",
                {**payload, **({"issue_id": 42} if operation == "update" else {})},
            )
        error = result.isError
        data = json.loads(result.content[0].text)
    if stage == "preflight":
        assert error and synthetic.writes == 0, data
    else:
        assert not error and synthetic.writes == 1, data
        assert data["outcome"] == "accepted" and data["upstream_accepted"] is True
        assert data["verification"] == "unavailable"


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("size", [2, 3, 4])
async def test_binary_cap_boundaries(application_factory, synthetic, boundary, size):
    async with application_factory(
        redmine_write_enabled=True,
        redmine_writer_auth_mode="personal_key",
        redmine_writer_operations="upload_attachment",
        redmine_max_binary_bytes=3,
    ) as app:
        payload = {
            "filename": "sample.txt",
            "content_base64": base64.b64encode(b"x" * size).decode(),
        }
        if boundary == "mcp":
            async with mcp_session(app) as session:
                result = await session.call_tool("upload_attachment", payload)
                accepted = not result.isError
        else:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": "offline-redmine-key"},
            ) as client:
                response = await client.post("/api/v1/uploads", json=payload)
                accepted = response.status_code == 200
        assert accepted == (size <= 3)
        assert synthetic.writes == (1 if size <= 3 else 0)


async def test_default_maximum_upload_passes_sdk_body_limit(writer_app, synthetic):
    size = writer_app.state.settings.redmine_max_binary_bytes
    async with mcp_session(writer_app) as session:
        result = await session.call_tool(
            "upload_attachment",
            {
                "filename": "maximum.bin",
                "content_base64": base64.b64encode(b"x" * size).decode(),
            },
        )
    assert not result.isError, result
    assert synthetic.writes == 1
    assert len(next(r for r in synthetic.requests if r.method == "POST").content) == size


@pytest.mark.parametrize("path", ["/mcp", "/api/v1/uploads"])
async def test_application_body_rejection_precedes_auth_and_keeps_correlation(
    application_factory, synthetic, path
):
    async with application_factory(redmine_max_request_body_bytes=4) as app:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                path, content=b"secret-oversize", headers={"X-Request-ID": "body-test"}
            )
    assert response.status_code == 413
    assert len(response.headers["X-Request-ID"]) == 32
    assert "secret-oversize" not in response.text
    assert synthetic.requests == []
