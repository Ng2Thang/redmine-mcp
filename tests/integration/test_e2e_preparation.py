"""SET-04/06: setup orchestration and actual pytest gates with fake external boundaries."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.e2e_setup_helpers import (
    REPOSITORY,
    SetupSandbox,
    configuration,
    containers,
    volume,
)
from tests.e2e_setup_helpers import (
    setup_sandbox as setup_sandbox,
)


@pytest.mark.parametrize(
    "scenario",
    [
        "fresh",
        "reuse",
        "reset",
        "credentials",
        "configuration",
        "volumes",
        "containers",
        "manifest",
        "startup",
        "running",
        "seed",
        "incomplete_seed",
        "collision",
        "preflight",
        "reset_failure",
        "os_error",
        "malformed_json",
    ],
)
def test_preparation_order_failure_cutoffs_and_private_diagnostics(
    setup_sandbox: SetupSandbox,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    scenario: str,
) -> None:
    module = setup_sandbox.preparation()
    events = []
    reset = scenario in {"reset", "reset_failure"}
    reuse = scenario in {"reuse", "manifest"}
    if reuse:
        module.STATE.mkdir(parents=True)
        (module.STATE / "fixtures.json").write_text("owned-manifest")

    def step(name: str) -> Any:
        def perform(*args: Any, **kwargs: Any) -> Any:
            events.append((name, args, kwargs))
            if scenario not in {"fresh", "reuse", "reset"} and (
                scenario == name or scenario == "reset_failure" and name == "reset"
            ):
                raise ValueError("guard refused selected environment")
            if scenario == "os_error" and name == "configuration":
                raise OSError("private-error-must-not-leak")
            if scenario == "malformed_json" and name == "configuration":
                raise json.JSONDecodeError("private-error-must-not-leak", "private-body", 0)
            return {"owned": True}

        return perform

    for function, name in {
        "initialize_credentials": "credentials",
        "compose_configuration": "configuration",
        "validate_volumes": "volumes",
        "validate_existing_containers": "containers",
        "manifest": "manifest",
        "reset_stack": "reset",
        "validate_running": "running",
        "preflight": "preflight",
    }.items():
        monkeypatch.setattr(module, function, step(name))

    def run(command: list[str]) -> Any:
        name = "startup" if "up" in command else "seed"
        events.append((name, command, {}))
        if name == "startup":
            assert command[-7:] == [
                "up",
                "-d",
                "--wait",
                "--wait-timeout",
                "600",
                "postgres",
                "redmine",
            ]
        else:
            assert command[-1] == "/opt/testing/e2e_seed.rb"
        failed = scenario == name or name == "seed" and scenario in {"incomplete_seed", "collision"}
        return subprocess.CompletedProcess(command, int(failed), "private-output", "private-error")

    monkeypatch.setattr(module, "run", run)
    monkeypatch.setattr(sys, "argv", ["prepare-e2e.py", *(["--reset"] if reset else [])])
    if scenario in {"fresh", "reuse", "reset"}:
        module.main()
        assert "E2E ready: Redmine 7.0.2" in capsys.readouterr().out
    else:
        with pytest.raises(SystemExit) as error:
            module.main()
        for sentinel in ("private-error-must-not-leak", "private-output", "private-error"):
            assert sentinel not in str(error.value)
        assert "E2E ready" not in capsys.readouterr().out
    names = [event[0] for event in events]
    expected = ["credentials", "configuration", "volumes", "containers"]
    if reset:
        expected.append("reset")
    elif reuse:
        expected.append("manifest")
    expected += ["startup", "running", "seed", "preflight"]
    cutoff = {
        "reset_failure": "reset",
        "os_error": "configuration",
        "malformed_json": "configuration",
        "incomplete_seed": "seed",
        "collision": "seed",
    }.get(scenario, scenario)
    if scenario not in {"fresh", "reuse", "reset"} and cutoff in expected:
        expected = expected[: expected.index(cutoff) + 1]
    assert names == expected
    for name, _, options in events:
        if name in {"volumes", "containers"}:
            assert options == {"reset": reset}
    assert (module.STATE / "compose-up.log").exists() == ("startup" in names)
    assert (module.STATE / "seed.log").exists() == ("seed" in names)
    if "seed" in names:
        assert (module.STATE / "seed.log").read_text() == "private-outputprivate-error"
    if reuse:
        assert (module.STATE / "fixtures.json").read_text() == "owned-manifest"


@pytest.mark.parametrize("fault", ["none", "native_version", "manifest_owner", "native_record"])
def test_preflight_composes_real_guards_with_mocked_docker_and_native_responses(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    module = setup_sandbox.environment()
    data = configuration(module)
    live = containers(module, data)
    owned = {
        "kind": "redmine-mcp-synthetic-v1",
        "owner": "prep-018",
        "version": "7.0.2",
        "project": "redmine-mcp-dev-7-0-2",
        "issues": {"control": 42},
    }
    if fault == "manifest_owner":
        owned["owner"] = "foreign"
    module.STATE.mkdir(parents=True)
    path = module.STATE / "fixtures.json"
    original = json.dumps(owned)
    path.write_text(original)
    calls = []

    def run(command: list[str]) -> Any:
        calls.append(command)
        code = 0
        if command[-3:] == ["config", "--format", "json"]:
            output = json.dumps(data)
        elif command[:3] == ["docker", "volume", "inspect"]:
            output = json.dumps([volume(module, command[-1])])
        elif command[-3:-1] == ["ps", "--quiet"]:
            output = "owned-" + command[-1]
        elif command[:2] == ["docker", "inspect"]:
            service = command[-1].removeprefix("owned-")
            output = json.dumps([live[service]])
        elif command[-1] == "/opt/testing/e2e_guard.rb":
            code = int(fault == "native_version")
            output = "private-native-error" if code else "guard verified"
        elif command[-1] == "/opt/testing/e2e_inspect.rb":
            output = "native log noise\n" + (
                '{"projects":' if fault == "native_record" else '{"projects":{"control":7}}'
            )
        else:
            raise AssertionError("Unexpected process dispatch in offline preflight")
        return subprocess.CompletedProcess(command, code, output, "")

    monkeypatch.setattr(module, "run", run)
    if fault == "none":
        assert module.preflight() == owned | {"metadata": {"projects": {"control": 7}}}
    else:
        with pytest.raises(ValueError):
            module.preflight()
    assert path.read_text() == original
    assert not any("up" in command or "rm" in command or "stop" in command for command in calls)
    assert not any(command[-1] == "/opt/testing/e2e_seed.rb" for command in calls)
    inspected = any(command[-1] == "/opt/testing/e2e_inspect.rb" for command in calls)
    assert inspected == (fault in {"none", "native_record"})


@pytest.mark.parametrize(
    "mode,arguments,exit_code,prepares,cases",
    [
        ("success", [], 0, 0, 0),
        ("success", ["tests/e2e"], 4, 0, 0),
        ("success", ["tests/e2e", "--collect-only", "--run-e2e"], 0, 0, 0),
        ("success", ["tests/e2e", "--collect-only"], 4, 0, 0),
        ("success", ["tests/e2e", "--run-e2e", "-k", "does_not_match"], 5, 0, 0),
        ("success", ["tests/e2e", "--run-e2e"], 0, 1, 2),
        ("failure", ["tests/e2e", "--run-e2e"], 1, 1, 0),
        ("missing_uv", ["tests/e2e", "--run-e2e"], 1, 1, 0),
    ],
)
def test_real_pytest_collection_and_fixture_gates_with_fake_preparation(
    tmp_path: Path,
    mode: str,
    arguments: list[str],
    exit_code: int,
    prepares: int,
    cases: int,
) -> None:
    # Only this Python/pytest child is real. It receives copied production hooks/fixtures;
    # its preparation runner and native guard are replaced before any fixture executes.
    (tmp_path / "tests/unit").mkdir(parents=True)
    (tmp_path / "tests/e2e").mkdir()
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\ntestpaths = tests/unit\nmarkers = e2e: offline gate probe\n"
    )
    root_hooks = (REPOSITORY / "tests/conftest.py").read_text(encoding="utf-8")
    (tmp_path / "tests/conftest.py").write_text(root_hooks, encoding="utf-8")
    live_hooks = (REPOSITORY / "tests/e2e/conftest.py").read_text(encoding="utf-8")
    shim = """
