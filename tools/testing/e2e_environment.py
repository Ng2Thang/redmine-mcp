"""Guarded lifecycle and inspection for the selected synthetic Compose stack."""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.testing.e2e_config import (
    ENV_FILE,
    KIND,
    OWNER,
    PORT,
    PROJECT,
    ROOT,
    STATE,
    VERSION,
    compose_command,
    native_command,
    process_environment,
    supported_version,
    validate_image,
)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=process_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def checked(command: list[str], message: str) -> str:
    result = run(command)
    if result.returncode:
        raise ValueError(message)
    return result.stdout


def inspect_volume(name: str) -> dict[str, Any] | None:
    result = run(["docker", "volume", "inspect", name])
    if result.returncode:
        if "no such volume" in result.stderr.lower():
            return None
        raise ValueError("Cannot inspect synthetic volumes; check Docker Desktop")
    return dict(json.loads(result.stdout)[0])


def initialize_credentials() -> None:
    if not ENV_FILE.exists():
        # Never initialize random passwords over a database that already exists.
        if any(inspect_volume(f"{PROJECT}_{key}") for key in ("redmine_db_data", "redmine_files")):
            raise ValueError("Existing volumes need their original env file; restore it before setup")
        if os.environ.get("REDMINE_E2E_COMPOSE_FILE"):
            raise ValueError("Initialize the custom profile's synthetic env file before E2E setup")
        result = subprocess.run(
            [sys.executable, "scripts/local_env.py", "init"],
            cwd=ROOT,
            env=process_environment() | {"REDMINE_TEST_VERSION": VERSION},
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise ValueError("Cannot initialize the selected synthetic env file")
    validate_credentials()


def validate_credentials() -> None:
    if not ENV_FILE.is_file():
        raise ValueError("Selected synthetic env file is missing; run scripts/prepare-e2e.py")
    values = dict(
        line.strip().split("=", 1)
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#") and "=" in line
    )
    if values.get("REDMINE_TEST_MARKER", "").strip("\"'") != KIND:
        raise ValueError("Selected env file is not marked as synthetic")


def same_path(value: str, expected: Path) -> bool:
    normalized = value.replace("\\", "/")
    if os.name == "nt":
        for prefix in ("/run/desktop/mnt/host/", "/host_mnt/", "/mnt/"):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                normalized = re.sub(r"^([a-zA-Z])/", r"\1:/", normalized)
                break
        normalized = re.sub(r"^/([a-zA-Z])/", r"\1:/", normalized)
    return Path(normalized).resolve() == expected.resolve()


def compose_configuration() -> dict[str, Any]:
    validate_credentials()
    data = json.loads(
        checked(
            compose_command("config", "--format", "json"),
            "Cannot resolve selected Compose configuration; check its env file and required values",
        )
    )
    services = data["services"]
    redmine = services["redmine"]
    validate_image(redmine["image"])
    environment = redmine.get("environment", {})
    if (
        data["name"] != PROJECT
        or environment.get("REDMINE_TEST_MARKER") != KIND
        or environment.get("REDMINE_E2E_OWNER") != OWNER
        or environment.get("REDMINE_E2E_VERSION") != VERSION
        or environment.get("REDMINE_E2E_PROJECT") != PROJECT
    ):
        raise ValueError("Selected Compose project or synthetic E2E markers do not match")
    ports = redmine.get("ports", [])
    if len(ports) != 1 or (
        ports[0].get("host_ip"),
        str(ports[0].get("published")),
        ports[0].get("target"),
    ) != ("127.0.0.1", str(PORT), 3000):
        raise ValueError("REDMINE_E2E_PORT must match the selected localhost Compose binding")
    for service in services.values():
        if any(port.get("host_ip") != "127.0.0.1" for port in service.get("ports", [])):
            raise ValueError("Synthetic Compose ports must bind to localhost")
    mounts = {mount["target"]: mount for mount in redmine.get("volumes", [])}
    for destination, source, readonly in (
        ("/opt/testing", ROOT / "tools/testing", True),
        ("/e2e-state", STATE, False),
    ):
        mount = mounts.get(destination, {})
        if (
            mount.get("type") != "bind"
            or not same_path(mount.get("source", ""), source)
            or bool(mount.get("read_only")) != readonly
        ):
            raise ValueError("Selected Compose profile must mount E2E scripts and private state")
    for service, destination, key in (
        ("redmine", "/usr/src/redmine/files", "redmine_files"),
        ("postgres", "/var/lib/postgresql/data", "redmine_db_data"),
    ):
        selected = next(
            (
                mount
                for mount in services[service].get("volumes", [])
                if mount["target"] == destination
            ),
            {},
        )
        definition = data.get("volumes", {}).get(key, {})
        labels = definition.get("labels", {})
        if (
            selected.get("type") != "volume"
            or selected.get("source") != key
            or definition.get("external")
            or definition.get("name") != f"{PROJECT}_{key}"
            or labels.get("redmine-mcp.environment") != "synthetic-test"
            or labels.get("redmine-mcp.redmine-version") != VERSION
        ):
            raise ValueError("Compose profile must use its own marked database/files volumes")
    return dict(data)


def validate_volumes(*, reset: bool = False) -> list[str]:
    existing = []
    for key in ("redmine_db_data", "redmine_files"):
        name = f"{PROJECT}_{key}"
        volume = inspect_volume(name)
        if volume is None:
            continue
        labels = volume.get("Labels") or {}
        version = labels.get("redmine-mcp.redmine-version", "")
        if (
            labels.get("com.docker.compose.project") != PROJECT
            or labels.get("com.docker.compose.volume") != key
            or labels.get("redmine-mcp.environment") != "synthetic-test"
            or not supported_version(version)
        ):
            raise ValueError("Refusing an unmarked or foreign synthetic volume")
        if not reset and version != VERSION:
            raise ValueError("Selected volumes belong to another version; use explicit --reset")
        existing.append(name)
    return existing


def project_containers() -> list[dict[str, Any]]:
    ids = checked(
        ["docker", "ps", "--all", "--quiet", "--filter", f"label=com.docker.compose.project={PROJECT}"],
        "Cannot inspect the selected Compose project",
    ).split()
    if not ids:
        return []
    return list(json.loads(checked(["docker", "inspect", *ids], "Cannot inspect project containers")))


def validate_existing_containers(*, reset: bool = False) -> None:
    for container in project_containers():
        config = container["Config"]
        labels = config.get("Labels") or {}
        service = labels.get("com.docker.compose.service")
        if service not in {"redmine", "postgres", "mcp-server", "mcp-writer", "seed", "backup-restore"}:
            raise ValueError("Selected Compose project contains an unexpected service")
        if service == "redmine":
            environment = dict(value.split("=", 1) for value in config.get("Env", []) if "=" in value)
            if environment.get("REDMINE_TEST_MARKER") != KIND:
                raise ValueError("Existing Redmine container is not marked as synthetic")
            match = re.match(r"redmine:([0-9]+\.[0-9]+\.[0-9]+)(?:[-@]|$)", config["Image"])
            if not match or not supported_version(match.group(1)):
                raise ValueError("Existing Redmine container is outside the supported version range")
            if not reset and match.group(1) != VERSION:
                raise ValueError("Existing Redmine version differs; use explicit --reset")
        for mount in container.get("Mounts", []):
            if mount.get("Type") == "volume" and mount.get("Name") not in {
                f"{PROJECT}_redmine_db_data",
                f"{PROJECT}_redmine_files",
            }:
                raise ValueError("Unexpected project volume; refusing lifecycle changes")


def service_container(service: str) -> dict[str, Any]:
    ids = checked(compose_command("ps", "--quiet", service), "Cannot resolve selected service").split()
    if len(ids) != 1:
        raise ValueError("Selected Compose service is missing or has multiple containers")
    output = checked(["docker", "inspect", ids[0]], "Cannot inspect selected service")
    return dict(json.loads(output)[0])


def validate_running(configuration: dict[str, Any]) -> None:
    if len(validate_volumes()) != 2:
        raise ValueError("Selected stack is missing its marked volumes")
    for service, destination, key in (
        ("redmine", "/usr/src/redmine/files", "redmine_files"),
        ("postgres", "/var/lib/postgresql/data", "redmine_db_data"),
    ):
        container = service_container(service)
        config = container["Config"]
        labels = config.get("Labels") or {}
        if (
            labels.get("com.docker.compose.project") != PROJECT
            or labels.get("com.docker.compose.service") != service
            or not container["State"].get("Running")
            or config["Image"] != configuration["services"][service]["image"]
        ):
            raise ValueError("Selected running service identity or image does not match")
        mounts = {mount["Destination"]: mount for mount in container.get("Mounts", [])}
        if mounts.get(destination, {}).get("Name") != f"{PROJECT}_{key}":
            raise ValueError("Selected service uses an unexpected database/files volume")
        if service == "redmine":
            environment = dict(value.split("=", 1) for value in config.get("Env", []) if "=" in value)
            expected_environment = {
                "REDMINE_TEST_MARKER": KIND,
                "REDMINE_E2E_OWNER": OWNER,
                "REDMINE_E2E_VERSION": VERSION,
                "REDMINE_E2E_PROJECT": PROJECT,
            }
            if any(environment.get(key) != value for key, value in expected_environment.items()):
                raise ValueError("Running Redmine E2E markers do not match")
            ports = container["NetworkSettings"]["Ports"].get("3000/tcp")
            if ports != [{"HostIp": "127.0.0.1", "HostPort": str(PORT)}]:
                raise ValueError("Running Redmine localhost port does not match")
            for destination, source, writable in (
                ("/opt/testing", ROOT / "tools/testing", False),
                ("/e2e-state", STATE, True),
            ):
                mount = mounts.get(destination, {})
                if (
                    mount.get("Type") != "bind"
                    or not same_path(mount.get("Source", ""), source)
                    or mount.get("RW") != writable
                ):
                    raise ValueError("Running Redmine E2E mounts do not match")
    checked(native_command("e2e_guard.rb"), "Native Redmine version/ownership check failed")


def manifest() -> dict[str, Any]:
    path = STATE / "fixtures.json"
    if not path.exists():
        raise ValueError("E2E fixture manifest missing; run scripts/prepare-e2e.py")
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("kind"), data.get("owner"), data.get("version"), data.get("project")) != (
        KIND,
        OWNER,
        VERSION,
        PROJECT,
    ):
        raise ValueError("E2E manifest owner/version/project mismatch; use explicit --reset")
    return dict(data)


