"""TOOL-043 opt-in owned native deletion, permission, fault and Inspector acceptance."""

import asyncio
import json
import os
import socket
import subprocess
import sys
from typing import Any

import httpx
import pytest

from redmine_mcp.common import ApplicationError
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.write import RedmineWriter, WriteReceipt
from tests.e2e.time_entry_delete_helpers import ROOT, STATE, fixture_command, owned_pair
from tests.e2e.time_entry_delete_helpers import time_fixture as time_fixture
from tests.helpers import mcp_session

pytestmark = pytest.mark.asyncio


async def native_entries() -> dict[int, Any]:
    state = await asyncio.to_thread(fixture_command, "inspect")
    assert state["owner"] == "tool-043"
    return {row["id"]: row for row in state["entries"]}


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_native_own_and_all_delete_control_totals_and_duplicate(
    time_fixture: Any,
    boundary: str,
) -> None:
    issue_id, entry_id, control_id = await owned_pair(time_fixture)
    before = await native_entries()
    control = await time_fixture.redmine("GET", f"time_entries/{control_id}.json")
    if boundary == "rest":
        async with time_fixture.client(user="time_own", operations="delete_time_entry") as client:
            response = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{entry_id}")
        assert response.status_code == 200
        receipt = response.json()
    else:
        async with (
            time_fixture.application(operations="delete_time_entry") as app,
            mcp_session(app, time_fixture.key("time_own")) as session,
        ):
            result = await session.call_tool(
                "delete_time_entry", {"issue_id": issue_id, "time_entry_id": entry_id}
            )
        assert not result.isError
        receipt = json.loads(result.content[0].text)
    assert receipt["outcome"] == "accepted" and receipt["upstream_accepted"] is True
    assert receipt["verification"] == "not_found" and receipt["observed_present"] is False
    assert receipt["resource_id"] == entry_id and receipt["issue_id"] == issue_id
    after = await native_entries()
    assert entry_id not in after and after[control_id] == before[control_id]
    assert await time_fixture.redmine("GET", f"time_entries/{control_id}.json") == control
    assert (await time_fixture.redmine("GET", f"issues/{issue_id}.json"))["issue"][
        "spent_hours"
    ] == 1
    # Admin submitted the entry, while ordinary credited user deleted it using edit-own.
    async with time_fixture.client(user="time_own", operations="delete_time_entry") as client:
        duplicate = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{entry_id}")
    assert duplicate.status_code == 404 and await native_entries() == after
    # The other ordinary editor can remove an entry credited to the own-only user.
    async with time_fixture.client(user="time_all", operations="delete_time_entry") as client:
        response = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{control_id}")
    assert response.status_code == 200 and response.json()["outcome"] == "accepted"
    assert not await native_entries()


@pytest.mark.parametrize("user", ["time_denied", "time_no_view", "time_no_issue"])
async def test_native_denied_roles_preserve_entries(time_fixture: Any, user: str) -> None:
    issue_id, entry_id, _ = await owned_pair(time_fixture)
    before = await native_entries()
    async with time_fixture.client(user=user, operations="delete_time_entry") as client:
        response = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{entry_id}")
    assert response.status_code == 403 and await native_entries() == before


async def test_wrong_issue_other_credit_and_independent_multi_call(time_fixture: Any) -> None:
    issue_id, entry_id, control_id = await owned_pair(time_fixture)
    other = await time_fixture.redmine(
        "POST",
        "issues.json",
        expected=201,
        json={"issue": {"project_id": time_fixture.time_project, "subject": "TOOL043 other issue"}},
    )
    before = await native_entries()
    async with time_fixture.client(user="time_own", operations="delete_time_entry") as client:
        wrong = await client.delete(
            f"/api/v1/issues/{other['issue']['id']}/time-entries/{entry_id}"
        )
    assert wrong.status_code == 422 and await native_entries() == before
    await time_fixture.redmine(
        "PUT",
        f"time_entries/{control_id}.json",
        expected=204,
        json={"time_entry": {"user_id": time_fixture.manifest["users"]["time_all"]["id"]}},
    )
    async with time_fixture.client(user="time_own", operations="delete_time_entry") as client:
        accepted = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{entry_id}")
        denied = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{control_id}")
    assert accepted.status_code == 200 and accepted.json()["outcome"] == "accepted"
    assert denied.status_code == 403
    state = await native_entries()
    assert entry_id not in state and control_id in state


