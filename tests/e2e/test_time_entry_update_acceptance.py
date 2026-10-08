"""TOOL-042 opt-in native state/role/fault checks on disposable pinned fixtures."""

import asyncio
import copy
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio

from redmine_mcp.common import ApplicationError
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.write import RedmineWriter, WriteReceipt
from tests.helpers import mcp_session

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".local/testing-e2e"
pytestmark = pytest.mark.asyncio


def fixture_command(action: str) -> dict[str, Any]:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "redmine-mcp-e2e-redmine-1",
            "bundle",
            "exec",
            "rails",
            "runner",
            "/opt/testing/tool042_fixtures.rb",
            action,
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    # Setup output includes private keys; never print it, even on failure.
    assert result.returncode == 0, f"TOOL-042 owned fixture {action} failed; inspect private ledger"
    return json.loads(result.stdout)


@pytest_asyncio.fixture
async def time_fixture(live: Any) -> Any:
    # live_manifest preflight has already checked image, volumes, marker and baseline ownership.
    fixture = await asyncio.to_thread(fixture_command, "setup")
    environment = copy.copy(live)
    environment.manifest = copy.deepcopy(live.manifest)
    environment.manifest["users"].update(
        {f"time_{name}": user for name, user in fixture["users"].items()}
    )
    environment.time_project = fixture["project_id"]
    environment.time_policies = fixture["policies"]
    environment.time_closed_status = fixture["closed_status_id"]
    environment.time_activities = fixture["activities"]
    try:
        yield environment
    finally:
        cleanup = await asyncio.to_thread(fixture_command, "cleanup")
        assert cleanup["cleanup"] == "passed"


async def owned_pair(environment: Any) -> tuple[int, int, int]:
    issue = await environment.redmine(
        "POST",
        "issues.json",
        expected=201,
        json={
            "issue": {
                "project_id": environment.time_project,
                "subject": "TOOL-042 disposable entry target",
            }
        },
    )
    issue_id = issue["issue"]["id"]
    activities = await environment.redmine(
        "GET",
        f"projects/{environment.time_project}.json",
        params={"include": "time_entry_activities"},
    )
    activity_id = next(
        row["id"]
        for row in activities["project"]["time_entry_activities"]
        if row["id"] != environment.time_activities["active"]
    )
    entries = []
    for comment in ("TOOL042 original", "TOOL042 control"):
        entry = await environment.redmine(
            "POST",
            "time_entries.json",
            expected=201,
            json={
                "time_entry": {
                    "issue_id": issue_id,
                    "project_id": environment.time_project,
                    "user_id": environment.manifest["users"]["time_own"]["id"],
                    "hours": 1,
                    "spent_on": "2026-10-01",
                    "activity_id": activity_id,
                    "comments": comment,
                }
            },
        )
        entries.append(entry["time_entry"]["id"])
    return issue_id, entries[0], entries[1]


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_native_update_state_control_and_own_credit(time_fixture: Any, boundary: str) -> None:
    issue_id, entry_id, control_id = await owned_pair(time_fixture)
    control = await time_fixture.redmine("GET", f"time_entries/{control_id}.json")
    payload = {
        "hours": 1.234,
        "spent_on": "2026-10-02",
        "comments": "TOOL042 corrected",
        "activity_id": time_fixture.time_activities["active"],
    }
    if boundary == "rest":
        async with time_fixture.client(user="time_own", operations="update_time_entry") as client:
            response = await client.put(
                f"/api/v1/issues/{issue_id}/time-entries/{entry_id}", json=payload
            )
        assert response.status_code == 200
        receipt = response.json()
    else:
        async with (
            time_fixture.application(operations="update_time_entry") as app,
            mcp_session(app, time_fixture.key("time_own")) as session,
        ):
            result = await session.call_tool(
                "update_time_entry", {"issue_id": issue_id, "time_entry_id": entry_id, **payload}
            )
        assert not result.isError
        receipt = json.loads(result.content[0].text)
    assert receipt["outcome"] == "accepted" and receipt["verification"] == "matched"
    native = (await time_fixture.redmine("GET", f"time_entries/{entry_id}.json"))["time_entry"]
    assert native["hours"] == 1.23 and native["spent_on"] == "2026-10-02"
    assert native["comments"] == payload["comments"]
    assert native["activity"]["id"] == payload["activity_id"]
    assert native["user"]["id"] == time_fixture.manifest["users"]["time_own"]["id"]
    assert await time_fixture.redmine("GET", f"time_entries/{control_id}.json") == control
    issue = (await time_fixture.redmine("GET", f"issues/{issue_id}.json"))["issue"]
    # Native issue totals sum stored hours; entry API hours are separately rounded for display.
    assert issue["spent_hours"] == 2.234
    # Own entry was submitted by admin, yet credited user's native own-edit grant applies.
    async with time_fixture.client(user="time_all", operations="update_time_entry") as client:
        response = await client.put(
            f"/api/v1/issues/{issue_id}/time-entries/{entry_id}", json={"comments": ""}
        )
    assert response.status_code == 200 and response.json()["verification"] == "matched"
    assert (await time_fixture.redmine("GET", f"time_entries/{entry_id}.json"))["time_entry"][
        "comments"
    ] == ""


