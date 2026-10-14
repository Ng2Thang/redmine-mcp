"""WRT-06/07: optional fields, copy/query contracts and post-commit uncertainty."""

import copy
import json
from typing import Any

import httpx
import pytest

from tests.helpers import ISSUE
from tests.issue_write_helpers import invoke, override, writes

pytestmark = pytest.mark.asyncio

FIELDS = {
    "subject": "supplied subject",
    "category_id": 9,
    "fixed_version_id": 100,
    "assigned_to_id": "me",
    "parent_issue_id": 43,
    "description": None,
    "start_date": "2026-10-01",
    "due_date": "2026-10-10",
    "done_ratio": 50,
    "estimated_hours": 1.25,
    "is_private": True,
    "custom_fields": [
        {"id": 11, "value": "text"},
        {"id": 12, "value": ["a", "b"]},
        {"id": 13, "value": None},
    ],
    "uploads": [{"token": "9.abc", "filename": "sample.txt", "description": " trimmed "}],
}


def arguments(operation: str) -> tuple[str, dict[str, Any]]:
    if operation == "update":
        return "update_issue", {"issue_id": 42, **copy.deepcopy(FIELDS)}
    return "create_issue", {
        "project_id": 7,
        **copy.deepcopy(FIELDS),
        "watcher_user_ids": [8, 3],
        **({"copy_from": 43} if operation == "copy" else {}),
    }


def observed_issue(synthetic: Any, issue_id: int) -> dict[str, Any]:
    return {
        **copy.deepcopy(ISSUE),
        "id": issue_id,
        "subject": "supplied subject",
        "category": {"id": 9, "name": "Category"},
        "fixed_version": {"id": 100, "name": "Release"},
        "assigned_to": {"id": 3, "name": "Caller"},
        "parent": {"id": 43},
        "description": None,
        "start_date": "2026-10-01",
        "due_date": "2026-10-10",
        "done_ratio": 50,
        "estimated_hours": 1.25,
        "is_private": True,
        "custom_fields": [
            {"id": 11, "name": "Text", "value": "text"},
            {"id": 12, "name": "Multi", "value": ["b", "a"]},
            {"id": 13, "name": "Nullable", "value": None},
        ],
        "attachments": [{**copy.deepcopy(synthetic.attachment), "description": "trimmed"}],
        "watchers": [{"id": 3, "name": "Caller"}, {"id": 8, "name": "Other"}],
    }


