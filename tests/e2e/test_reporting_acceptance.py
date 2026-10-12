"""Owned version-selected Redmine acceptance for tasks 034 and 035 only."""

import json
from decimal import Decimal
from typing import Any

import pytest

from tests.helpers import mcp_session

pytestmark = pytest.mark.asyncio


async def test_live_estimate_list_detail_sdk_parity(live: Any) -> None:
    project = live.manifest["projects"]["reporting"]
    try:
        for number in range(8):
            created = await live.redmine(
                "POST",
                "issues.json",
                user="a",
                expected=201,
                json={
                    "issue": {
                        "project_id": project,
                        "subject": f"Reporting estimate {number}",
                        "tracker_id": live.manifest["tracker_ids"][0],
                        "estimated_hours": 12,
                        "start_date": "2026-10-01",
                        "due_date": "2026-10-31",
                    },
                },
            )
            live.created_issues.append(created["issue"]["id"])
        native = await live.redmine(
            "GET",
            "issues.json",
            user="a",
            params={
                "project_id": project,
                "subproject_id": "!*",
                "status_id": "*",
                "limit": 100,
            },
        )
        async with live.client(writer=False) as client:
            response = await client.get(
                "/api/v1/issues",
                params={
                    "project_id": project,
                    "include_subprojects": "false",
                    "status_id": "*",
                    "limit": 100,
                },
            )
            assert response.status_code == 200
            page = response.json()
            selected = {row["id"]: row for row in page["items"] if row["id"] in live.created_issues}
            assert len(selected) == 8
            assert (
                sum((Decimal(str(row["estimated_hours"])) for row in selected.values()), Decimal(0))
                == 96
            )
            upstream = {row["id"]: row for row in native["issues"]}
            for issue_id, row in selected.items():
                detail = (await client.get(f"/api/v1/issues/{issue_id}")).json()
                raw = (await live.redmine("GET", f"issues/{issue_id}.json", user="a"))["issue"]
                assert (
                    row["estimated_hours"]
                    == detail["estimated_hours"]
                    == raw["estimated_hours"]
                    == 12
                )
                assert row["estimated_hours"] == upstream[issue_id]["estimated_hours"]
                assert detail["total_estimated_hours"] == raw.get("total_estimated_hours")
        async with (
            live.application(writer=False) as app,
            mcp_session(app, live.key("a")) as session,
        ):
            result = await session.call_tool(
                "list_issues", {"project_id": project, "status_id": "*"}
            )
            assert not result.isError
            assert {row["id"] for row in json.loads(result.content[0].text)["items"]} >= set(
                selected
            )
            result = await session.call_tool("get_issue", {"issue_id": live.created_issues[0]})
            assert not result.isError
            assert json.loads(result.content[0].text)["estimated_hours"] == 12
    finally:
        await live.cleanup()


