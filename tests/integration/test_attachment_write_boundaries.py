"""WRT-03: container membership must precede metadata changes or deletion."""

import copy
import json
from typing import Any

import httpx
import pytest

from tests.issue_write_helpers import assert_error, invoke, override, writes

pytestmark = pytest.mark.asyncio


def container_fixture(synthetic: Any, kind: str) -> int:
    target = copy.deepcopy(synthetic.attachment)
    control = {
        **copy.deepcopy(target),
        "id": 10,
        "filename": "control.txt",
        "content_url": "http://redmine.invalid/attachments/download/10/control.txt",
    }
    if kind == "version":
        synthetic.versions[100] = {
            "id": 100,
            "name": "Release",
            "project": {"id": 7, "name": "Demo"},
        }
        target["version"] = {"id": 100, "name": "Release"}
    synthetic.files = [target, control]
    synthetic.issues[42]["attachments"] = [copy.deepcopy(target), copy.deepcopy(control)]
    return {"project": 7, "version": 100, "issue": 42}[kind]


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("kind", ["project", "version", "issue"])
@pytest.mark.parametrize("operation", ["update_attachment", "delete_attachment"])
async def test_exact_container_proof_and_single_write_preserve_control(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    kind: str,
    operation: str,
) -> None:
    container = container_fixture(synthetic, kind)
    control = copy.deepcopy(synthetic.files[1])
    args = {"attachment_id": 9, "container_type": kind, "container_id": container}
    if operation == "update_attachment":
        args.update(filename="renamed.txt", description="")
    status, data = await invoke(writer_app, boundary, operation, args)
    assert status == 200 and data["outcome"] == "accepted" and data["upstream_accepted"] is True
    assert data["verification"] == "matched"
    request = writes(synthetic)[0]
    assert len(writes(synthetic)) == 1 and request.url.path == "/attachments/9.json"
    assert request.method == ("PATCH" if operation == "update_attachment" else "DELETE")
    if operation == "update_attachment":
        assert json.loads(request.content) == {
            "attachment": {"filename": "renamed.txt", "description": ""}
        }
        assert data["observed_attachment"]["filename"] == "renamed.txt"
    else:
        assert request.content == b"" and data["observed_present"] is False
        assert all(file["id"] != 9 for file in synthetic.files)
        assert all(a["id"] != 9 for a in synthetic.issues[42]["attachments"])
    assert request.headers["X-Redmine-API-Key"] == "offline-redmine-key"
    assert control in synthetic.files
    before = synthetic.requests[: synthetic.requests.index(request)]
    proof = "/issues/42.json" if kind == "issue" else "/projects/7/files.json"
    assert any(r.url.path == proof for r in before)
    if kind == "issue":
        assert any(
            r.url.path == proof and r.url.params.get("include") == "attachments" for r in before
        )
    if kind == "version":
        assert any(r.url.path == "/versions/100.json" for r in before)


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("operation", ["update_attachment", "delete_attachment"])
@pytest.mark.parametrize(
    "fault,kind,code",
    [
        ("wrong_container", "project", "resource_not_found"),
        ("wrong_version", "version", "resource_not_found"),
        ("wrong_project", "version", "resource_not_found"),
        ("missing_files", "project", "upstream_response"),
        ("malformed_files", "project", "upstream_response"),
        ("missing_attachments", "issue", "upstream_response"),
        ("wrong_issue", "issue", "resource_not_found"),
    ],
)
async def test_unproven_container_never_writes_even_with_visible_attachment_metadata(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    operation: str,
    fault: str,
    kind: str,
    code: str,
) -> None:
    container = container_fixture(synthetic, kind)
    if fault == "wrong_container":
        synthetic.files[0]["version"] = {"id": 100, "name": "Different container"}
    elif fault == "wrong_version":
        synthetic.files[0]["version"] = {"id": 101, "name": "Other version"}
    elif fault == "wrong_project":
        synthetic.versions[100]["project"]["id"] = 8
    elif fault == "missing_attachments":
        synthetic.issues[42].pop("attachments")
    elif fault == "wrong_issue":
        container = 43
    else:
        body = {} if fault == "missing_files" else {"files": [{"id": True}]}
        override(
            synthetic,
            lambda r: (
                httpx.Response(200, json=body) if r.url.path == "/projects/7/files.json" else None
            ),
        )
    before = copy.deepcopy(synthetic.attachment)
    args = {"attachment_id": 9, "container_type": kind, "container_id": container}
    if operation == "update_attachment":
        args["description"] = "must not change"
    status, data = await invoke(writer_app, boundary, operation, args)
    assert status == (422 if boundary == "mcp" else 404 if code == "resource_not_found" else 502)
    assert_error(data, boundary, code)
    assert writes(synthetic) == [] and synthetic.attachment == before


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "operation,fault,verification",
    [
        ("update_attachment", "unreadable", "unavailable"),
        ("update_attachment", "omitted_description", "unavailable"),
        ("update_attachment", "ignored_description", "mismatch"),
        ("delete_attachment", "unreadable", "unavailable"),
        ("delete_attachment", "still_present", "mismatch"),
    ],
)
async def test_accepted_attachment_write_preserves_unavailable_or_mismatching_readback(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    operation: str,
    fault: str,
    verification: str,
) -> None:
    container_fixture(synthetic, "project")
    old_files = copy.deepcopy(synthetic.files)

    def respond(request: httpx.Request) -> httpx.Response | None:
        if synthetic.writes:
            if operation == "update_attachment" and request.url.path == "/attachments/9.json":
                if fault == "unreadable":
                    return httpx.Response(403)
                observed = copy.deepcopy(synthetic.attachment)
                if fault == "omitted_description":
                    observed.pop("description")
                else:
                    observed["description"] = "ignored"
                return httpx.Response(200, json={"attachment": observed})
            if operation == "delete_attachment" and request.url.path == "/projects/7/files.json":
                return (
                    httpx.Response(403)
                    if fault == "unreadable"
                    else httpx.Response(200, json={"files": old_files})
                )
        return None

    override(synthetic, respond)
    args = {"attachment_id": 9, "container_type": "project", "container_id": 7}
    if operation == "update_attachment":
        args["description"] = "new description"
    status, data = await invoke(writer_app, boundary, operation, args)
    assert status == 200 and data["outcome"] == "accepted" and data["upstream_accepted"] is True
    assert data["verification"] == verification and len(writes(synthetic)) == 1
    if operation == "delete_attachment":
        assert data["observed_present"] is (True if fault == "still_present" else None)
