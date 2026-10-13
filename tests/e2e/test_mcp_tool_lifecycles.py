"""Registered MCP tools against native, owned version-selected Redmine state."""

import json
from fractions import Fraction
from typing import Any
from uuid import uuid4

import pytest

from redmine_mcp.auth import READ_OPERATIONS
from tests.e2e.test_catalog_acceptance import catalog_fixture as catalog_fixture
from tests.e2e.test_time_entry_update_acceptance import time_fixture as time_fixture
from tests.helpers import mcp_session

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]

READ_CASES = {
    "get_current_user": ("users/current.json", "user"),
    "list_my_project_capabilities": (None, None),
    "list_projects": ("projects.json", "projects"),
    "get_project": ("projects/{project}.json", "project"),
    "list_project_versions": ("projects/{project}/versions.json", "versions"),
    "list_project_issue_categories": (
        "projects/{project}/issue_categories.json",
        "issue_categories",
    ),
    "list_project_files": ("projects/{project}/files.json", "files"),
    "list_project_time_entry_activities": ("projects/{project}.json", "project"),
    "list_project_members": ("projects/{project}/memberships.json", "memberships"),
    "list_issues": ("issues.json", "issues"),
    "get_issue": ("issues/{issue}.json", "issue"),
    "get_attachment": ("attachments/{attachment}.json", "attachment"),
    "list_issue_time_entries": ("time_entries.json", "time_entries"),
    "list_time_entries": ("time_entries.json", "time_entries"),
    "list_issue_statuses": ("issue_statuses.json", "issue_statuses"),
    "list_issue_priorities": ("enumerations/issue_priorities.json", "issue_priorities"),
    "list_document_categories": ("enumerations/document_categories.json", "document_categories"),
    "list_trackers": ("trackers.json", "trackers"),
}


async def call(session: Any, operation: str, **arguments: Any) -> dict[str, Any]:
    result = await session.call_tool(operation, arguments)
    # Do not expose upstream bodies, temporary upload tokens or personal keys on failure.
    assert not result.isError, f"MCP {operation} failed"
    return json.loads(result.content[0].text)


def accepted(receipt: dict[str, Any]) -> None:
    assert receipt["outcome"] == "accepted"
    assert receipt["upstream_accepted"] is True
    assert receipt["verification"] == "matched"


