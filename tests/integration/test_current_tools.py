"""Current operation contracts through REST and MCP with stateful upstream mocks."""

import json
from typing import Any

import httpx
import pytest

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS
from tests.helpers import mcp_session

WRITES = [
    (
        "create_project_version",
        "POST",
        "/api/v1/projects/7/versions",
        {"name": "sprint-01"},
        "/projects/7/versions.json",
    ),
    (
        "upload_attachment",
        "POST",
        "/api/v1/uploads",
        {"filename": "sample.txt", "content_base64": "eA=="},
        "/uploads.json",
    ),
    (
        "add_project_file",
        "POST",
        "/api/v1/projects/7/files",
        {"token": "9.abc", "filename": "sample.txt"},
        "/projects/7/files.json",
    ),
    (
        "update_attachment",
        "PATCH",
        "/api/v1/attachments/9",
        {"container_type": "project", "container_id": 7, "description": "changed"},
        "/attachments/9.json",
    ),
    (
        "delete_attachment",
        "DELETE",
        "/api/v1/attachments/9?container_type=project&container_id=7",
        None,
        "/attachments/9.json",
    ),
    (
        "create_issue",
        "POST",
        "/api/v1/issues",
        {"project_id": 7, "subject": "created"},
        "/issues.json",
    ),
    ("update_issue", "PUT", "/api/v1/issues/42", {"subject": "changed"}, "/issues/42.json"),
    (
        "update_issue_note",
        "PUT",
        "/api/v1/issues/42/notes/1",
        {"notes": "changed"},
        "/journals/1.json",
    ),
    (
        "create_issue_relation",
        "POST",
        "/api/v1/issues/42/relations",
        {"issue_to_id": 43},
        "/issues/42/relations.json",
    ),
    ("delete_issue_relation", "DELETE", "/api/v1/relations/1", None, "/relations/1.json"),
    (
        "add_issue_watcher",
        "POST",
        "/api/v1/issues/42/watchers",
        {"user_id": 3},
        "/issues/42/watchers.json",
    ),
    (
        "remove_issue_watcher",
        "DELETE",
        "/api/v1/issues/42/watchers/3",
        None,
        "/issues/42/watchers/3.json",
    ),
]
READ_ARGUMENTS = {
    "list_time_entries": {"project_id": 7, "user_id": "me"},
    "list_project_members": {"project_ids": [7]},
    "get_project": {"project_id": 7},
    "list_project_versions": {"project_id": 7},
    "list_project_issue_categories": {"project_id": 7},
    "list_project_files": {"project_id": 7},
    "get_issue": {"issue_id": 42},
    "get_attachment": {"attachment_id": 9},
    "list_issue_time_entries": {"issue_id": 42},
}


def prepare(synthetic: Any, operation: Any) -> Any:
    if operation == "delete_issue_relation":
        for issue_id in (42, 43):
            synthetic.issues[issue_id]["relations"] = [synthetic.relation]
    if operation == "remove_issue_watcher":
        synthetic.issues[42]["watchers"] = [{"id": 3, "name": "Writer"}]


def arguments(operation: Any, payload: Any) -> Any:
    result = {} if payload is None else payload.copy()
    if operation in ("add_project_file", "create_project_version"):
        result["project_id"] = 7
    if operation in ("update_attachment", "delete_attachment"):
        result.update(attachment_id=9)
        if operation == "delete_attachment":
            result.update(container_type="project", container_id=7)
    if operation in (
        "update_issue",
        "update_issue_note",
        "create_issue_relation",
        "add_issue_watcher",
        "remove_issue_watcher",
    ):
        result["issue_id"] = 42
    if operation == "update_issue_note":
        result["journal_id"] = 1
    if operation == "delete_issue_relation":
        result["relation_id"] = 1
    if operation == "remove_issue_watcher":
        result["user_id"] = 3
    return result


