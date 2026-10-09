"""Real target-version permission and resulting-state acceptance on owned data."""

import json
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import pytest

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS
from tests.helpers import mcp_session

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def assert_ownership(live: Any) -> None:
    for name, project_id in live.manifest["projects"].items():
        data = live.manifest["metadata"]["projects"][str(project_id)]
        assert data["identifier"] == f"mcp-e2e-{name}"


async def test_all_live_tools_and_resulting_state(live: Any) -> None:
    await assert_ownership(live)
    project_id = live.manifest["projects"]["a"]
    user_id = live.manifest["users"]["a"]["id"]
    try:
        async with live.client() as client:
            first = await live.upload(client)
            response = await client.post(
                f"/api/v1/projects/{project_id}/files",
                json={"token": first["token"], "filename": "e2e.txt", "description": "owned"},
            )
            assert response.status_code == 200 and response.json()["verification"] == "matched"
            attachment_id = first["attachment_id"]
            response = await client.patch(
                f"/api/v1/attachments/{attachment_id}",
                json={
                    "container_type": "project",
                    "container_id": project_id,
                    "description": "changed",
                },
            )
            assert response.status_code == 200 and response.json()["verification"] == "matched"
            observed = await live.redmine("GET", f"attachments/{attachment_id}.json", user="a")
            assert observed["attachment"]["description"] == "changed"
            response = await client.post(
                "/api/v1/issues", json={"project_id": project_id, "subject": "E2E created"}
            )
            assert response.status_code == 200 and response.json()["outcome"] == "accepted"
            issue_id = response.json()["resource_id"]
            live.created_issues.append(issue_id)
            response = await client.post(
                "/api/v1/issues",
                json={"project_id": project_id, "copy_from": issue_id, "subject": "E2E copy"},
            )
            assert response.status_code == 200 and response.json()["outcome"] == "accepted"
            copy_id = response.json()["resource_id"]
            live.created_issues.append(copy_id)
            assert (await live.owned_issue(copy_id))["subject"] == "E2E copy"
            response = await client.put(
                f"/api/v1/issues/{issue_id}",
                json={"subject": "E2E changed", "notes": "E2E added note"},
            )
            assert response.status_code == 200 and response.json()["verification"] == "matched"
            journal_id = response.json()["journal_id"]
            assert journal_id is not None
            response = await client.put(
                f"/api/v1/issues/{issue_id}/notes/{journal_id}", json={"notes": "E2E edited note"}
            )
            assert response.status_code == 200 and response.json()["verification"] == "matched"
            response = await client.post(
                f"/api/v1/issues/{issue_id}/relations", json={"issue_to_id": copy_id}
            )
            assert response.status_code == 200 and response.json()["verification"] == "matched"
            relation_id = response.json()["resource_id"]
            response = await client.delete(f"/api/v1/relations/{relation_id}")
            assert response.status_code == 200 and response.json()["observed_present"] is False
            for method, path, body, present in [
                ("POST", f"/api/v1/issues/{issue_id}/watchers", {"user_id": user_id}, True),
                ("DELETE", f"/api/v1/issues/{issue_id}/watchers/{user_id}", None, False),
            ]:
                response = await client.request(method, path, json=body)
                assert (
                    response.status_code == 200 and response.json()["observed_present"] is present
                )
                observed = await live.redmine(
                    "GET", f"issues/{issue_id}.json", user="a", params={"include": "watchers"}
                )
                assert (
                    user_id in {row["id"] for row in observed["issue"].get("watchers", [])}
                ) is present
            args = {
                "get_project": {"project_id": project_id},
                "list_project_versions": {"project_id": project_id},
                "list_project_issue_categories": {"project_id": project_id},
                "list_project_files": {"project_id": project_id},
                "list_project_time_entry_activities": {"project_id": project_id},
                "list_project_members": {"project_ids": [project_id]},
                "get_issue": {"issue_id": issue_id},
                "get_attachment": {"attachment_id": attachment_id},
                "list_issue_time_entries": {"issue_id": live.manifest["issues"]["a"]},
                "list_my_project_capabilities": {"project_id": project_id},
                "list_issues": {"project_id": project_id},
            }
            async with live.application() as app:
                async with mcp_session(app, live.key("a")) as session:
                    names = {tool.name for tool in (await session.list_tools()).tools}
                    assert names == set(READ_OPERATIONS) | set(WRITE_OPERATIONS)
                    for operation in READ_OPERATIONS:
                        result = await session.call_tool(operation, args.get(operation, {}))
                        assert not result.isError, operation
                        if operation == "get_current_user":
                            assert json.loads(result.content[0].text)["id"] == user_id
            response = await client.delete(
                f"/api/v1/attachments/{attachment_id}",
                params={"container_type": "project", "container_id": project_id},
            )
            assert response.status_code == 200 and response.json()["observed_present"] is False
    finally:
        await live.cleanup()