@pytest.mark.parametrize("operation", READ_CASES)
async def test_each_reader_matches_native_caller_state(live: Any, operation: str) -> None:
    assert set(READ_CASES) == set(READ_OPERATIONS), "Add native parity for new reader tools"
    project = live.manifest["projects"]["a"]
    issue = live.manifest["issues"]["a"]
    arguments: dict[str, Any] = {}
    params: dict[str, Any] = {}
    attachment = None
    try:
        if operation in ("get_attachment", "list_project_files"):
            async with live.client() as client:
                uploaded = await live.upload(client)
                attachment = uploaded["attachment_id"]
                response = await client.post(
                    f"/api/v1/projects/{project}/files",
                    json={"token": uploaded["token"], "filename": "e2e.txt"},
                )
                assert response.status_code == 200
                accepted(response.json())
        if operation.startswith("list_project_") or operation in (
            "get_project", "list_my_project_capabilities"
        ):
            arguments = {"project_id": project}
        if operation == "list_project_members":
            arguments = {"project_ids": [project], "limit": 100}
            params = {"limit": 100}
        if operation in ("get_issue", "list_issue_time_entries", "list_time_entries"):
            arguments = {"issue_id": issue}
        if operation in ("list_issue_time_entries", "list_time_entries"):
            arguments["limit"] = 100
            params = {"issue_id": issue, "limit": 100}
        if operation == "get_attachment":
            arguments = {"attachment_id": attachment}
        if operation == "list_issues":
            arguments = {"project_id": project, "status_id": "*", "limit": 100}
            params = {
                "project_id": project, "subproject_id": "!*", "status_id": "*", "limit": 100
            }
        if operation == "list_projects":
            arguments = {"limit": 100}
            params = {"limit": 100}
        if operation == "list_project_time_entry_activities":
            params = {"include": "time_entry_activities"}
        async with (
            live.application(writer=False) as app,
            mcp_session(app, live.key("a")) as session,
        ):
            names = {tool.name for tool in (await session.list_tools()).tools}
            assert names == set(READ_OPERATIONS)
            payload = await call(session, operation, **arguments)
        if operation == "list_my_project_capabilities":
            assert len(payload["items"]) == 1
            item = payload["items"][0]
            assert payload["user_id"] == live.manifest["users"]["a"]["id"]
            assert item["id"] == project and item["membership_state"] == "known"
            assert any(row["operation_id"] == "get_issue" for row in item["tools"])
            native = await live.redmine(
                "GET", "users/current.json", user="a", params={"include": "memberships"}
            )
            member = next(
                row for row in native["user"]["memberships"] if row["project"]["id"] == project
            )
            assert {row["id"] for row in item["roles"]} == {
                row["id"] for row in member["roles"]
            }
            return
        path, key = READ_CASES[operation]
        assert path is not None and key is not None
        native = await live.redmine(
            "GET", path.format(project=project, issue=issue, attachment=attachment),
            user="a", params=params,
        )
        expected = native[key]
        if operation.startswith("get_"):
            assert payload["id"] == expected["id"]
            fields = {
                "get_current_user": ("login",),
                "get_project": ("identifier", "name", "status"),
                "get_issue": ("subject", "project", "tracker", "status"),
                "get_attachment": ("filename", "filesize", "description"),
            }[operation]
            for field in fields:
                if operation == "get_issue" and field in ("project", "tracker", "status"):
                    # MCP Reference exposes id/name; native status can also include is_closed.
                    reference = expected[field]
                    assert payload[field] == {
                        "id": reference["id"],
                        "name": reference["name"],
                    }, field
                else:
                    assert payload.get(field) == expected.get(field), field
        else:
            rows = payload["items"] if operation != "list_project_members" else None
            if operation == "list_project_members":
                assert len(payload["results"]) == 1
                result = payload["results"][0]
                assert result["project_id"] == project and result["outcome"] == "read"
                rows = result["page"]["items"]
            if operation == "list_project_time_entry_activities":
                expected = expected["time_entry_activities"]
            # Redmine 6 may return the entire project catalog despite limit=100.
            if operation == "list_projects":
                expected = expected[:100]
            assert rows is not None
            assert {row["id"] for row in rows} == {row["id"] for row in expected}
            if operation in (
                "list_issue_statuses", "list_issue_priorities",
                "list_document_categories", "list_trackers",
                "list_project_time_entry_activities",
            ):
                assert rows, "Owned fixture must provide a populated reference catalog"
            upstream = {row["id"]: row for row in expected}
            for row in rows:
                for field in ("name", "filename", "subject", "spent_on"):
                    if field in row:
                        assert row[field] == upstream[row["id"]][field], field
            if attachment is not None:
                assert attachment in {row["id"] for row in rows}
    finally:
        await live.cleanup()