@pytest.mark.asyncio
@pytest.mark.parametrize("case", WRITES, ids=[row[0] for row in WRITES])
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_all_writer_success_and_single_dispatch(
    writer_app: Any, synthetic: Any, case: Any, boundary: Any
) -> None:
    operation, method, path, payload, upstream_path = case
    prepare(synthetic, operation)
    if boundary == "rest":
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=writer_app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-redmine-key"},
        ) as client:
            response = await client.request(method, path, json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
    else:
        async with mcp_session(writer_app) as session:
            result = await session.call_tool(operation, arguments(operation, payload))
            assert not result.isError, (operation, result)
            data = json.loads(result.content[0].text)
    assert data["outcome"] == "accepted"
    assert data["upstream_accepted"] is True
    if operation != "upload_attachment":
        assert data["verification"] == "matched", data
    dispatched = [r for r in synthetic.requests if r.method != "GET"]
    assert len(dispatched) == 1
    assert (dispatched[0].method, dispatched[0].url.path) == (method, upstream_path)
    assert dispatched[0].headers["X-Redmine-API-Key"] == "offline-redmine-key"


@pytest.mark.asyncio
@pytest.mark.parametrize("case", WRITES, ids=[row[0] for row in WRITES])
async def test_reader_deployment_denies_all_writes(
    application_factory: Any, synthetic: Any, case: Any
) -> None:
    _, method, path, payload, _ = case
    async with application_factory() as app:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-redmine-key"},
        ) as client:
            response = await client.request(method, path, json=payload)
        assert response.status_code == 403
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("case", WRITES, ids=[row[0] for row in WRITES])
async def test_known_permission_denial_prevents_write(
    writer_app: Any, synthetic: Any, case: Any
) -> None:
    operation, method, path, payload, _ = case
    prepare(synthetic, operation)
    if operation == "upload_attachment":
        synthetic.write_failure = 403
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-reader-key"},
    ) as client:
        response = await client.request(method, path, json=payload)
    if operation == "upload_attachment":
        # Global evidence remains partial; the upstream must enforce its final grant.
        assert response.status_code == 403
        assert synthetic.writes == 1
    else:
        assert response.status_code == 403, response.text
        assert synthetic.writes == 0


@pytest.mark.asyncio
async def test_current_readers_and_caller_specific_discovery(
    writer_app: Any, synthetic: Any
) -> None:
    async with mcp_session(writer_app) as session:
        tools = (await session.list_tools()).tools
        assert {t.name for t in tools} == set(READ_OPERATIONS) | set(WRITE_OPERATIONS)
        for operation in READ_OPERATIONS:
            result = await session.call_tool(operation, READ_ARGUMENTS.get(operation, {}))
            assert not result.isError, (operation, result)
        assert all(t.annotations.readOnlyHint for t in tools if t.name in READ_OPERATIONS)
    async with mcp_session(writer_app, "offline-reader-key") as session:
        tools = (await session.list_tools()).tools
        assert {t.name for t in tools} == set(READ_OPERATIONS) | {"upload_attachment"}
        hidden = await session.call_tool("create_issue", {"project_id": 7, "subject": "denied"})
        assert hidden.isError
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [403, 422, httpx.ReadTimeout("private-error")])
async def test_create_error_sanitization_and_no_retry(
    writer_app: Any, synthetic: Any, failure: Any
) -> None:
    synthetic.write_failure = failure
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-redmine-key"},
    ) as client:
        response = await client.post("/api/v1/issues", json={"project_id": 7, "subject": "x"})
    if isinstance(failure, Exception):
        assert response.status_code == 200
        assert response.json()["outcome"] == "uncertain"
    else:
        assert response.status_code == failure
    assert "private-error" not in response.text and "must-not-leak" not in response.text
    assert synthetic.writes == 1


@pytest.mark.asyncio
async def test_accepted_write_with_failed_readback_is_not_a_failed_write(
    writer_app: Any, synthetic: Any
) -> None:
    synthetic.readback_failure = True
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-redmine-key"},
    ) as client:
        response = await client.put("/api/v1/issues/42", json={"subject": "changed"})
    assert response.status_code == 200
    assert response.json()["outcome"] == "accepted"
    assert response.json()["verification"] == "unavailable"
    assert synthetic.issues[42]["subject"] == "changed"
