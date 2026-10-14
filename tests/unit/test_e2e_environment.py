"""SET-03/05: inspect ownership and refuse unsafe lifecycle operations offline."""

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests.e2e_setup_helpers import (
    SetupSandbox,
    completed,
    configuration,
    containers,
    replace,
    volume,
)
from tests.e2e_setup_helpers import (
    setup_sandbox as setup_sandbox,
)


def stub_config(module: ModuleType, monkeypatch: pytest.MonkeyPatch, data: Any) -> list[Any]:
    calls = []

    def run(command: list[str]) -> Any:
        calls.append(command)
        assert command[-3:] == ["config", "--format", "json"]
        return completed(command, data=data)

    monkeypatch.setattr(module, "run", run)
    return calls


def test_valid_compose_configuration_and_native_guard(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = setup_sandbox.environment()
    data = configuration(module)
    calls = stub_config(module, monkeypatch, data)
    assert module.compose_configuration() == data
    assert len(calls) == 1
    live = containers(module, data)
    monkeypatch.setattr(module, "validate_volumes", lambda: ["db", "files"])
    monkeypatch.setattr(module, "service_container", live.__getitem__)
    guards = []
    monkeypatch.setattr(module, "checked", lambda command, message: guards.append(command) or "")
    module.validate_running(data)
    assert len(guards) == 1 and guards[0][-1] == "/opt/testing/e2e_guard.rb"


@pytest.mark.parametrize(
    "path,value",
    [
        (("name",), "foreign"),
        *(
            (("services", "redmine", "environment", key), "foreign")
            for key in (
                "REDMINE_TEST_MARKER",
                "REDMINE_E2E_OWNER",
                "REDMINE_E2E_VERSION",
                "REDMINE_E2E_PROJECT",
            )
        ),
        (("services", "redmine", "image"), "redmine:latest"),
        (("services", "redmine", "ports", 0, "host_ip"), "0.0.0.0"),
        (("services", "redmine", "ports", 0, "published"), 3002),
        (("services", "redmine", "ports", 0, "target"), 8001),
        (("services", "postgres", "ports", 0, "host_ip"), "0.0.0.0"),
        (("services", "redmine", "volumes", 0, "read_only"), False),
        (("services", "redmine", "volumes", 0, "source"), "/foreign/scripts"),
        (("services", "redmine", "volumes", 1, "read_only"), True),
        (("services", "redmine", "volumes", 1, "type"), "volume"),
        (("services", "postgres", "volumes", 0, "source"), "foreign_db"),
        (("volumes", "redmine_files", "external"), True),
        (("volumes", "redmine_db_data", "name"), "foreign_db"),
        (("volumes", "redmine_files", "labels", "redmine-mcp.environment"), "production"),
        (("volumes", "redmine_db_data", "labels", "redmine-mcp.redmine-version"), "6.0.1"),
    ],
)
def test_compose_mismatch_never_dispatches_mutation(
    setup_sandbox: SetupSandbox,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str | int, ...],
    value: Any,
) -> None:
    module = setup_sandbox.environment()
    data = configuration(module)
    replace(data, path, value)
    calls = stub_config(module, monkeypatch, data)
    with pytest.raises(ValueError):
        module.compose_configuration()
    assert len(calls) == 1 and not module.STATE.exists()


@pytest.mark.parametrize(
    "labels",
    [
        None,
        {},
        {"com.docker.compose.project": "foreign"},
        {"redmine-mcp.environment": "production"},
        {"redmine-mcp.redmine-version": "5.1.0"},
        {"com.docker.compose.volume": "seed_state"},
    ],
)
def test_foreign_volume_is_never_accepted_even_for_reset(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, labels: Any
) -> None:
    module = setup_sandbox.environment()

    def inspect(name: str) -> Any:
        data = volume(module, name)
        data["Labels"] = labels if labels is None or not labels else data["Labels"] | labels
        return data

    monkeypatch.setattr(module, "inspect_volume", inspect)
    with pytest.raises(ValueError, match="unmarked or foreign"):
        module.validate_volumes(reset=True)


@pytest.mark.parametrize("reset", [False, True])
def test_version_migration_requires_explicit_reset(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, reset: bool
) -> None:
    module = setup_sandbox.environment()

    def inspect(name: str) -> Any:
        data = volume(module, name)
        data["Labels"]["redmine-mcp.redmine-version"] = "6.0.1"
        return data

    monkeypatch.setattr(module, "inspect_volume", inspect)
    if reset:
        assert module.validate_volumes(reset=True) == [
            module.PROJECT + "_redmine_db_data",
            module.PROJECT + "_redmine_files",
        ]
    else:
        with pytest.raises(ValueError, match="explicit --reset"):
            module.validate_volumes()