async def test_mcp_issue_notes_relations_and_watchers_lifecycle(live: Any) -> None:
    project = live.manifest["projects"]["a"]
    user = live.manifest["users"]["a"]["id"]
    try:
        async with live.application() as app, mcp_session(app, live.key("a")) as session:
            for subject in ("MCP lifecycle source", "MCP lifecycle target"):
                receipt = await call(session, "create_issue", project_id=project, subject=subject)
                if receipt.get("resource_id"):
                    live.created_issues.append(receipt["resource_id"])
                accepted(receipt)
                assert (await live.owned_issue(receipt["resource_id"]))["subject"] == subject
            issue, target = live.created_issues
            receipt = await call(
                session, "update_issue", issue_id=issue,
                subject="MCP updated", notes="MCP original note",
            )
            accepted(receipt)
            journal = receipt["journal_id"]
            assert journal is not None
            accepted(await call(
                session, "update_issue_note", issue_id=issue,
                journal_id=journal, notes="MCP edited note",
            ))
            native = await live.redmine(
                "GET", f"issues/{issue}.json", user="a", params={"include": "journals"}
            )
            assert native["issue"]["subject"] == "MCP updated"
            assert next(row for row in native["issue"]["journals"] if row["id"] == journal)[
                "notes"
            ] == "MCP edited note"
            relation = await call(
                session, "create_issue_relation", issue_id=issue, issue_to_id=target
            )
            accepted(relation)
            relation_id = relation["resource_id"]
            for endpoint in (issue, target):
                rows = await live.redmine("GET", f"issues/{endpoint}/relations.json", user="a")
                assert relation_id in {row["id"] for row in rows["relations"]}
            receipt = await call(session, "delete_issue_relation", relation_id=relation_id)
            accepted(receipt)
            assert receipt["observed_present"] is False
            for endpoint in (issue, target):
                rows = await live.redmine("GET", f"issues/{endpoint}/relations.json", user="a")
                assert relation_id not in {row["id"] for row in rows["relations"]}
            watcher_calls = (("add_issue_watcher", True), ("remove_issue_watcher", False))
            for operation, present in watcher_calls:
                receipt = await call(session, operation, issue_id=issue, user_id=user)
                accepted(receipt)
                assert receipt["observed_present"] is present
                native = await live.redmine(
                    "GET", f"issues/{issue}.json", user="a", params={"include": "watchers"}
                )
                assert (user in {row["id"] for row in native["issue"]["watchers"]}) is present
    finally:
        await live.cleanup()


async def test_mcp_project_file_attachment_lifecycle(live: Any) -> None:
    project = live.manifest["projects"]["a"]
    try:
        async with live.application() as app, mcp_session(app, live.key("a")) as session:
            uploaded = await call(
                session, "upload_attachment",
                filename="mcp-lifecycle.txt", content_base64="aGVsbG8=",
            )
            attachment = uploaded.get("attachment_id")
            if attachment:
                live.attachments.append(attachment)
            assert uploaded["outcome"] == "accepted" and uploaded["upstream_accepted"] is True
            assert attachment and uploaded["token"]
            receipt = await call(
                session, "add_project_file", project_id=project,
                token=uploaded["token"], filename="mcp-lifecycle.txt", description="MCP original",
            )
            accepted(receipt)
            assert receipt["attachment_id"] == attachment
            rows = await call(session, "list_project_files", project_id=project)
            assert attachment in {row["id"] for row in rows["items"]}
            context = {
                "attachment_id": attachment, "container_type": "project", "container_id": project
            }
            accepted(await call(session, "update_attachment", **context, description="MCP changed"))
            detail = await call(session, "get_attachment", attachment_id=attachment)
            native = await live.redmine("GET", f"attachments/{attachment}.json", user="a")
            native = native["attachment"]
            assert detail["description"] == native["description"] == "MCP changed"
            assert detail["filesize"] == native["filesize"] == 5
            receipt = await call(session, "delete_attachment", **context)
            accepted(receipt)
            assert receipt["observed_present"] is False
            await live.redmine("GET", f"attachments/{attachment}.json", user="a", expected=404)
            rows = await call(session, "list_project_files", project_id=project)
            assert attachment not in {row["id"] for row in rows["items"]}
    finally:
        await live.cleanup()


