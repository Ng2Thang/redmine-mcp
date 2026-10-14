"""WRT-05: exact principal, native no-ops and omitted versus empty watcher lists."""

import copy
from typing import Any

import httpx
import pytest

from tests.issue_write_helpers import invoke, override, writes

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "operation,existing",
    [
        ("add_issue_watcher", False),
        ("add_issue_watcher", True),
        ("remove_issue_watcher", False),
        ("remove_issue_watcher", True),
    ],
)
async def test_another_principal_and_noop_preserve_control_watcher(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    operation: str,
    existing: bool,
) -> None:
    control = {"id": 3, "name": "Control watcher"}
    synthetic.issues[42]["watchers"] = [control] + (
        [{"id": 8, "name": "Target"}] if existing else []
    )
    status, data = await invoke(writer_app, boundary, operation, {"issue_id": 42, "user_id": 8})
    assert status == 200 and data["outcome"] == "accepted" and data["upstream_accepted"] is True
    assert data["verification"] == "matched" and data["user_id"] == 8
    assert data["observed_present"] is (operation == "add_issue_watcher")
    observed = synthetic.issues[42]["watchers"]
    assert control in observed and sum(w["id"] == 8 for w in observed) == int(
        operation == "add_issue_watcher"
    )
    dispatched = writes(synthetic)
    assert len(dispatched) == 1
    assert dispatched[0].url.path == (
        "/issues/42/watchers.json"
        if operation == "add_issue_watcher"
        else "/issues/42/watchers/8.json"
    )
    assert dispatched[0].content == (
        b'{"watcher":{"user_id":8}}' if operation == "add_issue_watcher" else b""
    )
    assert dispatched[0].headers["X-Redmine-API-Key"] == "offline-redmine-key"


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("operation", ["add_issue_watcher", "remove_issue_watcher"])
@pytest.mark.parametrize(
    "fault", ["omitted", "empty", "duplicate", "malformed", "forbidden", "opposite"]
)
async def test_membership_verification_does_not_invent_hidden_or_noop_state(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    operation: str,
    fault: str,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response | None:
        if synthetic.writes and request.url.path == "/issues/42.json":
            if fault == "forbidden":
                return httpx.Response(403)
            issue = copy.deepcopy(synthetic.issues[42])
            if fault == "omitted":
                issue.pop("watchers")
            else:
                rows = {
                    "empty": [],
                    "duplicate": [{"id": 8, "name": "Target"}] * 2,
                    "malformed": [{"id": True, "name": "Invalid"}],
                    "opposite": []
                    if operation == "add_issue_watcher"
                    else [{"id": 8, "name": "Target"}],
                }
                issue["watchers"] = rows[fault]
            return httpx.Response(200, json={"issue": issue})
        return None

    override(synthetic, respond)
    status, data = await invoke(writer_app, boundary, operation, {"issue_id": 42, "user_id": 8})
    assert status == 200 and data["outcome"] == "accepted" and data["upstream_accepted"] is True
    if fault in {"omitted", "duplicate", "malformed", "forbidden"}:
        assert data["verification"] == "unavailable" and data["observed_present"] is None
    elif fault == "empty":
        assert data["observed_present"] is False
        assert data["verification"] == (
            "mismatch" if operation == "add_issue_watcher" else "matched"
        )
    else:
        assert data["verification"] == "mismatch"
    assert len(writes(synthetic)) == 1
