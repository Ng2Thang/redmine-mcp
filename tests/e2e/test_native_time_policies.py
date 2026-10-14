"""G05 NAT-02: native policies changed only in a fresh disposable two-service stack."""

import asyncio
import json
from datetime import date, timedelta
from fractions import Fraction
from typing import Any

import pytest
import pytest_asyncio

from tests.e2e.g05_helpers import VariantEnvironment, fixture_command
from tests.e2e.test_native_variants import (
    test_inverse_cross_project_relations_and_unchanged_control as verify_inverse_relation,
)
from tests.helpers import mcp_session
from tools.testing.g05_policy import PolicyStack

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def policy_environment(live_manifest: Any) -> Any:
    stack = PolicyStack()
    try:
        await asyncio.to_thread(stack.start)
        data = await asyncio.to_thread(
            fixture_command, "setup", command=stack.native, state=stack.state
        )
        environment = VariantEnvironment(data, stack.url)
        environment.stack = stack
        try:
            yield environment
        finally:
            result = await asyncio.to_thread(
                fixture_command, "cleanup", command=stack.native, state=stack.state
            )
            assert result["cleanup"] == "passed"
    finally:
        await asyncio.to_thread(stack.cleanup)


async def write_time(
    env: Any, boundary: str, issue: int, payload: dict[str, Any], entry: int | None = None
) -> tuple[bool, dict[str, Any]]:
    if boundary == "mcp":
        async with env.application() as app, mcp_session(app, env.key("writer")) as session:
            arguments = {"issue_id": issue, **payload}
            if entry is not None:
                arguments["time_entry_id"] = entry
            result = await session.call_tool(
                "create_time_entry" if entry is None else "update_time_entry", arguments
            )
        return bool(result.isError), {} if result.isError else json.loads(result.content[0].text)
    async with env.client(user="writer") as client:
        path = f"/api/v1/issues/{issue}/time-entries"
        response = await client.request(
            "POST" if entry is None else "PUT",
            path if entry is None else f"{path}/{entry}",
            json=payload,
        )
    return response.status_code != 200, response.json()


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "relation_type,canonical",
    [
        ("duplicated", "duplicates"),
        ("blocked", "blocks"),
        ("follows", "precedes"),
        ("copied_from", "copied_to"),
    ],
)
async def test_enabled_cross_project_inverse_relations(
    policy_environment: Any, boundary: str, relation_type: str, canonical: str
) -> None:
    env = policy_environment
    await asyncio.to_thread(
        env.stack.run,
        env.stack.native("g05_policy.rb", "allow"),
        f"cross-project-{relation_type}-{boundary}",
    )
    previous = env.data["policies"]["cross_project"]
    env.data["policies"]["cross_project"] = True
    try:
        await verify_inverse_relation(env, boundary, relation_type, canonical, True)
    finally:
        env.data["policies"]["cross_project"] = previous


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("restricted", [False, True])
async def test_native_create_update_policy_matrix(
    policy_environment: Any, boundary: str, restricted: bool
) -> None:
    env = policy_environment
    stack, data = env.stack, env.data
    action = "restrict" if restricted else "allow"
    await asyncio.to_thread(
        stack.run, stack.native("g05_policy.rb", action), f"{action}-{boundary}"
    )
    issue = data["issues"]["a"]
    today = data["today"]
    valid = {
        "hours": 1,
        "spent_on": today,
        "comments": "G05 valid",
        "activity_id": data["activities"]["active"],
    }
    control = (
        await env.redmine(
            "POST",
            "time_entries.json",
            user="writer",
            expected=201,
            params={"project_id": data["projects"]["parent"]},
            json={"time_entry": {"issue_id": issue, **valid}},
        )
    )["time_entry"]
    before_control = await env.redmine("GET", f"time_entries/{control['id']}.json")
    cases = [
        ("required_comments", issue, {**valid, "comments": ""}, not restricted),
        (
            "future_date",
            issue,
            {**valid, "spent_on": (date.fromisoformat(today) + timedelta(days=2)).isoformat()},
            not restricted,
        ),
        (
            "closed_issue",
            data["issues"]["closed"],
            valid,
            not restricted or not data["policies"]["closed_supported"],
        ),
        (
            "disabled_activity",
            issue,
            {**valid, "activity_id": data["activities"]["inactive"]},
            False,
        ),
        ("explicit_activity", issue, valid, True),
        ("default_activity", issue, {k: v for k, v in valid.items() if k != "activity_id"}, True),
        ("minute_rounding", issue, {**valid, "hours": 1.234}, True),
    ]
    evidence = []
    for name, selected_issue, payload, accepted in cases:
        native = await env.redmine(
            "POST",
            "time_entries.json",
            user="writer",
            expected=201 if accepted else 422,
            params={"project_id": data["projects"]["parent"]},
            json={"time_entry": {"issue_id": selected_issue, **payload}},
        )
        failed, receipt = await write_time(env, boundary, selected_issue, payload)
        assert failed is not accepted, f"Create policy parity: {name}"
        if accepted:
            assert receipt["outcome"] == "accepted" and receipt["verification"] == "matched"
            observed = (await env.redmine("GET", f"time_entries/{receipt['resource_id']}.json"))[
                "time_entry"
            ]
            for field in ("hours", "spent_on", "comments", "activity"):
                assert observed[field] == native["time_entry"][field]
            if name == "minute_rounding":
                expected_hours = (
                    Fraction(74, 60) if isinstance(observed["hours"], str) else Fraction("1.23")
                )
                assert Fraction(str(observed["hours"])) == expected_hours
        # Updates use a fresh valid entry; compare the same caller's native policy result.
        baseline = (
            await env.redmine(
                "POST",
                "time_entries.json",
                user="writer",
                expected=201,
                params={"project_id": data["projects"]["parent"]},
                json={"time_entry": {"issue_id": selected_issue if accepted else issue, **valid}},
            )
        )["time_entry"]
        update = {k: v for k, v in payload.items() if k != "spent_on" or name == "future_date"}
        native_issue = selected_issue if accepted else issue
        update_accepted = accepted or name == "closed_issue"
        # Closing policy is checked against an entry already attached to a closed issue.
        if name == "closed_issue" and restricted and data["policies"]["closed_supported"]:
            # Create under permissive settings, then reinstate restriction before either update.
            await asyncio.to_thread(
                stack.run, stack.native("g05_policy.rb", "allow"), f"closed-allow-{boundary}"
            )
            baseline = (
                await env.redmine(
                    "POST",
                    "time_entries.json",
                    user="writer",
                    expected=201,
                    params={"project_id": data["projects"]["parent"]},
                    json={"time_entry": {"issue_id": selected_issue, **valid}},
                )
            )["time_entry"]
            await asyncio.to_thread(
                stack.run, stack.native("g05_policy.rb", "restrict"), f"closed-restrict-{boundary}"
            )
            native_issue = selected_issue
            update_accepted = False
        before = await env.redmine("GET", f"time_entries/{baseline['id']}.json")
        await env.redmine(
            "PUT",
            f"time_entries/{baseline['id']}.json",
            user="writer",
            expected=204 if update_accepted else 422,
            json={"time_entry": update},
        )
        # Restore changed fields before exercising the MCP/REST update on the same entry.
        if update_accepted:
            await env.redmine(
                "PUT",
                f"time_entries/{baseline['id']}.json",
                user="writer",
                expected=204,
                json={"time_entry": valid},
            )
        failed, receipt = await write_time(env, boundary, native_issue, update, baseline["id"])
        assert failed is not update_accepted, f"Update policy parity: {name}"
        after = await env.redmine("GET", f"time_entries/{baseline['id']}.json")
        if update_accepted:
            assert receipt["outcome"] == "accepted" and receipt["verification"] == "matched"
        else:
            assert after == before
        evidence.append(
            {"case": name, "create_accepted": accepted, "update_accepted": update_accepted}
        )
    assert await env.redmine("GET", f"time_entries/{control['id']}.json") == before_control
    (stack.state / f"matrix-{action}-{boundary}.json").write_text(
        json.dumps(
            {
                "owner": "g05",
                "version": data["version"],
                "project": stack.project,
                "restricted": restricted,
                "boundary": boundary,
                "native_parity": evidence,
                "control_unchanged": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