async def test_contrasting_permissions_private_visibility_and_denied_unchanged_state(
    live: Any,
) -> None:
    await assert_ownership(live)
    issue_id = live.manifest["issues"]["a"]
    before = await live.owned_issue(issue_id)
    async with live.client(user="b") as client:
        response = await client.put(
            f"/api/v1/issues/{issue_id}", json={"subject": "MUST NOT CHANGE"}
        )
        assert response.status_code == 403
        private = await client.get(f"/api/v1/issues/{live.manifest['issues']['private']}")
        assert private.status_code in (403, 404)
        visible = await client.get(f"/api/v1/issues/{issue_id}", params={"include": "journals"})
        assert visible.status_code == 200
        assert all(note["notes"] != "E2E private note" for note in visible.json()["journals"])
    async with live.client() as client:
        visible = await client.get(f"/api/v1/issues/{issue_id}", params={"include": "journals"})
        assert visible.status_code == 200
        assert any(note["notes"] == "E2E private note" for note in visible.json()["journals"])
    assert (await live.owned_issue(issue_id))["subject"] == before["subject"]
    async with live.application() as app:
        for user in ("a", "b"):
            async with mcp_session(app, live.key(user)) as session:
                result = await session.call_tool(
                    "list_my_project_capabilities", {"project_id": live.manifest["projects"]["a"]}
                )
                assert not result.isError
                tools = json.loads(result.content[0].text)["items"][0]["tools"]
                candidates = {item["operation_id"] for item in tools}
                assert ("create_issue" in candidates) is (user == "a")


@pytest.mark.parametrize(
    "fixture,user,expected,changed",
    [
        ("own", "own", 200, True),
        ("own_other", "own", 200, False),
        ("tracker", "tracker", 200, True),
        ("tracker_other", "tracker", 200, False),
        ("closed", "a", 403, False),
        ("archived", "a", 403, False),
        ("disabled", "a", 403, False),
    ],
)
async def test_ownership_tracker_and_project_state_permissions(
    live: Any, fixture: Any, user: Any, expected: Any, changed: Any
) -> None:
    await assert_ownership(live)
    issue_id = live.manifest["issues"][fixture]
    before = await live.owned_issue(issue_id)
    try:
        async with live.client(user=user) as client:
            response = await client.put(
                f"/api/v1/issues/{issue_id}", json={"subject": "E2E permission check"}
            )
            assert response.status_code == expected
            if expected == 200:
                assert response.json()["verification"] == ("matched" if changed else "mismatch")
        after = await live.owned_issue(issue_id)
        assert after["subject"] == ("E2E permission check" if changed else before["subject"])
    finally:
        if changed:
            await live.redmine(
                "PUT",
                f"issues/{issue_id}.json",
                json={"issue": {"subject": before["subject"]}},
                expected=204,
            )


async def test_deployment_admission_applies_even_to_admin(live: Any) -> None:
    await assert_ownership(live)
    async with live.client(user="admin", admitted=live.manifest["users"]["a"]["id"]) as client:
        read = await client.get("/api/v1/projects")
        assert read.status_code == 200
        write = await client.post(
            "/api/v1/issues",
            json={"project_id": live.manifest["projects"]["a"], "subject": "denied"},
        )
        assert write.status_code == 403