async def test_live_general_logs_filters_scope_visibility_and_sdk(live: Any) -> None:
    projects = live.manifest["projects"]
    users = live.manifest["users"]
    ids: list[int] = []
    activity = (await live.redmine("GET", "enumerations/time_entry_activities.json"))[
        "time_entry_activities"
    ][0]["id"]

    async def create(
        project: int, user: str, hours: float, day: str, issue: int | None = None
    ) -> int:
        body = {
            "project_id": project,
            "hours": hours,
            "spent_on": day,
            "activity_id": activity,
            "comments": "Task 035 owned reporting fixture",
        }
        if issue is not None:
            body["issue_id"] = issue
        result = await live.redmine(
            "POST", "time_entries.json", user=user, expected=201, json={"time_entry": body}
        )
        entry_id = result["time_entry"]["id"]
        ids.append(entry_id)
        return entry_id

    try:
        parent = await create(projects["parent"], "a", 0.1, "2026-09-01")
        child = await create(
            projects["child"], "a", 0.2, "2026-09-30", live.manifest["issues"]["child"]
        )
        await create(projects["child"], "a", 2, "2026-10-01")
        other = await create(projects["reporting"], "a", 1.25, "2026-09-15")
        own = await create(projects["reporting"], "own", 0.5, "2026-09-15")
        common = {"spent_from": "2026-09-01", "spent_to": "2026-09-30"}
        async with live.client(writer=False) as client:
            for descendants, expected in [(False, {parent}), (True, {parent, child})]:
                query = {
                    **common,
                    "project_id": projects["parent"],
                    "include_subprojects": str(descendants).lower(),
                    "limit": 1,
                }
                unique: dict[int, Any] = {}
                offset = 0
                while True:
                    response = await client.get(
                        "/api/v1/time-entries", params={**query, "offset": offset}
                    )
                    assert response.status_code == 200
                    page = response.json()
                    assert not page["pagination_policy"]["requires_narrowing"]
                    unique.update({row["id"]: row for row in page["items"]})
                    offset += page["limit"]
                    if offset >= page["total"]:
                        break
                assert set(unique) == expected
                assert unique[parent]["issue_id"] is None
                native = await live.redmine(
                    "GET",
                    "time_entries.json",
                    user="a",
                    params={
                        "project_id": projects["parent"],
                        "subproject_id": "*" if descendants else "!*",
                        "from": common["spent_from"],
                        "to": common["spent_to"],
                        "sort": "spent_on:asc",
                        "limit": 100,
                    },
                )
                assert set(unique) == {row["id"] for row in native["time_entries"]}
                if descendants:
                    assert sum(
                        (Decimal(str(row["hours"])) for row in unique.values()), Decimal(0)
                    ) == Decimal("0.3")
            combined = await client.get(
                "/api/v1/time-entries",
                params={
                    **common,
                    "project_id": projects["parent"],
                    "include_subprojects": "true",
                    "user_id": users["a"]["id"],
                    "issue_id": live.manifest["issues"]["child"],
                },
            )
            assert combined.status_code == 200
            assert [row["id"] for row in combined.json()["items"]] == [child]
            same_day = await client.get(
                "/api/v1/time-entries",
                params={
                    **common,
                    "project_id": projects["reporting"],
                },
            )
            assert same_day.status_code == 200
            assert [row["id"] for row in same_day.json()["items"]] == [other, own]
        async with live.client(user="own", writer=False) as client:
            response = await client.get(
                "/api/v1/time-entries", params={**common, "project_id": projects["reporting"]}
            )
            assert response.status_code == 200
            assert [row["id"] for row in response.json()["items"]] == [own]
            assert response.json()["visibility"]["scope"] == "requesting_redmine_user"
            native = await live.redmine(
                "GET",
                "time_entries.json",
                user="own",
                params={
                    "project_id": projects["reporting"],
                    "subproject_id": "!*",
                    "from": common["spent_from"],
                    "to": common["spent_to"],
                },
            )
            assert [row["id"] for row in native["time_entries"]] == [own]
            assert other not in {row["id"] for row in response.json()["items"]}
        async with live.client(user="b", writer=False) as client:
            response = await client.get(
                "/api/v1/time-entries", params={"project_id": projects["reporting"]}
            )
            assert response.status_code in (403, 404)
        async with (
            live.application(writer=False) as app,
            mcp_session(app, live.key("own")) as session,
        ):
            for user in [users["own"]["id"], "me"]:
                result = await session.call_tool(
                    "list_time_entries",
                    {
                        **common,
                        "project_id": projects["reporting"],
                        "user_id": user,
                    },
                )
                assert not result.isError
                assert [row["id"] for row in json.loads(result.content[0].text)["items"]] == [own]
    finally:
        for entry_id in reversed(ids):
            raw = (await live.redmine("GET", f"time_entries/{entry_id}.json"))["time_entry"]
            assert raw["project"]["id"] in projects.values()
            assert raw["comments"] == "Task 035 owned reporting fixture"
            await live.redmine("DELETE", f"time_entries/{entry_id}.json", expected=204)
