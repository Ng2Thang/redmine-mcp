"""Refuse destructive policy-stack cleanup unless both owned volumes are verified."""

import json
import subprocess
from unittest.mock import Mock

import pytest

from tools.testing.e2e_config import VERSION
from tools.testing.g05_policy import PolicyStack


def stack() -> PolicyStack:
    value = PolicyStack.__new__(PolicyStack)
    value.project = "redmine-mcp-g05-policy-7-0-2-0123456789ab"
    value.allocated = True
    return value


@pytest.mark.parametrize("volume_index", [0, 1])
@pytest.mark.parametrize(
    "label",
    [
        "com.docker.compose.project",
        "redmine-mcp.owner",
        "redmine-mcp.redmine-version",
        "redmine-mcp.environment",
    ],
)
def test_foreign_policy_volume_never_reaches_native_guard_or_down(
    monkeypatch: pytest.MonkeyPatch, volume_index: int, label: str
) -> None:
    value = stack()
    labels = {
        "com.docker.compose.project": value.project,
        "redmine-mcp.owner": "g05",
        "redmine-mcp.redmine-version": VERSION,
        "redmine-mcp.environment": "synthetic-test",
    }
    results = []
    for index in range(2):
        observed = labels | ({label: "foreign"} if index == volume_index else {})
        results.append(subprocess.CompletedProcess([], 0, json.dumps([{"Labels": observed}])))
    run = Mock(side_effect=results)
    monkeypatch.setattr(subprocess, "run", run)
    native = Mock(side_effect=AssertionError("Native execution must not be reached"))
    monkeypatch.setattr(value, "native", native)
    with pytest.raises(AssertionError, match="Refusing foreign"):
        value.cleanup()
    assert run.call_count == volume_index + 1
    assert all(call.args[0][:3] == ["docker", "volume", "inspect"] for call in run.call_args_list)
    native.assert_not_called()


def test_missing_volume_never_authorizes_policy_stack_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = Mock(return_value=subprocess.CompletedProcess([], 1, "", "unavailable"))
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(AssertionError, match="Cannot verify"):
        stack().cleanup()
    assert run.call_count == 1 and run.call_args.args[0][:3] == ["docker", "volume", "inspect"]


def test_unallocated_stack_has_no_cleanup_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    value = stack()
    value.allocated = False
    run = Mock(side_effect=AssertionError("No process should launch"))
    monkeypatch.setattr(subprocess, "run", run)
    value.cleanup()
    run.assert_not_called()


@pytest.mark.parametrize("script", ["../e2e_seed.rb", "other.rb", "e2e_seed.rb"])
def test_policy_native_script_allowlist(script: str) -> None:
    with pytest.raises(ValueError, match="Unexpected"):
        stack().native(script)


def test_existing_policy_volume_is_not_adopted_or_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    value = stack()
    value.allocated = False
    run = Mock(return_value=subprocess.CompletedProcess([], 0, "exists"))
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(AssertionError, match="pre-existing"):
        value.start()
    value.cleanup()
    assert run.call_count == 1 and not value.allocated