async def test_separate_reader_deployment_cannot_write(live: Any) -> None:
    await assert_ownership(live)
    async with live.application(writer=False) as app:
        async with mcp_session(app, live.key("a")) as session:
            assert {tool.name for tool in (await session.list_tools()).tools} == set(
                READ_OPERATIONS
            )
    async with live.client(writer=False) as client:
        denied = await client.post(
            "/api/v1/issues",
            json={"project_id": live.manifest["projects"]["a"], "subject": "MUST NOT CREATE"},
        )
        assert denied.status_code == 403


async def test_multiple_group_and_inherited_roles(live: Any) -> None:
    await assert_ownership(live)
    async with live.application() as app:
        for user in ("a", "b"):
            async with mcp_session(app, live.key(user)) as session:
                result = await session.call_tool(
                    "list_my_project_capabilities",
                    {"project_id": live.manifest["projects"]["child"], "include_reasons": True},
                )
                assert not result.isError
                item = json.loads(result.content[0].text)["items"][0]
                assert item["membership_state"] == "known"
                assert any(role["inherited"] for role in item["roles"])
        async with mcp_session(app, live.key("a")) as session:
            result = await session.call_tool(
                "list_my_project_capabilities", {"project_id": live.manifest["projects"]["a"]}
            )
            roles = json.loads(result.content[0].text)["items"][0]["roles"]
            assert len(roles) == 2 and len({role["id"] for role in roles}) == 2


def permission_action(action: Any) -> None:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "redmine-mcp-e2e-redmine-1",
            "bundle",
            "exec",
            "rails",
            "runner",
            "/opt/testing/e2e_permissions.rb",
            action,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "Owned permission fixture action failed"


async def test_role_revocation_changes_scoped_capabilities_and_direct_calls(
    live: Any,
) -> None:
    await assert_ownership(live)
    project_id = live.manifest["projects"]["a"]
    async with live.application() as app:
        async with mcp_session(app, live.key("a")) as session:
            arguments = {"project_id": project_id, "operation_id": "create_issue"}
            before = await session.call_tool("list_my_project_capabilities", arguments)
            assert json.loads(before.content[0].text)["items"]
            inventory = await live.redmine(
                "GET", "issues.json", params={"project_id": project_id, "status_id": "*"}
            )
            try:
                permission_action("revoke")
                revoked = await session.call_tool("list_my_project_capabilities", arguments)
                assert not revoked.isError
                assert json.loads(revoked.content[0].text)["items"] == []
                result = await session.call_tool(
                    "create_issue", {"project_id": project_id, "subject": "MUST NOT CREATE"}
                )
                assert result.isError
                after = await live.redmine(
                    "GET", "issues.json", params={"project_id": project_id, "status_id": "*"}
                )
                assert after["total_count"] == inventory["total_count"]
            finally:
                permission_action("restore")
            restored = await session.call_tool("list_my_project_capabilities", arguments)
            assert json.loads(restored.content[0].text)["items"]


async def test_uncertain_create_reconciles_real_state_without_retry(
    live: Any, monkeypatch: Any
) -> None:
    await assert_ownership(live)
    project_id = live.manifest["projects"]["a"]
    subject = f"E2E uncertain {uuid4().hex}"
    original = httpx.AsyncHTTPTransport.handle_async_request
    dispatched = 0

    async def lose_create_response(transport: Any, request: Any) -> Any:
        nonlocal dispatched
        response = await original(transport, request)
        if request.method == "POST" and request.url.path == "/issues.json":
            dispatched += 1
            await response.aread()
            try:
                assert response.status_code == 201
                live.created_issues.append(response.json()["issue"]["id"])
            finally:
                await response.aclose()
            raise httpx.ReadTimeout("Simulated lost response after real commit", request=request)
        return response

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", lose_create_response)
    try:
        async with live.client() as client:
            receipt = await client.post(
                "/api/v1/issues", json={"project_id": project_id, "subject": subject}
            )
            assert receipt.status_code == 200 and receipt.json()["outcome"] == "uncertain"
            reconciled = await live.redmine(
                "GET", "issues.json", params={"project_id": project_id, "status_id": "*"}
            )
            matches = [row for row in reconciled["issues"] if row["subject"] == subject]
            assert len(matches) == 1
            assert matches[0]["id"] == live.created_issues[0]
            assert dispatched == 1
    finally:
        await live.cleanup()