def native_variant(synthetic: Any, operation: str, fault: str = "none") -> int:
    issue_id = 42 if operation == "update" else 44

    def respond(request: httpx.Request) -> httpx.Response | None:
        if request.method in {"POST", "PUT"} and request.url.path in {
            "/issues.json",
            "/issues/42.json",
        }:
            synthetic.issues[issue_id] = observed_issue(synthetic, issue_id)
            if fault == "lost_reply":
                raise httpx.ReadTimeout("private-commit-reply")
            return (
                httpx.Response(204)
                if operation == "update"
                else httpx.Response(201, json={"issue": {"id": issue_id}})
            )
        if synthetic.writes and request.url.path == f"/issues/{issue_id}.json":
            if fault == "forbidden":
                return httpx.Response(403)
            observed = copy.deepcopy(synthetic.issues[issue_id])
            if fault == "malformed":
                observed = {"id": issue_id}
            elif fault == "wrong_id":
                observed["id"] = 999
            elif fault == "mismatch":
                observed["done_ratio"] = 0
            elif fault == "unavailable":
                observed.pop("custom_fields")
            return httpx.Response(200, json={"issue": observed})
        return None

    override(synthetic, respond)
    return issue_id


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("operation", ["copy", "update"])
@pytest.mark.parametrize("clear", [False, True])
async def test_optional_null_clears_are_serialized_and_omission_preserves_fields(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    operation: str,
    clear: bool,
) -> None:
    issue_id = 42 if operation == "update" else 44
    cleared = {
        "category_id": None,
        "fixed_version_id": None,
        "parent_issue_id": None,
        "description": None,
        "start_date": None,
        "due_date": None,
        "estimated_hours": None,
    }

    def respond(request: httpx.Request) -> httpx.Response | None:
        if request.method in {"POST", "PUT"}:
            observed = observed_issue(synthetic, issue_id)
            observed["subject"] = "changed"
            if clear:
                for reference in ("category", "fixed_version", "parent"):
                    observed.pop(reference)
                observed.update(
                    description=None, start_date=None, due_date=None, estimated_hours=None
                )
            synthetic.issues[issue_id] = observed
            return (
                httpx.Response(204)
                if operation == "update"
                else httpx.Response(201, json={"issue": {"id": issue_id}})
            )
        return None

    override(synthetic, respond)
    args = {"subject": "changed", **(cleared if clear else {})}
    if operation == "update":
        tool = "update_issue"
        args["issue_id"] = 42
    else:
        tool = "create_issue"
        args.update(project_id=7, copy_from=43)
    status, data = await invoke(writer_app, boundary, tool, args)
    assert status == 200 and data["verification"] == "matched"
    expected = {"subject": "changed", **(cleared if clear else {})}
    if operation == "copy":
        expected["project_id"] = 7
    assert data["field_verification"] == {field: "matched" for field in expected}
    assert json.loads(writes(synthetic)[0].content) == {"issue": expected}
    assert len(writes(synthetic)) == 1
    assert ("category" not in synthetic.issues[issue_id]) is clear


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("operation", ["create", "copy", "update"])
@pytest.mark.parametrize(
    "fault,verification",
    [
        ("none", "matched"),
        ("mismatch", "mismatch"),
        ("unavailable", "unavailable"),
    ],
)
async def test_optional_field_payloads_and_independent_observation(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    operation: str,
    fault: str,
    verification: str,
) -> None:
    source_control = copy.deepcopy(synthetic.issues[43])
    issue_id = native_variant(synthetic, operation, fault)
    tool, args = arguments(operation)
    status, data = await invoke(writer_app, boundary, tool, args)
    assert status == 200 and data["outcome"] == "accepted" and data["upstream_accepted"] is True
    assert data["resource_id"] == issue_id and data["verification"] == verification
    expected_fields = set(FIELDS) | (
        {"project_id", "watcher_user_ids"} if operation != "update" else set()
    )
    expected = {field: "matched" for field in expected_fields}
    if fault != "none":
        expected["done_ratio" if fault == "mismatch" else "custom_fields"] = verification
    assert data["field_verification"] == expected
    request = writes(synthetic)[0]
    assert len(writes(synthetic)) == 1
    native_payload = copy.deepcopy(FIELDS)
    if operation != "update":
        native_payload.update(project_id=7, watcher_user_ids=[8, 3])
    assert json.loads(request.content) == {"issue": native_payload}
    assert dict(request.url.params) == (
        {}
        if operation == "update"
        else {"project_id": "7", **({"copy_from": "43"} if operation == "copy" else {})}
    )
    assert request.headers["X-Redmine-API-Key"] == "offline-redmine-key"
    assert synthetic.issues[43] == source_control
    after = synthetic.requests[synthetic.requests.index(request) + 1 :]
    reads = [r for r in after if r.url.path == f"/issues/{issue_id}.json"]
    assert len(reads) == 1
    assert reads[0].url.params.get("include") == (
        "attachments" if operation == "update" else "attachments,watchers"
    )


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("operation", ["create", "copy", "update"])
@pytest.mark.parametrize("fault", ["forbidden", "malformed", "wrong_id"])
async def test_accepted_issue_write_does_not_become_failed_when_readback_is_unusable(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    operation: str,
    fault: str,
) -> None:
    issue_id = native_variant(synthetic, operation, fault)
    tool, args = arguments(operation)
    status, data = await invoke(writer_app, boundary, tool, args)
    assert status == 200 and data["outcome"] == "accepted" and data["upstream_accepted"] is True
    assert data["resource_id"] == issue_id and data["verification"] == "unavailable"
    assert data["observed_issue"] is None and len(writes(synthetic)) == 1
    assert synthetic.issues[issue_id]["subject"] == "supplied subject"


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "fault", ["missing", "boolean", "string", "malformed_json", "unexpected_status"]
)
async def test_unusable_creation_reply_has_no_invented_identity_or_search_retry(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    fault: str,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response | None:
        if request.method == "POST" and request.url.path == "/issues.json":
            synthetic.issues[44] = {**copy.deepcopy(ISSUE), "id": 44, "subject": "committed"}
            if fault == "malformed_json":
                return httpx.Response(201, content=b"not-json-private-body")
            payload = (
                {}
                if fault == "missing"
                else {"issue": {"id": True if fault == "boolean" else "44"}}
            )
            return httpx.Response(200 if fault == "unexpected_status" else 201, json=payload)
        return None

    override(synthetic, respond)
    status, data = await invoke(
        writer_app, boundary, "create_issue", {"project_id": 7, "subject": "committed"}
    )
    assert status == 200 and data["outcome"] == "uncertain"
    assert data["upstream_accepted"] is (None if fault == "unexpected_status" else True)
    assert data["resource_id"] is None and data["verification"] == "unavailable"
    assert len(writes(synthetic)) == 1 and synthetic.issues[44]["subject"] == "committed"
    after = synthetic.requests[synthetic.requests.index(writes(synthetic)[0]) + 1 :]
    assert not any(r.url.path.startswith("/issues") for r in after)
    assert "private-body" not in json.dumps(data)


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("operation", ["create", "update"])
async def test_committed_lost_reply_is_not_replayed_or_reclassified_as_acceptance(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    operation: str,
) -> None:
    issue_id = native_variant(synthetic, operation, "lost_reply")
    tool, args = arguments(operation)
    status, data = await invoke(writer_app, boundary, tool, args)
    assert status == 200 and data["outcome"] == "uncertain" and data["upstream_accepted"] is None
    assert data["resource_id"] == (42 if operation == "update" else None)
    assert data["verification"] == ("matched" if operation == "update" else "unavailable")
    assert (
        len(writes(synthetic)) == 1 and synthetic.issues[issue_id]["subject"] == "supplied subject"
    )
    assert "private-commit-reply" not in json.dumps(data)
