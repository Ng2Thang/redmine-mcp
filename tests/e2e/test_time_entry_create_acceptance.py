"""Opt-in creation and activity checks using only owned time-project resources."""

import json
from fractions import Fraction
from typing import Any

import pytest

from redmine_mcp.common import ApplicationError
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.write import RedmineWriter, WriteReceipt
from tests.e2e.test_time_entry_update_acceptance import time_fixture as time_fixture
from tests.helpers import mcp_session

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def owned_issue(environment: Any) -> int:
    result = await environment.redmine(
        "POST",
        "issues.json",
        expected=201,
        json={"issue": {"project_id": environment.time_project, "subject": "TOOL-041 test target"}},
    )
    # The imported fixture owns the whole disposable project and removes its issues/entries.
    return result["issue"]["id"]


async def create(
    environment: Any,
    issue_id: int,
    boundary: str,
    payload: dict[str, Any],
    *,
    user: str = "time_own",
) -> tuple[bool, dict[str, Any]]:
    if boundary == "mcp":
        async with (
            environment.application(operations="create_time_entry") as app,
            mcp_session(app, environment.key(user)) as session,
        ):
            result = await session.call_tool("create_time_entry", {"issue_id": issue_id, **payload})
        return bool(result.isError), {} if result.isError else json.loads(result.content[0].text)
    async with environment.client(user=user, operations="create_time_entry") as client:
        response = await client.post(f"/api/v1/issues/{issue_id}/time-entries", json=payload)
    return response.status_code != 200, response.json()


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_two_owned_issues_record_sixteen_caller_hours(
    time_fixture: Any, boundary: str
) -> None:
    issues = [await owned_issue(time_fixture) for _ in range(2)]
    entries = []
    for issue, spent_on in zip(issues, ("2026-10-01", "2026-10-02"), strict=True):
        failed, receipt = await create(
            time_fixture,
            issue,
            boundary,
            {
                "hours": 8,
                "spent_on": spent_on,
                "activity_id": time_fixture.time_activities["active"],
                "comments": "TOOL041 eight hours",
            },
        )
        assert not failed
        assert receipt["outcome"] == "accepted" and receipt["upstream_accepted"] is True
        assert receipt["verification"] == "matched"
        entry_id = receipt["resource_id"]
        entries.append(entry_id)
        native = (await time_fixture.redmine("GET", f"time_entries/{entry_id}.json"))["time_entry"]
        assert (
            native["issue"]["id"] == issue and native["project"]["id"] == time_fixture.time_project
        )
        assert native["user"]["id"] == time_fixture.manifest["users"]["time_own"]["id"]
        assert Fraction(str(native["hours"])) == 8 and native["spent_on"] == spent_on
        issue_native = (await time_fixture.redmine("GET", f"issues/{issue}.json"))["issue"]
        assert issue_native["spent_hours"] == 8
    assert len(set(entries)) == 2
    async with (
        time_fixture.application(writer=False) as app,
        mcp_session(app, time_fixture.key("time_own")) as session,
    ):
        result = await session.call_tool(
            "list_time_entries", {"project_id": time_fixture.time_project, "user_id": "me"}
        )
    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["total"] == 2 and {row["id"] for row in data["items"]} == set(entries)
    assert sum(Fraction(str(row["hours"])) for row in data["items"]) == 16


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_duplicate_requests_are_distinct_native_entries(
    time_fixture: Any, boundary: str
) -> None:
    issue = await owned_issue(time_fixture)
    payload = {
        "hours": 1,
        "spent_on": "2026-10-01",
        "comments": "TOOL041 duplicate",
        "activity_id": time_fixture.time_activities["active"],
    }
    first = await create(time_fixture, issue, boundary, payload)
    second = await create(time_fixture, issue, boundary, payload)
    assert not first[0] and not second[0]
    assert first[1]["resource_id"] != second[1]["resource_id"]
    native = await time_fixture.redmine("GET", "time_entries.json", params={"issue_id": issue})
    assert native["total_count"] == 2
    assert {row["id"] for row in native["time_entries"]} == {
        first[1]["resource_id"],
        second[1]["resource_id"],
    }


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_read_only_time_role_cannot_create(time_fixture: Any, boundary: str) -> None:
    issue = await owned_issue(time_fixture)
    failed, _ = await create(
        time_fixture,
        issue,
        boundary,
        {"hours": 1, "spent_on": "2026-10-01", "comments": "TOOL041 denied"},
        user="time_read_only",
    )
    assert failed
    native = await time_fixture.redmine("GET", "time_entries.json", params={"issue_id": issue})
    assert native["total_count"] == 0


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_log_without_time_view_preserves_acceptance(time_fixture: Any, boundary: str) -> None:
    issue = await owned_issue(time_fixture)
    failed, receipt = await create(
        time_fixture,
        issue,
        boundary,
        {
            "hours": 1,
            "spent_on": "2026-10-01",
            "comments": "TOOL041 no time view",
            "activity_id": time_fixture.time_activities["active"],
        },
        user="time_no_view",
    )
    assert not failed
    assert receipt["outcome"] == "accepted" and receipt["upstream_accepted"] is True
    assert receipt["verification"] == "unavailable"
    native = (await time_fixture.redmine("GET", f"time_entries/{receipt['resource_id']}.json"))[
        "time_entry"
    ]
    assert native["user"]["id"] == time_fixture.manifest["users"]["time_no_view"]["id"]