def native_state() -> dict[str, Any]:
    output = checked(native_command("e2e_inspect.rb"), "Owned fixture inspection failed")
    records = [line for line in output.splitlines() if line.startswith('{"projects":')]
    if len(records) != 1:
        raise ValueError("Native fixture inspection did not emit one ownership record")
    return dict(json.loads(records[0]))


def preflight() -> dict[str, Any]:
    configuration = compose_configuration()
    validate_running(configuration)
    data = manifest()
    data["metadata"] = native_state()
    return data


def reset_stack() -> None:
    volumes = validate_volumes(reset=True)
    validate_existing_containers(reset=True)
    # Check consumers before removal. Never stop another project using these volumes.
    for volume in volumes:
        ids = checked(
            ["docker", "ps", "--all", "--quiet", "--filter", f"volume={volume}"],
            "Cannot inspect synthetic volume consumers",
        ).split()
        if ids:
            consumers = json.loads(
                checked(["docker", "inspect", *ids], "Cannot inspect volume consumers")
            )
            if any(
                (c["Config"].get("Labels") or {}).get("com.docker.compose.project") != PROJECT
                for c in consumers
            ):
                raise ValueError("A different project uses the selected volume; refusing reset")
    target = STATE.resolve()
    expected_parent = (ROOT / ".local/e2e").resolve()
    if (
        not target.is_relative_to(ROOT.resolve())
        or target.parent != expected_parent
        or target.name != VERSION
        or STATE.is_symlink()
        or STATE.is_junction()
    ):
        raise ValueError("Refusing reset outside the selected E2E state directory")
    # Use the inspected project containers rather than `down -v`, which can select extra volumes.
    containers = project_containers()
    if containers:
        checked(["docker", "stop", *[c["Id"] for c in containers]], "Cannot stop selected project")
        checked(["docker", "rm", *[c["Id"] for c in containers]], "Cannot remove selected containers")
    for volume in volumes:
        checked(["docker", "volume", "rm", volume], "Cannot remove selected synthetic volume")
    if target.exists():
        shutil.rmtree(target)