@pytest.mark.parametrize("fault", ["lost_reply", "readback_denied", "readback_missing", "cleanup"])
async def test_native_commit_fault_receipts_and_no_replay(
    time_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    issue_id, entry_id, control_id = await owned_pair(time_fixture)
    before = await native_entries()
    original_write, original_get = RedmineWriter.write_json, RedmineClient.get
    calls = 0

    async def receipt_fault(self: Any, *args: Any, **kwargs: Any) -> WriteReceipt:
        nonlocal calls
        calls += 1
        receipt = await original_write(self, *args, **kwargs)
        assert receipt.outcome == "accepted"
        if fault == "lost_reply":
            return WriteReceipt("uncertain", 500)
        if fault == "cleanup":
            return WriteReceipt("uncertain", 204)
        return receipt

    async def observation_fault(self: Any, path: str, *args: Any, **kwargs: Any) -> Any:
        if calls and path == f"time_entries/{entry_id}.json":
            if fault == "readback_denied":
                raise ApplicationError("access_denied", "Owned read-back denial", 403)
            if fault == "readback_missing":
                raise ApplicationError("resource_not_found", "Owned visibility observation", 404)
        return await original_get(self, path, *args, **kwargs)

    monkeypatch.setattr(RedmineWriter, "write_json", receipt_fault)
    monkeypatch.setattr(RedmineClient, "get", observation_fault)
    async with time_fixture.client(user="time_own", operations="delete_time_entry") as client:
        response = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{entry_id}")
    assert response.status_code == 200 and calls == 1
    receipt = response.json()
    assert receipt["outcome"] == ("uncertain" if fault == "lost_reply" else "accepted")
    assert receipt["upstream_accepted"] is (None if fault == "lost_reply" else True)
    assert receipt["verification"] == ("unavailable" if fault == "readback_denied" else "not_found")
    state = await native_entries()
    assert entry_id not in state and state[control_id] == before[control_id]


async def test_entry_moved_after_preflight_documents_native_race(
    time_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue_id, entry_id, control_id = await owned_pair(time_fixture)
    other = await time_fixture.redmine(
        "POST",
        "issues.json",
        expected=201,
        json={"issue": {"project_id": time_fixture.time_project, "subject": "TOOL043 race issue"}},
    )
    original = RedmineWriter.write_json
    calls = 0

    async def move_before_delete(self: Any, *args: Any, **kwargs: Any) -> WriteReceipt:
        nonlocal calls
        calls += 1
        await time_fixture.redmine(
            "PUT",
            f"time_entries/{entry_id}.json",
            expected=204,
            json={"time_entry": {"issue_id": other["issue"]["id"]}},
        )
        return await original(self, *args, **kwargs)

    monkeypatch.setattr(RedmineWriter, "write_json", move_before_delete)
    async with time_fixture.client(user="time_all", operations="delete_time_entry") as client:
        response = await client.delete(f"/api/v1/issues/{issue_id}/time-entries/{entry_id}")
    assert response.status_code == 200 and response.json()["outcome"] == "accepted"
    state = await native_entries()
    assert calls == 1 and entry_id not in state and control_id in state
    # Explicit contract limitation: no lock/If-Match guards issue linkage after preflight.


async def test_inspector_discovery_delete_and_native_state(time_fixture: Any) -> None:
    issue_id, entry_id, _ = await owned_pair(time_fixture)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    config = STATE / "tool043-inspector.json"
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
        "tests.e2e.server:create_time_entry_delete_app",
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
                    "delete_time_entry",
                    "--tool-args-json",
                    json.dumps(
                        {
                            "issue_id": issue_id,
                            "time_entry_id": entry_id,
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
                    tool for tool in payload["tools"] if tool["name"] == "delete_time_entry"
                )
                assert tool["annotations"]["destructiveHint"] is True
            else:
                assert not payload.get("isError")
                receipt = json.loads(payload["content"][0]["text"])
                assert receipt["outcome"] == "accepted" and receipt["verification"] == "not_found"
        state = await asyncio.to_thread(fixture_command, "inspect")
        assert all(row["id"] != entry_id for row in state["entries"])
    finally:
        server.terminate()
        await asyncio.wait_for(server.wait(), timeout=15)
        config.unlink(missing_ok=True)