@pytest.mark.parametrize("user", ["time_own", "time_no_view"])
async def test_activity_expansion_follows_native_time_visibility(
    time_fixture: Any, user: str
) -> None:
    async with time_fixture.client(user=user, writer=False) as client:
        response = await client.get(
            f"/api/v1/projects/{time_fixture.time_project}/time-entry-activities"
        )
    assert response.status_code == 200
    native = await time_fixture.redmine(
        "GET",
        f"projects/{time_fixture.time_project}.json",
        user=user,
        params={"include": "time_entry_activities"},
    )
    choices = native["project"].get("time_entry_activities")
    data = response.json()
    if choices is None:
        assert data["items"] == []
        assert {"path": "/items", "state": "not_returned"} in data["visibility"]["observations"]
    else:
        assert {row["id"] for row in data["items"]} == {row["id"] for row in choices}
        assert time_fixture.time_activities["active"] in {row["id"] for row in data["items"]}
        assert time_fixture.time_activities["inactive"] not in {row["id"] for row in data["items"]}


@pytest.mark.parametrize("activity", ["inactive", "unknown"])
async def test_native_activity_rejection_creates_no_entry(time_fixture: Any, activity: str) -> None:
    issue = await owned_issue(time_fixture)
    activity_id = 2147483647 if activity == "unknown" else time_fixture.time_activities[activity]
    async with time_fixture.client(user="time_own", operations="create_time_entry") as client:
        response = await client.post(
            f"/api/v1/issues/{issue}/time-entries",
            json={
                "hours": 1,
                "spent_on": "2026-10-01",
                "activity_id": activity_id,
                "comments": "TOOL041 invalid activity",
            },
        )
    assert response.status_code == 422
    native = await time_fixture.redmine("GET", "time_entries.json", params={"issue_id": issue})
    assert native["total_count"] == 0


@pytest.mark.parametrize("fault", ["lost_reply", "500", "readback_forbidden"])
async def test_native_commit_with_injected_receipt_fault_is_never_retried(
    time_fixture: Any, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    issue = await owned_issue(time_fixture)
    original, original_get = RedmineWriter.write_json, RedmineClient.get
    calls = 0

    async def write(self: Any, *args: Any, **kwargs: Any) -> WriteReceipt:
        nonlocal calls
        calls += 1
        receipt = await original(self, *args, **kwargs)
        assert receipt.outcome == "accepted"
        if fault == "lost_reply":
            return WriteReceipt("uncertain")
        return WriteReceipt("uncertain", 500) if fault == "500" else receipt

    async def get(self: Any, path: str, *args: Any, **kwargs: Any) -> Any:
        if fault == "readback_forbidden" and calls and path.startswith("time_entries/"):
            raise ApplicationError("access_denied", "Owned observation fault", 403)
        return await original_get(self, path, *args, **kwargs)

    monkeypatch.setattr(RedmineWriter, "write_json", write)
    monkeypatch.setattr(RedmineClient, "get", get)
    failed, receipt = await create(
        time_fixture,
        issue,
        "mcp",
        {
            "hours": 1,
            "spent_on": "2026-10-01",
            "comments": "TOOL041 fault",
            "activity_id": time_fixture.time_activities["active"],
        },
    )
    assert not failed and calls == 1
    accepted = fault == "readback_forbidden"
    assert receipt["outcome"] == ("accepted" if accepted else "uncertain")
    assert receipt["upstream_accepted"] is (True if accepted else None)
    assert receipt["verification"] == "unavailable"
    assert (receipt["resource_id"] is not None) is accepted
    native = await time_fixture.redmine("GET", "time_entries.json", params={"issue_id": issue})
    assert native["total_count"] == 1 and native["time_entries"][0]["comments"] == "TOOL041 fault"