async def test_mcp_time_entry_create_update_delete_lifecycle(time_fixture: Any) -> None:
    live = time_fixture
    created = await live.redmine(
        "POST", "issues.json", expected=201,
        json={"issue": {"project_id": live.time_project, "subject": "MCP time lifecycle"}},
    )
    issue = created["issue"]["id"]
    # The task-owned time fixture removes its project, entries and users even on failure.
    async with live.application() as app, mcp_session(app, live.key("time_own")) as session:
        receipt = await call(
            session, "create_time_entry", issue_id=issue, hours=1.5, spent_on="2026-10-01",
            activity_id=live.time_activities["active"], comments="MCP time original",
        )
        accepted(receipt)
        entry = receipt["resource_id"]
        native = (await live.redmine("GET", f"time_entries/{entry}.json"))["time_entry"]
        assert Fraction(str(native["hours"])) == Fraction(3, 2)
        assert native["user"]["id"] == live.manifest["users"]["time_own"]["id"]
        assert native["issue"]["id"] == issue
        receipt = await call(
            session, "update_time_entry", issue_id=issue, time_entry_id=entry,
            hours=2, comments="MCP time changed",
        )
        accepted(receipt)
        native = (await live.redmine("GET", f"time_entries/{entry}.json"))["time_entry"]
        assert Fraction(str(native["hours"])) == 2 and native["comments"] == "MCP time changed"
        assert native["spent_on"] == "2026-10-01"
        for operation in ("list_issue_time_entries", "list_time_entries"):
            rows = await call(session, operation, issue_id=issue)
            assert {row["id"] for row in rows["items"]} == {entry}
        receipt = await call(session, "delete_time_entry", issue_id=issue, time_entry_id=entry)
        assert receipt["outcome"] == "accepted" and receipt["upstream_accepted"] is True
        assert receipt["verification"] == "not_found" and receipt["observed_present"] is False
        await live.redmine("GET", f"time_entries/{entry}.json", expected=404)
        for operation in ("list_issue_time_entries", "list_time_entries"):
            assert (await call(session, operation, issue_id=issue))["items"] == []
        native = (await live.redmine("GET", f"issues/{issue}.json"))["issue"]
        assert native["spent_hours"] == 0


async def test_mcp_version_and_membership_lifecycle(live: Any, catalog_fixture: Any) -> None:
    project = catalog_fixture["projects"]["parent"]
    roles = catalog_fixture["roles"]
    user = live.manifest["users"]["own"]["id"]
    # The catalog fixture owns and removes the project, version and memberships.
    async with (
        live.application(operations="allowed_all") as app,
        mcp_session(app, live.key("a")) as session,
    ):
        name = "MCP lifecycle " + uuid4().hex
        receipt = await call(session, "create_project_version", project_id=project, name=name)
        accepted(receipt)
        native = await live.redmine("GET", f"versions/{receipt['resource_id']}.json")
        version = native["version"]
        assert version["project"]["id"] == project
        assert version["name"] == name
        assert version["status"] == "open" and version["sharing"] == "none"
        result = await call(
            session, "add_project_members",
            items=[{"project_id": project, "user_id": user, "role_ids": [roles["read"]]}],
        )
        assert result["phase"] == "executed" and len(result["results"]) == 1
        row = result["results"][0]
        assert row["outcome"] == "accepted" and row["verification"] == "matched"
        membership = row["membership_id"]
        for role, operation in ((roles["read"], None), (roles["other"], "update_project_members")):
            if operation:
                result = await call(
                    session, operation,
                    items=[{
                        "project_id": project,
                        "membership_id": membership,
                        "role_ids": [role],
                    }],
                )
                row = result["results"][0]
                assert row["outcome"] == "accepted" and row["verification"] == "matched"
            native = await live.redmine("GET", f"projects/{project}/memberships.json")
            member = next(row for row in native["memberships"] if row["id"] == membership)
            assert member["user"]["id"] == user
            assert {row["id"] for row in member["roles"]} == {role}
        result = await call(
            session, "delete_project_members",
            items=[{"project_id": project, "membership_id": membership}],
        )
        row = result["results"][0]
        assert row["outcome"] == "accepted" and row["verification"] == "matched"
        native = await live.redmine("GET", f"projects/{project}/memberships.json")
        assert membership not in {row["id"] for row in native["memberships"]}