@pytest.mark.parametrize("user", ["time_denied", "time_no_view"])
async def test_native_denial_preserves_entry(time_fixture: Any, user: str) -> None:
    issue_id, entry_id, _ = await owned_pair(time_fixture)
    before = await time_fixture.redmine("GET", f"time_entries/{entry_id}.json")
    async with time_fixture.client(user=user, operations="update_time_entry") as client:
        response = await client.put(
            f"/api/v1/issues/{issue_id}/time-entries/{entry_id}", json={"hours": 9}
        )
    assert response.status_code == 403
    assert await time_fixture.redmine("GET", f"time_entries/{entry_id}.json") == before


async def test_wrong_issue_and_other_credit_are_denied(time_fixture: Any) -> None:
    issue_id, entry_id, control_id = await owned_pair(time_fixture)
    other = await time_fixture.redmine(
        "POST",
        "issues.json",
        expected=201,
        json={"issue": {"project_id": time_fixture.time_project, "subject": "TOOL042 other issue"}},
    )
    async with time_fixture.client(user="time_own", operations="update_time_entry") as client:
        response = await client.put(
            f"/api/v1/issues/{other['issue']['id']}/time-entries/{entry_id}", json={"hours": 9}
        )
        assert response.status_code == 422
    await time_fixture.redmine(
        "PUT",
        f"time_entries/{control_id}.json",
        expected=204,
        json={"time_entry": {"user_id": time_fixture.manifest["users"]["time_all"]["id"]}},
    )
    async with time_fixture.client(user="time_own", operations="update_time_entry") as client:
        response = await client.put(
            f"/api/v1/issues/{issue_id}/time-entries/{control_id}", json={"hours": 9}
        )
        assert response.status_code == 403
        invalid = await client.put(
            f"/api/v1/issues/{issue_id}/time-entries/{entry_id}", json={"activity_id": 2147483647}
        )
        assert invalid.status_code == 422
        inactive = await client.put(
            f"/api/v1/issues/{issue_id}/time-entries/{entry_id}",
            json={"activity_id": time_fixture.time_activities["inactive"]},
        )
        assert inactive.status_code == 422