@pytest.mark.parametrize(
    "failure,expected", [("No such volume: missing", None), ("denied", "error")]
)
def test_inspect_missing_volume_is_distinct_from_docker_failure(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, failure: str, expected: Any
) -> None:
    module = setup_sandbox.environment()
    response = completed([], code=1)
    response.stderr = failure
    monkeypatch.setattr(module, "run", lambda command: response)
    if expected is None:
        assert module.inspect_volume("owned-missing") is None
    else:
        with pytest.raises(ValueError, match="Cannot inspect synthetic volumes"):
            module.inspect_volume("owned-missing")


@pytest.mark.parametrize(
    "path,value",
    [
        (("Config", "Labels", "com.docker.compose.service"), "unrelated"),
        (("Config", "Env"), ["REDMINE_TEST_MARKER=production"]),
        (("Config", "Image"), "redmine:5.1.0"),
        (("Config", "Image"), "foreign-image:7.0.2"),
        (("Mounts", 2, "Name"), "foreign-files"),
    ],
)
def test_existing_container_mismatch_refuses_lifecycle(
    setup_sandbox: SetupSandbox,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str | int, ...],
    value: Any,
) -> None:
    module = setup_sandbox.environment()
    container = containers(module, configuration(module))["redmine"]
    replace(container, path, value)
    monkeypatch.setattr(module, "project_containers", lambda: [container])
    with pytest.raises(ValueError):
        module.validate_existing_containers(reset=True)


@pytest.mark.parametrize("reset", [False, True])
def test_existing_container_version_change_requires_reset(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, reset: bool
) -> None:
    module = setup_sandbox.environment()
    container = containers(module, configuration(module))["redmine"]
    container["Config"]["Image"] = "redmine:6.0.1@sha256:" + "b" * 64
    monkeypatch.setattr(module, "project_containers", lambda: [container])
    if reset:
        module.validate_existing_containers(reset=True)
    else:
        with pytest.raises(ValueError, match="explicit --reset"):
            module.validate_existing_containers()


@pytest.mark.parametrize(
    "path,value",
    [
        (("Config", "Labels", "com.docker.compose.project"), "foreign"),
        (("Config", "Labels", "com.docker.compose.service"), "postgres"),
        (("State", "Running"), False),
        (("Config", "Image"), "redmine:7.0.2@sha256:" + "b" * 64),
        (("Config", "Env"), []),
        (("Mounts", 2, "Name"), "foreign-files"),
        (("Mounts", 0, "RW"), True),
        (("Mounts", 1, "RW"), False),
        (("Mounts", 1, "Source"), "/foreign/state"),
        (("NetworkSettings", "Ports", "3000/tcp"), [{"HostIp": "0.0.0.0", "HostPort": "8001"}]),
    ],
)
def test_running_mismatch_stops_before_native_guard(
    setup_sandbox: SetupSandbox,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str | int, ...],
    value: Any,
) -> None:
    module = setup_sandbox.environment()
    data = configuration(module)
    live = containers(module, data)
    replace(live["redmine"], path, value)
    monkeypatch.setattr(module, "validate_volumes", lambda: ["db", "files"])
    monkeypatch.setattr(module, "service_container", live.__getitem__)
    # Any unchecked native dispatch reaches the fail-closed process boundary.
    with pytest.raises(ValueError):
        module.validate_running(data)


@pytest.mark.parametrize("count", [0, 1])
def test_missing_running_volumes_refused(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, count: int
) -> None:
    module = setup_sandbox.environment()
    monkeypatch.setattr(module, "validate_volumes", lambda: ["db"][:count])
    with pytest.raises(ValueError, match="missing its marked volumes"):
        module.validate_running(configuration(module))


@pytest.mark.parametrize("fault", ["missing", "json", "kind", "owner", "version", "project"])
def test_manifest_refusals(setup_sandbox: SetupSandbox, fault: str) -> None:
    module = setup_sandbox.environment()
    module.STATE.mkdir(parents=True)
    data = {
        "kind": module.KIND,
        "owner": module.OWNER,
        "version": module.VERSION,
        "project": module.PROJECT,
    }
    if fault not in {"missing", "json"}:
        data[fault] = "foreign"
    if fault != "missing":
        (module.STATE / "fixtures.json").write_text("{" if fault == "json" else json.dumps(data))
    with pytest.raises(ValueError):
        module.manifest()


@pytest.mark.parametrize("output", ["", '{"projects":{}}\n{"projects":{}}', '{"projects":'])
def test_native_inspection_requires_one_valid_record(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, output: str
) -> None:
    module = setup_sandbox.environment()
    monkeypatch.setattr(module, "checked", lambda command, message: output)
    with pytest.raises(ValueError):
        module.native_state()