from types import SimpleNamespace
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "state"
EVENTS = ROOT / "events.txt"
def event(value):
    with EVENTS.open("a", encoding="utf-8") as handle:
        handle.write(value + "\\n")
def fake_prepare(command, **kwargs):
    assert command == ["uv", "run", "--frozen", "python", "scripts/prepare-e2e.py"]
    assert kwargs["cwd"] == ROOT and kwargs["check"] is False
    assert "--reset" not in command
    event("prepare")
    if MODE == "missing_uv":
        raise OSError("private-launch-failure")
    kwargs["stdout"].write("private-preparation-output")
    return SimpleNamespace(returncode=1 if MODE == "failure" else 0)
subprocess = SimpleNamespace(run=fake_prepare, STDOUT=-2)
def fake_preflight():
    assert EVENTS.read_text().splitlines() == ["prepare"]
    event("preflight")
    return {"owned": True}
inspect_preflight = fake_preflight
def forbidden_native(*args, **kwargs):
    raise AssertionError("Real native dispatch is prohibited in the offline gate probe")
import tools.testing.e2e_environment as environment
environment.run = forbidden_native
"""
    (tmp_path / "tests/e2e/conftest.py").write_text(
        live_hooks + f"\nMODE = {mode!r}\n" + shim, encoding="utf-8"
    )
    probe = """
from pathlib import Path
def record():
    with (Path(__file__).resolve().parents[2] / "cases.txt").open("a") as handle:
        handle.write("case\\n")
def test_first(live_manifest):
    assert live_manifest == {"owned": True}
    record()
def test_second(live_manifest):
    assert live_manifest == {"owned": True}
    record()
"""
    (tmp_path / "tests/e2e/test_probe.py").write_text(probe)
    (tmp_path / "tests/unit/test_probe.py").write_text("def test_offline():\n    assert True\n")
    environment = {
        k: v
        for k, v in os.environ.items()
        if not k.upper().startswith(("REDMINE_", "COMPOSE_", "PYTEST_"))
    }
    environment.update({"PYTHONPATH": str(REPOSITORY), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *arguments],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == exit_code, output
    assert "ImportError" not in output and "NameError" not in output, output
    if exit_code == 4:
        assert "Live tests require: pytest tests/e2e --run-e2e" in output
    events_path = tmp_path / "events.txt"
    events = events_path.read_text().splitlines() if events_path.exists() else []
    assert events.count("prepare") == prepares
    case_path = tmp_path / "cases.txt"
    observed = len(case_path.read_text().splitlines()) if case_path.exists() else 0
    assert observed == cases
    if not arguments:
        assert "1 passed" in output
    if prepares and exit_code == 0:
        assert events == ["prepare", "preflight"]
    else:
        assert "preflight" not in events
    assert "private-launch-failure" not in output
    assert "private-preparation-output" not in output
    assert (tmp_path / "state/pytest-prepare.log").exists() == bool(prepares)
