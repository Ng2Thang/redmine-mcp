"""Shared built-in launcher boundaries used by E2E preparation."""

import json
from typing import Any

import pytest

from tests.e2e_setup_helpers import SetupSandbox
from tests.e2e_setup_helpers import setup_sandbox as setup_sandbox


@pytest.mark.parametrize("version", ["6.0.1", "7.0.2"])
def test_launcher_selects_only_requested_version_and_ignores_compose_overrides(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, version: str
) -> None:
    monkeypatch.setenv("REDMINE_TEST_VERSION", version)
    monkeypatch.setenv("COMPOSE_FILE", "/foreign/compose.yaml")
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "foreign")
    monkeypatch.setenv("COMPOSE_PROFILES", "writer")
    module = setup_sandbox.load("scripts/local_env.py")
    project = "redmine-mcp-dev-" + version.replace(".", "-")
    assert module.compose_command("up", "postgres", "redmine") == [
        "docker",
        "compose",
        "-p",
        project,
        "-f",
        str(setup_sandbox.root / "deploy" / f"compose.test.{version}.yaml"),
        "up",
        "postgres",
        "redmine",
    ]
    environment = module.compose_environment()
    assert environment["COMPOSE_DISABLE_ENV_FILE"] == "1"
    assert not {"COMPOSE_FILE", "COMPOSE_PROJECT_NAME", "COMPOSE_PROFILES"} & environment.keys()
    assert (
        environment["REDMINE_E2E_STATE"] == (setup_sandbox.root / ".local/e2e" / project).as_posix()
    )


@pytest.mark.parametrize("version", ["6.1.2", "latest", "7.0.3"])
def test_builtin_launcher_refuses_nonbuiltin_versions(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, version: str
) -> None:
    monkeypatch.setenv("REDMINE_TEST_VERSION", version)
    with pytest.raises(SystemExit, match="Unsupported synthetic"):
        setup_sandbox.load("scripts/local_env.py")


@pytest.mark.parametrize("fault", ["none", "project", "version", "environment"])
def test_launcher_volume_ownership(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    module = setup_sandbox.load("scripts/local_env.py")
    labels = {
        "com.docker.compose.project": module.PROJECT,
        "redmine-mcp.redmine-version": "7.0.2",
        "redmine-mcp.environment": "synthetic-test",
    }
    if fault != "none":
        key = {
            "project": "com.docker.compose.project",
            "version": "redmine-mcp.redmine-version",
            "environment": "redmine-mcp.environment",
        }[fault]
        labels[key] = "foreign"
    calls = []

    def output(*arguments: str) -> str:
        calls.append(arguments)
        if arguments == ("volume", "ls", "--quiet"):
            return module.PROJECT + "_redmine_db_data\nforeign-volume"
        assert arguments == ("volume", "inspect", module.PROJECT + "_redmine_db_data")
        return json.dumps([{"Labels": labels}])

    monkeypatch.setattr(module, "docker_output", output)
    if fault == "none":
        module.validate_volumes()
    else:
        with pytest.raises(SystemExit, match="not marked"):
            module.validate_volumes()
    assert len(calls) == 2


@pytest.mark.parametrize("owner", ["owned", "foreign", "host", "free"])
def test_port_conflicts_never_stop_other_services(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, owner: str
) -> None:
    module = setup_sandbox.load("scripts/local_env.py")
    bindings = {name: {"ports": []} for name in ("postgres", "redmine", "mcp-server")}
    bindings["redmine"]["ports"] = [{"published": 3002, "host_ip": "127.0.0.1"}]
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: type(
            "Result", (), {"returncode": 0, "stdout": json.dumps({"services": bindings})}
        )(),
    )
    containers = [
        {
            "Name": "/occupied",
            "Config": {
                "Labels": {
                    "com.docker.compose.project": module.PROJECT if owner == "owned" else "foreign",
                    "com.docker.compose.service": "redmine",
                }
            },
            "NetworkSettings": {
                "Ports": {"3000/tcp": [{"HostIp": "127.0.0.1", "HostPort": "3002"}]}
            },
        }
    ]

    def output(*arguments: str) -> str:
        if arguments == ("ps", "--quiet"):
            return "container" if owner in {"owned", "foreign"} else ""
        assert arguments == ("inspect", "container")
        return json.dumps(containers)

    monkeypatch.setattr(module, "docker_output", output)
    sockets = []

    class Listener:
        def __enter__(self) -> "Listener":
            sockets.append(self)
            return self

        def __exit__(self, *args: Any) -> None:
            pass

        def setsockopt(self, *args: Any) -> None:
            pass

        def bind(self, address: tuple[str, int]) -> None:
            assert address == ("127.0.0.1", 3002)
            if owner == "host":
                raise OSError("occupied")

    monkeypatch.setattr(module.socket, "socket", lambda *args: Listener())
    if owner in {"foreign", "host"}:
        with pytest.raises(SystemExit, match="already used|unavailable"):
            module.check_ports()
    else:
        module.check_ports()
    assert len(sockets) == int(owner in {"host", "free"})
