"""Writer validation and authorization-before-dispatch with fake ports."""

from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.attachments.models import (
    AttachmentContainerRequest,
    AttachmentUpdateRequest,
)
from redmine_mcp.features.attachments.service import AttachmentService
from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.issues.write_models import (
    IssueCreateRequest,
    IssueNoteUpdateRequest,
    IssueRelationCreateRequest,
    IssueUpdateRequest,
    IssueWatcherAddRequest,
)
from redmine_mcp.features.projects.models import AddProjectFileRequest
from redmine_mcp.features.projects.service import ProjectService


@pytest.mark.parametrize(
    "model,values",
    [
        (IssueCreateRequest, {"project_id": 7}),
        (IssueCreateRequest, {"project_id": True, "subject": "x"}),
        (IssueCreateRequest, {"project_id": 7, "subject": " "}),
        (IssueUpdateRequest, {}),
        (IssueUpdateRequest, {"notes": " "}),
        (IssueUpdateRequest, {"private_notes": True}),
        (IssueUpdateRequest, {"subject": None}),
        (IssueNoteUpdateRequest, {}),
        (IssueNoteUpdateRequest, {"notes": None}),
        (IssueRelationCreateRequest, {"issue_to_id": 42, "delay": 1}),
        (
            IssueRelationCreateRequest,
            {"issue_to_id": 42, "relation_type": "follows", "delay": True},
        ),
        (IssueWatcherAddRequest, {"user_id": 0}),
    ],
)
def test_invalid_writer_inputs(model: Any, values: Any) -> None:
    with pytest.raises(ValidationError):
        model(**values)


def test_omission_null_and_empty_note_contracts() -> None:
    assert IssueUpdateRequest(description=None).model_dump(exclude_unset=True) == {
        "description": None
    }
    assert IssueUpdateRequest(notes="hello").model_dump(exclude_unset=True) == {"notes": "hello"}
    assert IssueNoteUpdateRequest(notes="").notes == ""
    assert IssueCreateRequest(project_id=7, copy_from=42).subject is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,args,port",
    [
        ("create_issue", (IssueCreateRequest(project_id=7, subject="x"),), "creator"),
        ("update_issue", (42, IssueUpdateRequest(notes="x")), "updater"),
        ("update_issue_note", (42, 1, IssueNoteUpdateRequest(notes="x")), "note_updater"),
        (
            "create_issue_relation",
            (42, IssueRelationCreateRequest(issue_to_id=43)),
            "relation_creator",
        ),
        ("delete_issue_relation", (1,), "relation_deleter"),
        ("add_issue_watcher", (42, 3), "watcher_adder"),
        ("remove_issue_watcher", (42, 3), "watcher_remover"),
    ],
)
async def test_permission_denial_prevents_issue_writer_dispatch(
    method: Any, args: Any, port: Any
) -> None:
    writer = AsyncMock()
    auth = AsyncMock()
    auth.authorize.side_effect = ApplicationError("permission_denied", "denied", 403)
    service = IssueService(AsyncMock(), authorizer=auth, **{port: writer})
    with pytest.raises(ApplicationError):
        await getattr(service, method)(*args)
    assert writer.mock_calls == []
    assert auth.authorize.await_args.args[0].operation == method


@pytest.mark.asyncio
@pytest.mark.parametrize("filename,content", [("../x", "eA=="), ("x", "???"), ("x", "eHh4eA==")])
async def test_invalid_upload_never_dispatches(filename: Any, content: Any) -> None:
    writer = AsyncMock()
    with pytest.raises(ApplicationError):
        await AttachmentService(AsyncMock(), writer, max_binary_bytes=3).upload_attachment(
            filename, content
        )
    writer.upload_attachment.assert_not_awaited()


@pytest.mark.asyncio
async def test_download_disabled_without_reader_access() -> None:
    reader = AsyncMock()
    with pytest.raises(ApplicationError) as error:
        await AttachmentService(reader).download_attachment(1)
    assert error.value.code == "attachment_download_disabled"
    assert reader.mock_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation", ["upload_attachment", "update_attachment", "delete_attachment", "add_project_file"]
)
async def test_artifact_writer_denial_prevents_dispatch(operation: Any) -> None:
    writer = AsyncMock()
    auth = AsyncMock()
    auth.authorize.side_effect = ApplicationError("permission_denied", "denied", 403)
    if operation == "add_project_file":
        call = ProjectService(AsyncMock(), writer, auth).add_project_file(
            7, AddProjectFileRequest(token="9.abc", filename="x")
        )
    else:
        service = AttachmentService(
            AsyncMock(), writer, metadata_writer=writer, deleter=writer, authorizer=auth
        )
        if operation == "upload_attachment":
            call = service.upload_attachment("x", "eA==")
        elif operation == "update_attachment":
            call = service.update_attachment(
                9, AttachmentUpdateRequest(container_type="project", container_id=7, description="")
            )
        else:
            call = service.delete_attachment(
                9, AttachmentContainerRequest(container_type="project", container_id=7)
            )
    with pytest.raises(ApplicationError):
        await call
    assert writer.mock_calls == []
    assert auth.authorize.await_args.args[0].operation == operation


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method",
    ["get_project", "list_project_versions", "list_project_issue_categories", "list_project_files"],
)
@pytest.mark.parametrize("value", [0, True, "7"])
async def test_project_context_validation_prevents_gateway_calls(method: Any, value: Any) -> None:
    reader = AsyncMock()
    with pytest.raises(ApplicationError):
        await getattr(ProjectService(reader), method)(value)
    assert reader.mock_calls == []
