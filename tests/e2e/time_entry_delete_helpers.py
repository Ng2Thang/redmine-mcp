"""TOOL-043 owned fixture helpers; credentials remain in the ignored private ledger."""

import asyncio
import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest_asyncio

from tools.testing.e2e_config import CONTAINER
from tools.testing.e2e_config import STATE as STATE

ROOT = Path(__file__).resolve().parents[2]


def fixture_command(action: str) -> dict[str, Any]:
    result = subprocess.run(
        [
            "docker",
            "exec",
            CONTAINER,
            "bundle",
            "exec",
            "rails",
            "runner",
            "/opt/testing/tool043_fixtures.rb",
            action,
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    # Setup output includes private keys; never print it, even on failure.
    assert result.returncode == 0, f"TOOL-043 owned fixture {action} failed; inspect private ledger"
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
                "subject": "TOOL-043 disposable deletion target",
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
    for comment in ("TOOL043 original", "TOOL043 control"):
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