def reset_boundaries(module: ModuleType, monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    calls = []
    monkeypatch.setattr(module, "inspect_volume", lambda name: volume(module, name))
    live = containers(module, configuration(module))
    monkeypatch.setattr(module, "project_containers", lambda: list(live.values()))

    def checked(command: list[str], message: str) -> str:
        calls.append(command)
        if command[:2] == ["docker", "ps"]:
            return ""
        return ""

    monkeypatch.setattr(module, "checked", checked)
    monkeypatch.setattr(module.shutil, "rmtree", lambda path: calls.append(("rmtree", path)))
    return calls


def test_reset_selects_exact_owned_resources_and_retains_other_state(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = setup_sandbox.environment()
    module.STATE.mkdir(parents=True)
    for path in (
        module.ROOT / ".local/e2e/redmine-mcp-dev-6-0-1/control",
        module.ROOT / ".local/backups/control",
        module.ROOT / ".env",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("retained")
    calls = reset_boundaries(module, monkeypatch)
    module.reset_stack()
    mutations = [c for c in calls if isinstance(c, list) and c[1] != "ps"]
    assert mutations == [
        ["docker", "stop", "owned-redmine", "owned-postgres"],
        ["docker", "rm", "owned-redmine", "owned-postgres"],
        ["docker", "volume", "rm", module.PROJECT + "_redmine_db_data"],
        ["docker", "volume", "rm", module.PROJECT + "_redmine_files"],
    ]
    assert calls[-1] == ("rmtree", module.STATE.resolve())
    assert all(
        path.read_text() == "retained"
        for path in (
            module.ROOT / ".local/e2e/redmine-mcp-dev-6-0-1/control",
            module.ROOT / ".local/backups/control",
            module.ROOT / ".env",
        )
    )


@pytest.mark.parametrize(
    "fault", ["outside", "parent", "sibling", "symlink", "junction", "consumer"]
)
def test_reset_refusals_make_no_destructive_calls(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    module = setup_sandbox.environment()
    calls = reset_boundaries(module, monkeypatch)
    if fault in {"outside", "parent", "sibling"}:
        monkeypatch.setattr(
            module,
            "STATE",
            {
                "outside": setup_sandbox.root.parent / "outside",
                "parent": module.ROOT / ".local/e2e",
                "sibling": module.ROOT / ".local/e2e/redmine-mcp-dev-6-0-1",
            }[fault],
        )
    elif fault in {"symlink", "junction"}:
        attribute = "is_symlink" if fault == "symlink" else "is_junction"
        original = getattr(Path, attribute)
        monkeypatch.setattr(Path, attribute, lambda path: path == module.STATE or original(path))
    else:

        def consumer(command: list[str], message: str) -> str:
            calls.append(command)
            if command[1] == "ps":
                return "foreign-consumer"
            assert command == ["docker", "inspect", "foreign-consumer"]
            return json.dumps([{"Config": {"Labels": {"com.docker.compose.project": "foreign"}}}])

        monkeypatch.setattr(module, "checked", consumer)
    with pytest.raises(ValueError, match="Refusing reset|refusing reset"):
        module.reset_stack()
    assert all(isinstance(c, list) and c[1] in {"ps", "inspect"} for c in calls)


@pytest.mark.parametrize("stage", ["stop", "rm", "volume", "rmtree"])
def test_reset_failure_stops_remaining_actions(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    module = setup_sandbox.environment()
    module.STATE.mkdir(parents=True)
    calls = reset_boundaries(module, monkeypatch)
    original = module.checked

    def checked(command: list[str], message: str) -> str:
        if command[1] == stage:
            calls.append(command)
            raise ValueError("injected removal failure")
        return original(command, message)

    def rmtree(path: Path) -> None:
        calls.append(("rmtree", path))
        raise OSError("injected removal failure")

    monkeypatch.setattr(module, "checked", checked)
    if stage == "rmtree":
        monkeypatch.setattr(module.shutil, "rmtree", rmtree)
    with pytest.raises((OSError, ValueError), match="injected removal failure"):
        module.reset_stack()
    assert calls[-1][0] == "rmtree" if stage == "rmtree" else calls[-1][1] == stage
    assert module.STATE.exists()


@pytest.mark.parametrize("ids", ["", "first second", "only"])
def test_service_resolution_requires_exactly_one_container(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, ids: str
) -> None:
    module = setup_sandbox.environment()
    calls = []

    def checked(command: list[str], message: str) -> str:
        calls.append(command)
        if command[-3:] == ["ps", "--quiet", "redmine"]:
            return ids
        assert command == ["docker", "inspect", "only"]
        return json.dumps([{"Id": "only"}])

    monkeypatch.setattr(module, "checked", checked)
    if ids == "only":
        assert module.service_container("redmine") == {"Id": "only"}
        assert len(calls) == 2
    else:
        with pytest.raises(ValueError, match="missing or has multiple"):
            module.service_container("redmine")
        assert len(calls) == 1


@pytest.mark.parametrize("existing", [False, True])
def test_missing_custom_credentials_are_never_regenerated(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, existing: bool
) -> None:
    module = setup_sandbox.environment()
    env_file = module.ROOT / ".local/custom.env"
    monkeypatch.setattr(module, "ENV_FILE", env_file)
    monkeypatch.setattr(
        module, "inspect_volume", lambda name: {"owned": True} if existing else None
    )
    with pytest.raises(ValueError, match="original env file|Initialize the custom profile"):
        module.initialize_credentials()
    assert not env_file.exists()


@pytest.mark.parametrize("marker", [None, "production", "'redmine-mcp-synthetic-v1'"])
def test_custom_credentials_require_synthetic_marker_without_reading_secrets_into_errors(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, marker: str | None
) -> None:
    module = setup_sandbox.environment()
    env_file = module.ROOT / ".local/custom.env"
    env_file.parent.mkdir()
    body = "# comment\nDB_PASSWORD=private-sentinel\n"
    if marker is not None:
        body += "REDMINE_TEST_MARKER=" + marker + "\n"
    env_file.write_text(body, encoding="utf-8-sig")
    monkeypatch.setattr(module, "ENV_FILE", env_file)
    if marker == "'redmine-mcp-synthetic-v1'":
        module.initialize_credentials()
    else:
        with pytest.raises(ValueError, match="not marked as synthetic") as error:
            module.initialize_credentials()
        assert "private-sentinel" not in str(error.value)
    assert env_file.read_text(encoding="utf-8-sig") == body


def test_native_version_or_ownership_failure_aborts_running_validation(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = setup_sandbox.environment()
    data = configuration(module)
    live = containers(module, data)
    monkeypatch.setattr(module, "validate_volumes", lambda: ["db", "files"])
    monkeypatch.setattr(module, "service_container", live.__getitem__)
    calls = []

    def run(command: list[str]) -> Any:
        calls.append(command)
        assert command[-1] == "/opt/testing/e2e_guard.rb"
        result = completed(command, code=1)
        result.stderr = "private-native-version-error"
        return result

    monkeypatch.setattr(module, "run", run)
    with pytest.raises(ValueError, match="Native Redmine version/ownership check failed") as error:
        module.validate_running(data)
    assert len(calls) == 1 and "private-native" not in str(error.value)


def test_preflight_preserves_manifest_and_checks_before_native_inspection(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = setup_sandbox.environment()
    events = []
    manifest = {"owned": True}
    data = {"selected": True}

    def record(name: str, result: Any) -> Any:
        events.append(name)
        return result

    monkeypatch.setattr(module, "compose_configuration", lambda: record("configuration", data))
    monkeypatch.setattr(module, "validate_running", lambda value: record("running", value))
    monkeypatch.setattr(module, "manifest", lambda: record("manifest", manifest.copy()))
    monkeypatch.setattr(module, "native_state", lambda: record("inspection", {"projects": {}}))
    assert module.preflight() == {"owned": True, "metadata": {"projects": {}}}
    assert events == ["configuration", "running", "manifest", "inspection"]
    assert manifest == {"owned": True}


def test_empty_reset_never_invents_resources_to_remove(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = setup_sandbox.environment()
    monkeypatch.setattr(module, "inspect_volume", lambda name: None)
    monkeypatch.setattr(module, "project_containers", lambda: [])
    module.reset_stack()
    assert not module.STATE.exists()


def test_process_environment_is_forwarded_and_checked_errors_are_sanitized(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = setup_sandbox.environment()
    calls = []

    def run(command: list[str], **options: Any) -> Any:
        calls.append((command, options))
        result = completed(command, code=1)
        result.stderr = "private-tool-output"
        return result

    monkeypatch.setattr(module.subprocess, "run", run)
    with pytest.raises(ValueError, match="safe error") as error:
        module.checked(["docker", "inspect", "owned"], "safe error")
    assert "private-tool-output" not in str(error.value)
    assert calls[0][1]["cwd"] == module.ROOT
    assert calls[0][1]["env"]["REDMINE_E2E_VERSION"] == "7.0.2"
    assert calls[0][1]["env"]["REDMINE_TEST_VERSION"] == "7.0.2"
    assert calls[0][1]["env"]["MSYS2_ARG_CONV_EXCL"] == "*"
    assert calls[0][1]["capture_output"] is True and calls[0][1]["check"] is False
