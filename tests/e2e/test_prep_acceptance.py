"""Owned native acceptance for prep-022 through prep-026."""

import json
from uuid import uuid4

import pytest

from tests.e2e.test_catalog_acceptance import catalog_fixture
from tests.helpers import mcp_session

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def preparation_fixture(live_manifest):
    yield from catalog_fixture.__wrapped__(live_manifest)


async def test_live_sdk_assignment_null_clear_and_upload(live, preparation_fixture):
    project = preparation_fixture["projects"]["parent"]
    try:
        async with live.application(operations="allowed_all") as app:
            transport = app.state.mcp._http_transport
            async with mcp_session(app, live.key("a")) as session:
                result = await session.call_tool(
                    "create_issue",
                    {
                        "project_id": project,
                        "subject": "Prep022 disposable issue",
                        "description": "clear me",
                        "estimated_hours": 2,
                        "due_date": "2026-10-20",
                    },
                )
                assert not result.isError
                issue = json.loads(result.content[0].text)["resource_id"]
                for assignment in (live.manifest["users"]["b"]["id"], "me", None):
                    result = await session.call_tool(
                        "update_issue",
                        {
                            "issue_id": issue,
                            "assigned_to_id": assignment,
                            "description": None,
                            "estimated_hours": None,
                            "due_date": None,
                        },
                    )
                    assert not result.isError
                    receipt = json.loads(result.content[0].text)
                    assert receipt["outcome"] == "accepted" and receipt["upstream_accepted"] is True
                    raw = (await live.redmine("GET", f"issues/{issue}.json", user="a"))["issue"]
                    expected = (
                        live.manifest["users"]["a"]["id"] if assignment == "me" else assignment
                    )
                    assert raw.get("assigned_to", {}).get("id") == expected
                    assert not raw.get("description") and raw.get("estimated_hours") is None
                    assert raw.get("due_date") is None
                result = await session.call_tool(
                    "upload_attachment",
                    {
                        "filename": "prep024.txt",
                        "content_base64": "aGVsbG8=",
                    },
                )
                assert not result.isError
                upload = json.loads(result.content[0].text)
                live.attachments.append(upload["attachment_id"])
                assert upload["outcome"] == "accepted"
                result = await session.call_tool(
                    "update_issue",
                    {
                        "issue_id": issue,
                        "uploads": [{"token": upload["token"], "filename": "prep024.txt"}],
                    },
                )
                assert not result.isError
                assert json.loads(result.content[0].text)["outcome"] == "accepted"
            assert transport._manager_started
        assert transport._manager_task.done() and not transport._manager_started
        assert app.state.mcp._http_client.is_closed
    finally:
        if "issue" in locals():
            raw = (await live.redmine("GET", f"issues/{issue}.json"))["issue"]
            assert raw["project"]["id"] == project
            assert raw["subject"] == "Prep022 disposable issue"
            await live.redmine("DELETE", f"issues/{issue}.json", expected=204)
        await live.cleanup()


async def test_live_ten_item_membership_lifecycle(live, preparation_fixture):
    prefix = "mcp-e2e-prep023-" + uuid4().hex
    projects = []
    roles = preparation_fixture["roles"]
    target = live.manifest["users"]["b"]["id"]
    try:
        for index in range(10):
            raw = await live.redmine(
                "POST",
                "projects.json",
                expected=201,
                json={
                    "project": {
                        "name": f"Prep023 {index}",
                        "identifier": f"{prefix}-{index}",
                        "is_public": False,
                        "enabled_module_names": ["issue_tracking"],
                    }
                },
            )
            project = raw["project"]["id"]
            projects.append(project)
            await live.redmine(
                "POST",
                f"projects/{project}/memberships.json",
                expected=201,
                json={
                    "membership": {
                        "user_id": live.manifest["users"]["a"]["id"],
                        "role_ids": [roles["manager"]],
                    }
                },
            )
        async with live.application(operations="allowed_all") as app:
            async with mcp_session(app, live.key("a")) as session:
                result = await session.call_tool(
                    "add_project_members",
                    {
                        "items": [
                            {"project_id": project, "user_id": target, "role_ids": [roles["read"]]}
                            for project in projects
                        ]
                    },
                )
                assert not result.isError
                rows = json.loads(result.content[0].text)["results"]
                assert len(rows) == 10 and all(r["outcome"] == "accepted" for r in rows)
                memberships = []
                for project in projects:
                    native = await live.redmine(
                        "GET", f"projects/{project}/memberships.json", user="a"
                    )
                    member = next(
                        m for m in native["memberships"] if m.get("user", {}).get("id") == target
                    )
                    assert {r["id"] for r in member["roles"]} == {roles["read"]}
                    memberships.append(member["id"])
                for operation, role in (
                    ("update_project_members", roles["other"]),
                    ("delete_project_members", None),
                ):
                    items = [
                        {
                            "project_id": p,
                            "membership_id": m,
                            **({"role_ids": [role]} if role else {}),
                        }
                        for p, m in zip(projects, memberships, strict=True)
                    ]
                    result = await session.call_tool(operation, {"items": items})
                    assert not result.isError
                    rows = json.loads(result.content[0].text)["results"]
                    assert len(rows) == 10 and all(r["outcome"] == "accepted" for r in rows)
                    for project in projects:
                        native = await live.redmine(
                            "GET", f"projects/{project}/memberships.json", user="a"
                        )
                        matches = [
                            m
                            for m in native["memberships"]
                            if m.get("user", {}).get("id") == target
                        ]
                        assert (
                            (len(matches) == 1 and {r["id"] for r in matches[0]["roles"]} == {role})
                            if role
                            else not matches
                        )
    finally:
        for project in reversed(projects):
            raw = await live.redmine("GET", f"projects/{project}.json")
            assert raw["project"]["identifier"].startswith(prefix + "-")
            await live.redmine("DELETE", f"projects/{project}.json", expected=204)
            await live.redmine("GET", f"projects/{project}.json", expected=404)