@pytest.mark.parametrize("fault", ["lost_reply", "readback_failure", "concurrent_edit"])
async def test_owned_commit_faults_are_not_retried(
    time_fixture: Any, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    issue_id, entry_id, _ = await owned_pair(time_fixture)
    original = RedmineWriter.write_json
    original_get = RedmineClient.get
    calls = 0

    async def lose_reply(self: Any, *args: Any, **kwargs: Any) -> WriteReceipt:
        nonlocal calls
        calls += 1
        accepted = await original(self, *args, **kwargs)
        assert accepted.outcome == "accepted"
        if fault == "concurrent_edit":
            await time_fixture.redmine(
                "PUT",
                f"time_entries/{entry_id}.json",
                expected=204,
                json={"time_entry": {"comments": "Concurrent edit"}},
            )
        return WriteReceipt("uncertain", 500) if fault == "lost_reply" else accepted

    async def fail_observation(self: Any, path: str, *args: Any, **kwargs: Any) -> Any:
        if fault == "readback_failure" and calls and path == f"time_entries/{entry_id}.json":
            raise ApplicationError("access_denied", "Owned injected observation denial", 403)
        return await original_get(self, path, *args, **kwargs)

    monkeypatch.setattr(RedmineWriter, "write_json", lose_reply)
    monkeypatch.setattr(RedmineClient, "get", fail_observation)
    async with time_fixture.client(user="time_own", operations="update_time_entry") as client:
        response = await client.put(
            f"/api/v1/issues/{issue_id}/time-entries/{entry_id}", json={"comments": "Lost reply"}
        )
    assert response.status_code == 200
    receipt = response.json()
    assert receipt["outcome"] == ("uncertain" if fault == "lost_reply" else "accepted")
    assert receipt["upstream_accepted"] is (None if fault == "lost_reply" else True)
    assert (
        receipt["verification"]
        == {
            "lost_reply": "matched",
            "readback_failure": "unavailable",
            "concurrent_edit": "mismatch",
        }[fault]
    )
    assert calls == 1
    native = (await time_fixture.redmine("GET", f"time_entries/{entry_id}.json"))["time_entry"]
    assert native["comments"] == ("Concurrent edit" if fault == "concurrent_edit" else "Lost reply")


async def test_native_current_settings_and_unchanged_activity(time_fixture: Any) -> None:
    issue_id, entry_id, _ = await owned_pair(time_fixture)
    route = f"/api/v1/issues/{issue_id}/time-entries/{entry_id}"
    before = (await time_fixture.redmine("GET", f"time_entries/{entry_id}.json"))["time_entry"]
    async with time_fixture.client(user="time_own", operations="update_time_entry") as client:
        response = await client.put(route, json={"comments": ""})
        assert response.status_code == (
            422 if "comments" in time_fixture.time_policies["required"] else 200
        )
        response = await client.put(route, json={"spent_on": "2099-01-01"})
        assert response.status_code == (200 if time_fixture.time_policies["future"] else 422)
        daily_max = time_fixture.time_policies["daily_max"]
        if daily_max > 0:
            response = await client.put(route, json={"hours": daily_max + 1})
            assert response.status_code == 422
        if time_fixture.time_closed_status is not None:
            await time_fixture.redmine(
                "PUT",
                f"issues/{issue_id}.json",
                expected=204,
                json={"issue": {"status_id": time_fixture.time_closed_status}},
            )
            response = await client.put(route, json={"comments": "Closed issue edit"})
            assert response.status_code == (200 if time_fixture.time_policies["closed"] else 422)
    after = (await time_fixture.redmine("GET", f"time_entries/{entry_id}.json"))["time_entry"]
    assert after["activity"] == before["activity"] and after["hours"] == before["hours"]


async def test_inspector_discovery_update_and_native_state(time_fixture: Any) -> None:
    issue_id, entry_id, _ = await owned_pair(time_fixture)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    config = STATE / "tool042-inspector.json"
    config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "owned": {
                        "type": "streamable-http",
                        "url": f"http://127.0.0.1:{port}/mcp",
                        "headers": {"X-Redmine-API-Key": time_fixture.key("time_own")},
                    }
                }
            }
        )
    )
    os.chmod(config, 0o600)
    server = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "uvicorn",
        "tests.e2e.server:create_time_entry_update_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
    )
    try:
        async with httpx.AsyncClient(trust_env=False) as client:
            for _ in range(150):
                try:
                    if (await client.get(f"http://127.0.0.1:{port}/health")).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(0.2)
            else:
                pytest.fail("Owned Inspector writer did not start")
        for method in ("tools/list", "tools/call"):
            command = [
                "npx.cmd" if os.name == "nt" else "npx",
                "--yes",
                "@modelcontextprotocol/inspector@2.8.0",
                "--cli",
                "--config",
                str(config),
                "--server",
                "owned",
                "--format",
                "json",
                "--method",
                method,
            ]
            if method == "tools/call":
                command += [
                    "--tool-name",
                    "update_time_entry",
                    "--tool-args-json",
                    json.dumps(
                        {
                            "issue_id": issue_id,
                            "time_entry_id": entry_id,
                            "comments": "TOOL042 Inspector",
                        }
                    ),
                ]
            result = await asyncio.to_thread(
                subprocess.run, command, capture_output=True, text=True, timeout=60, cwd=ROOT
            )
            assert result.returncode == 0, "Inspector failed; private credentials not printed"
            payload = json.loads(result.stdout)["result"]
            if method == "tools/list":
                tool = next(
                    tool for tool in payload["tools"] if tool["name"] == "update_time_entry"
                )
                assert tool["annotations"]["destructiveHint"] is True
            else:
                assert not payload.get("isError")
                receipt = json.loads(payload["content"][0]["text"])
                assert receipt["outcome"] == "accepted" and receipt["verification"] == "matched"
        assert (await time_fixture.redmine("GET", f"time_entries/{entry_id}.json"))["time_entry"][
            "comments"
        ] == "TOOL042 Inspector"
    finally:
        server.terminate()
        await asyncio.wait_for(server.wait(), timeout=15)
        config.unlink(missing_ok=True)
