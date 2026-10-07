"""Prep-020 native versions, managed memberships and allowed_all on disposable projects."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS
from tests.helpers import mcp_session

pytestmark = pytest.mark.asyncio
ROOT = Path(__file__).resolve().parents[2]


def fixture_action(action: str, run: str) -> Any:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "redmine-mcp-e2e-redmine-1",
            "bundle",
            "exec",
            "rails",
            "runner",
            "/opt/testing/e2e_catalog.rb",
            action,
            run,
        ],
        capture_output=True,
        text=True,
        env=os.environ | {"MSYS_NO_PATHCONV": "1", "MSYS2_ARG_CONV_EXCL": "*"},
    )
    directory = ROOT / ".local/testing-e2e/prep-020" / run
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{action}-{uuid4().hex}.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, "Owned prep-020 fixture action failed; inspect private evidence"
    # Native issue creation can print mail-delivery notices before our JSON record.
    records = [line for line in result.stdout.splitlines() if line.startswith('{"')]
    assert len(records) == 1, "Owned fixture did not emit exactly one JSON record"
    return json.loads(records[0])


@pytest.fixture(scope="module")
def catalog_fixture(live_manifest: Any) -> Any:
    # live_manifest runs image/container/volume/version/manifest guards first.
    assert live_manifest["version"] == "7.0.2"
    run = uuid4().hex
    try:
        data = fixture_action("prepare", run)
        yield data
    finally:
        fixture_action("cleanup", run)


async def test_live_versions_fields_duplicates_no_issue_read_and_denial(
    live: Any, catalog_fixture: Any
) -> None:
    projects = catalog_fixture["projects"]
    parent = projects["parent"]
    payload = {"name": "sprint-01", "description": "prep020 original", "due_date": "2026-10-20"}
    async with live.client(operations="allowed_all") as client:
        response = await client.post(f"/api/v1/projects/{parent}/versions", json=payload)
        assert response.status_code == 200
        receipt = response.json()
        assert receipt["outcome"] == "accepted" and receipt["verification"] == "matched"
        version_id = receipt["resource_id"]
        raw = (await live.redmine("GET", f"versions/{version_id}.json", user="a"))["version"]
        assert raw["project"]["id"] == parent
        assert {k: raw[k] for k in payload} == payload
        assert raw["status"] == "open" and raw["sharing"] == "none"
        before = await live.redmine("GET", f"projects/{parent}/versions.json", user="a")
        duplicate = await client.post(
            f"/api/v1/projects/{parent}/versions", json={**payload, "description": "must not apply"}
        )
        assert duplicate.status_code == 200
        assert duplicate.json()["outcome"] == "existing"
        assert duplicate.json()["resource_id"] == version_id
        assert duplicate.json()["error"]["code"] == "version_already_exists"
        assert (await live.redmine("GET", f"versions/{version_id}.json"))["version"] == raw
        assert await live.redmine("GET", f"projects/{parent}/versions.json", user="a") == before
    async with live.client(user="b", operations="allowed_all") as client:
        denied = await client.post(f"/api/v1/projects/{parent}/versions", json={"name": "denied"})
        assert denied.status_code == 403
    assert await live.redmine("GET", f"projects/{parent}/versions.json", user="a") == before
    async with live.client(user="own", operations="allowed_all") as client:
        response = await client.post(
            f"/api/v1/projects/{projects['version_only']}/versions", json={"name": "no issue read"}
        )
        assert response.status_code == 200
        receipt = response.json()
        assert receipt["outcome"] == "accepted" and receipt["upstream_accepted"] is True
        assert receipt["verification"] == "unavailable"
        raw = (await live.redmine("GET", f"versions/{receipt['resource_id']}.json"))["version"]
        assert raw["status"] == "open" and raw["sharing"] == "none"
        assert raw["project"]["id"] == projects["version_only"]
    async with (
        live.application(operations="allowed_all") as app,
        mcp_session(app, live.key("a")) as session,
    ):
        result = await session.call_tool(
            "create_project_version", {"project_id": parent, "name": "sdk version"}
        )
        assert not result.isError and json.loads(result.content[0].text)["outcome"] == "accepted"
        tools = (await session.list_tools()).tools
        assert {tool.name for tool in tools} == set(READ_OPERATIONS) | set(WRITE_OPERATIONS)
        result = await session.call_tool("list_my_project_capabilities", {"project_id": parent})
        assert not result.isError
        capabilities = json.loads(result.content[0].text)["items"][0]
        assert {"manage_versions", "manage_members"} <= set(capabilities["permissions"])
        candidates = {row["operation_id"]: row["state"] for row in capabilities["tools"]}
        assert candidates["create_project_version"] == "conditional"
        assert candidates["add_project_members"] == "conditional"


async def test_live_membership_visibility_managed_roles_inheritance_and_assignment_effects(
    live: Any, catalog_fixture: Any
) -> None:
    projects, roles = catalog_fixture["projects"], catalog_fixture["roles"]
    parent, child = projects["parent"], projects["child"]
    target = live.manifest["users"]["own"]["id"]
    route = "/api/v1/projects/memberships/batch"

    def row(project: int, **values: Any) -> dict[str, Any]:
        return {"project_id": project, **values}

    async def members(project: int) -> list[Any]:
        return (await live.redmine("GET", f"projects/{project}/memberships.json"))["memberships"]

    async with live.client(user="own", writer=False) as client:
        native = await live.redmine(
            "GET", f"projects/{projects['public']}/memberships.json", user="own"
        )
        response = await client.get(
            "/api/v1/projects/memberships", params={"project_ids": projects["public"]}
        )
        assert response.status_code == 200 and response.json()["results"][0]["outcome"] == "read"
        assert {r["id"] for r in response.json()["results"][0]["page"]["items"]} == {
            r["id"] for r in native["memberships"]
        }
        await live.redmine("GET", f"projects/{parent}/memberships.json", user="own", expected=403)
        response = await client.get("/api/v1/projects/memberships", params={"project_ids": parent})
        assert response.json()["results"][0]["outcome"] == "rejected"
    async with live.client(operations="allowed_all") as client:
        before = await members(parent)
        mixed = await client.post(
            route,
            json={
                "items": [
                    row(parent, user_id=target, role_ids=[roles["read"]]),
                    row(live.manifest["projects"]["b"], user_id=target, role_ids=[roles["read"]]),
                ]
            },
        )
        assert mixed.status_code == 200 and mixed.json()["phase"] == "preflight_failed"
        assert await members(parent) == before
        filtered = await client.post(
            route,
            json={
                "items": [
                    row(
                        parent,
                        user_id=live.manifest["users"]["tracker"]["id"],
                        role_ids=[roles["protected"]],
                    )
                ]
            },
        )
        assert (
            filtered.status_code == 200 and filtered.json()["results"][0]["outcome"] == "rejected"
        )
        assert await members(parent) == before
        added = await client.post(
            route, json={"items": [row(parent, user_id=target, role_ids=[roles["read"]])]}
        )
        assert added.status_code == 200
        receipt = added.json()["results"][0]
        assert receipt["outcome"] == "accepted" and receipt["verification"] == "matched"
        member_id = receipt["membership_id"]
        descendants = await members(child)
        inherited = next(r for r in descendants if r.get("user", {}).get("id") == target)
        assert all(r["inherited"] for r in inherited["roles"])
        rejected = await client.request(
            "DELETE", route, json={"items": [row(child, membership_id=inherited["id"])]}
        )
        assert rejected.json()["phase"] == "preflight_failed"
        assert rejected.json()["results"][0]["outcome"] == "rejected"
        group = next(r for r in await members(parent) if "group" in r)
        rejected = await client.request(
            "DELETE", route, json={"items": [row(parent, membership_id=group["id"])]}
        )
        assert rejected.json()["phase"] == "preflight_failed"
        protected = next(
            r
            for r in await members(parent)
            if r.get("user", {}).get("id") == live.manifest["users"]["notes"]["id"]
        )
        updated = await client.put(
            route,
            json={"items": [row(parent, membership_id=protected["id"], role_ids=[roles["other"]])]},
        )
        receipt = updated.json()["results"][0]
        assert receipt["outcome"] == "accepted" and receipt["verification"] == "mismatch"
        assert {r["id"] for r in receipt["observed_membership"]["roles"]} == {
            roles["protected"],
            roles["other"],
        }
        rejected = await client.request(
            "DELETE", route, json={"items": [row(parent, membership_id=protected["id"])]}
        )
        assert rejected.json()["results"][0]["outcome"] == "rejected"
        assert any(r["id"] == protected["id"] for r in await members(parent))
        assignment = fixture_action("assign", catalog_fixture["run"])
        observed = fixture_action("inspect", catalog_fixture["run"])
        assert observed["projects"]["parent"]["default_assigned_to_id"] == target
        assert (
            observed["category_assigned_to_id"] == target
            and observed["issue_assigned_to_id"] == target
        )
    async with (
        live.application(operations="allowed_all") as app,
        mcp_session(app, live.key("a")) as session,
    ):
        result = await session.call_tool(
            "update_project_members",
            {"items": [row(parent, membership_id=member_id, role_ids=[roles["other"]])]},
        )
        assert not result.isError
        assert json.loads(result.content[0].text)["results"][0]["verification"] == "matched"
        inherited = next(r for r in await members(child) if r.get("user", {}).get("id") == target)
        assert {r["id"] for r in inherited["roles"]} == {roles["other"]}
        result = await session.call_tool("list_project_members", {"project_ids": [parent, child]})
        assert not result.isError and all(
            r["outcome"] == "read" for r in json.loads(result.content[0].text)["results"]
        )
        result = await session.call_tool(
            "delete_project_members", {"items": [row(parent, membership_id=member_id)]}
        )
        assert not result.isError
        assert json.loads(result.content[0].text)["results"][0]["verification"] == "matched"
        assert not any(r.get("user", {}).get("id") == target for r in await members(child))
        # Re-add through SDK, then delete through REST to cover both mutation boundaries.
        result = await session.call_tool(
            "add_project_members",
            {"items": [row(parent, user_id=target, role_ids=[roles["read"]])]},
        )
        assert not result.isError
        new_id = json.loads(result.content[0].text)["results"][0]["membership_id"]
    observed = fixture_action("inspect", catalog_fixture["run"])
    assert observed["projects"]["parent"]["default_assigned_to_id"] is None
    assert observed["category_assigned_to_id"] is None
    assert observed["issue_assigned_to_id"] == target
    assert (await live.redmine("GET", f"issues/{assignment['issue_id']}.json"))["issue"][
        "assigned_to"
    ]["id"] == target
    async with live.client(operations="allowed_all") as client:
        response = await client.request(
            "DELETE", route, json={"items": [row(parent, membership_id=new_id)]}
        )
        assert response.json()["results"][0]["verification"] == "matched"


async def test_live_allowed_all_inspector_catalog_and_native_parity(catalog_fixture: Any) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/verify-catalog-inspector.py", catalog_fixture["run"]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    directory = ROOT / ".local/testing-e2e/prep-020" / catalog_fixture["run"]
    (directory / "inspector-run.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, "Owned Inspector check failed; inspect private evidence"


async def test_live_historical_read_variants_with_populated_owned_state(
    live: Any, catalog_fixture: Any
) -> None:
    projects = catalog_fixture["projects"]
    parent, child = projects["parent"], projects["child"]
    private = json.loads(
        (ROOT / ".local/testing-e2e/prep-020" / catalog_fixture["run"] / "fixture.json").read_text()
    )
    issue_id, category_id = private["issue_id"], private["category_id"]
    versions = (await live.redmine("GET", f"projects/{parent}/versions.json"))["versions"]
    version_id = versions[0]["id"]
    await live.redmine(
        "PUT",
        f"versions/{version_id}.json",
        expected=204,
        json={"version": {"sharing": "descendants"}},
    )
    await live.redmine(
        "PUT",
        f"issues/{issue_id}.json",
        expected=204,
        json={
            "issue": {
                "category_id": category_id,
                "fixed_version_id": version_id,
                "start_date": "2026-09-01",
                "due_date": "2026-09-30",
            }
        },
    )
    created = await live.redmine(
        "POST",
        "issues.json",
        expected=201,
        json={
            "issue": {
                "project_id": child,
                "subject": "Prep020 descendant",
                "fixed_version_id": version_id,
                "tracker_id": live.manifest["tracker_ids"][0],
                "start_date": "2026-09-01",
                "due_date": "2026-09-30",
            }
        },
    )
    child_id = created["issue"]["id"]
    activity = (await live.redmine("GET", "enumerations/time_entry_activities.json"))[
        "time_entry_activities"
    ][0]["id"]
    for selected, hours in [(issue_id, 1.25), (child_id, 2.5)]:
        await live.redmine(
            "POST",
            "time_entries.json",
            user="a",
            expected=201,
            json={
                "time_entry": {
                    "issue_id": selected,
                    "hours": hours,
                    "spent_on": "2026-09-15",
                    "activity_id": activity,
                    "comments": "Prep020 disposable aggregate",
                }
            },
        )
    async with live.client(writer=False) as client:
        for path, kind in [
            (f"projects/{parent}/versions.json", "versions"),
            (f"projects/{child}/versions.json", "versions"),
            (f"projects/{parent}/issue_categories.json", "issue_categories"),
        ]:
            raw = await live.redmine("GET", path, user="a")
            response = await client.get(
                "/api/v1/"
                + path.removesuffix(".json").replace("issue_categories", "issue-categories")
            )
            assert response.status_code == 200
            assert {r["id"] for r in response.json()["items"]} == {r["id"] for r in raw[kind]}
        category = await client.get(
            "/api/v1/issues",
            params={"project_id": parent, "category_id": category_id, "status_id": "*"},
        )
        assert category.status_code == 200 and {r["id"] for r in category.json()["items"]} == {
            issue_id
        }
        for descendants, expected in [(False, {issue_id}), (True, {issue_id, child_id})]:
            query = {
                "project_id": parent,
                "fixed_version_id": version_id,
                "status_id": "*",
                "include_subprojects": str(descendants).lower(),
            }
            response = await client.get("/api/v1/issues", params=query)
            assert (
                response.status_code == 200
                and {r["id"] for r in response.json()["items"]} == expected
            )
            assert sum(r["spent_hours"] for r in response.json()["items"]) == (
                1.25 if not descendants else 3.75
            )
            native = await live.redmine(
                "GET",
                "issues.json",
                user="a",
                params={
                    "project_id": parent,
                    "fixed_version_id": version_id,
                    "subproject_id": "*" if descendants else "!*",
                    "status_id": "*",
                },
            )
            assert {r["id"] for r in native["issues"]} == expected
        detail = await client.get(
            f"/api/v1/issues/{issue_id}", params={"include": "allowed_statuses"}
        )
        native = (
            await live.redmine(
                "GET", f"issues/{issue_id}.json", user="a", params={"include": "allowed_statuses"}
            )
        )["issue"]
        assert native["allowed_statuses"], (
            "Owned workflow lacks the required nonempty transition fixture"
        )
        assert (
            detail.status_code == 200
            and detail.json()["allowed_statuses"] == native["allowed_statuses"]
        )
        for endpoint, key in [
            ("issue_statuses", "issue_statuses"),
            ("trackers", "trackers"),
            ("enumerations/issue_priorities", "issue_priorities"),
        ]:
            native = await live.redmine("GET", endpoint + ".json", user="a")
            public = {
                "issue_statuses": "/api/v1/issue-statuses",
                "trackers": "/api/v1/trackers",
                "enumerations/issue_priorities": "/api/v1/issue-priorities",
            }[endpoint]
            response = await client.get(public)
            assert response.status_code == 200
            assert {(r["id"], r["name"]) for r in response.json()["items"]} == {
                (r["id"], r["name"]) for r in native[key]
            }
        project = await live.redmine(
            "GET", f"projects/{parent}.json", user="a", params={"include": "trackers"}
        )
        assert {r["id"] for r in project["project"]["trackers"]} == set(
            live.manifest["tracker_ids"]
        )
        entries = await client.get(f"/api/v1/issues/{issue_id}/time-entries")
        native = await live.redmine(
            "GET", "time_entries.json", user="a", params={"issue_id": issue_id}
        )
        assert entries.status_code == 200 and {r["id"] for r in entries.json()["items"]} == {
            r["id"] for r in native["time_entries"]
        }
    for user in ("a", "b"):
        async with live.client(user=user, writer=False) as client:
            response = await client.get("/api/v1/users/current")
            native = (
                await live.redmine(
                    "GET", "users/current.json", user=user, params={"include": "memberships"}
                )
            )["user"]
            assert response.status_code == 200 and response.json()["id"] == native["id"]
            assert response.json()["login"] == native["login"]
    async with live.client(user="own", writer=False) as client:
        response = await client.get(f"/api/v1/projects/{parent}/versions")
        assert response.status_code in (403, 404)