async def test_received_500_after_real_commit_is_uncertain_without_retry(
    live: Any, monkeypatch: Any
) -> None:
    await assert_ownership(live)
    project_id = live.manifest["projects"]["a"]
    subject = f"E2E prep-019 {uuid4().hex}"
    state = Path(__file__).resolve().parents[2] / ".local/testing-e2e"
    evidence_dir = state / "prep-019" / uuid4().hex
    evidence_dir.mkdir(parents=True)
    cleanup_path = state / "last-cleanup.json"
    if cleanup_path.exists():
        (evidence_dir / "previous-cleanup.json").write_bytes(cleanup_path.read_bytes())
    original = httpx.AsyncHTTPTransport.handle_async_request
    dispatched = 0
    evidence = {"owner": "prep-019", "version": "7.0.2", "scenario": "STAB-019-006"}

    async def matching_owned_ids() -> list[int]:
        matches = []
        offset = 0
        expected_total = None
        for _ in range(100):
            page = await live.redmine(
                "GET",
                "issues.json",
                user="a",
                params={"project_id": project_id, "status_id": "*", "limit": 100, "offset": offset},
            )
            total = page["total_count"]
            expected_total = total if expected_total is None else expected_total
            assert total == expected_total and page["offset"] == offset
            rows = page["issues"]
            assert all(row["project"]["id"] == project_id for row in rows)
            matches.extend(row["id"] for row in rows if row["subject"] == subject)
            offset += len(rows)
            if offset == total:
                return matches
            assert rows and offset < total, "Owned inventory is incomplete"
        pytest.fail("Owned inventory exceeds reconciliation budget")

    async def replace_committed_response(transport: Any, request: Any) -> Any:
        nonlocal dispatched
        target = (
            request.method == "POST"
            and request.url.host == "127.0.0.1"
            and request.url.port == 3001
            and request.url.path == "/issues.json"
        )
        if target:
            issue = json.loads(request.content).get("issue", {})
            target = issue.get("project_id") == project_id and issue.get("subject") == subject
        response = await original(transport, request)
        if not target:
            return response
        dispatched += 1
        try:
            await response.aread()
            assert response.status_code == 201, "Owned create did not return native 201"
            created_id = response.json()["issue"]["id"]
            assert type(created_id) is int and created_id > 0, "Owned create ID is invalid"
            live.created_issues.append(created_id)
        finally:
            await response.aclose()
        return httpx.Response(500, request=request, json={"secret": "must-not-leak"})

    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(
                httpx.AsyncHTTPTransport, "handle_async_request", replace_committed_response
            )
            async with live.client(user="a", writer=True) as client:
                receipt = await client.post(
                    "/api/v1/issues", json={"project_id": project_id, "subject": subject}
                )
            assert receipt.status_code == 200
            data = receipt.json()
            assert data["outcome"] == "uncertain" and data["upstream_accepted"] is None
            assert data["resource_id"] is None and data["verification"] == "unavailable"
            assert "must-not-leak" not in receipt.text
        assert dispatched == 1 and len(live.created_issues) == 1
        created_id = live.created_issues[0]
        native = await live.redmine("GET", f"issues/{created_id}.json", user="a")
        assert native["issue"]["subject"] == subject
        assert native["issue"]["project"]["id"] == project_id
        assert await matching_owned_ids() == [created_id]
        evidence.update(
            {"dispatches": dispatched, "reconciliation": "passed", "receipt": "uncertain"}
        )
    finally:
        try:
            try:
                if dispatched and not live.created_issues:
                    matches = await matching_owned_ids()
                    assert len(matches) <= 1, (
                        "Owned create cannot be uniquely reconciled for cleanup"
                    )
                    live.created_issues.extend(matches)
            finally:
                await live.cleanup()
                evidence["cleanup"] = "passed"
        finally:
            if cleanup_path.exists():
                (evidence_dir / "cleanup.json").write_bytes(cleanup_path.read_bytes())
            (evidence_dir / "evidence.json").write_text(json.dumps(evidence, indent=2))
