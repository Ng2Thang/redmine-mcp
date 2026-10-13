"""Run one self-contained development Compose stack without host configuration files."""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = os.environ.get("REDMINE_TEST_VERSION", "7.0.2")
if VERSION not in {"7.0.2", "6.0.1"}:
    raise SystemExit("Unsupported synthetic Redmine version.")
PROJECT = f"redmine-mcp-dev-{VERSION.replace('.', '-')}"


def compose_command(*arguments: str) -> list[str]:
    return [
        "docker",
        "compose",
        "-p",
        PROJECT,
        "-f",
        str(ROOT / "deploy" / f"compose.test.{VERSION}.yaml"),
        *arguments,
    ]


def compose_environment() -> dict[str, str]:
    """Keep terminal and root dotenv settings out of the development stack."""
    environment = os.environ.copy()
    for name in list(environment):
        if name.startswith("COMPOSE_"):
            environment.pop(name)
    environment.update(
        {
            "COMPOSE_DISABLE_ENV_FILE": "1",
            "MSYS_NO_PATHCONV": "1",
            "MSYS2_ARG_CONV_EXCL": "*",
            "REDMINE_E2E_STATE": (ROOT / ".local/e2e" / PROJECT).as_posix(),
        }
    )
    return environment


def docker_output(*arguments: str) -> str:
    result = subprocess.run(
        ["docker", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise SystemExit("Cannot inspect Docker; check that Docker Desktop is running.")
    return result.stdout


def validate_volumes() -> None:
    existing = set(docker_output("volume", "ls", "--quiet").split())
    for key in ("redmine_db_data", "redmine_files"):
        name = f"{PROJECT}_{key}"
        if name not in existing:
            continue
        labels = json.loads(docker_output("volume", "inspect", name))[0].get("Labels") or {}
        if (
            labels.get("redmine-mcp.redmine-version") != VERSION
            or labels.get("redmine-mcp.environment") != "synthetic-test"
            or labels.get("com.docker.compose.project") != PROJECT
        ):
            raise SystemExit(f"Existing volume is not marked for Redmine {VERSION}: {name}")


def check_ports() -> None:
    result = subprocess.run(
        compose_command("config", "--format", "json"),
        cwd=ROOT,
        env=compose_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise SystemExit("Cannot resolve selected Compose files; Docker Compose 2.24.4+ is required.")
    services = json.loads(result.stdout)["services"]
    ids = docker_output("ps", "--quiet").split()
    containers = json.loads(docker_output("inspect", *ids)) if ids else []
    for service in ("postgres", "redmine", "mcp-server"):
        for binding in services[service].get("ports", []):
            port = int(binding["published"])
            owned = False
            for container in containers:
                labels = container["Config"].get("Labels") or {}
                for bindings in container["NetworkSettings"].get("Ports", {}).values():
                    for published in bindings or []:
                        if int(published["HostPort"]) != port:
                            continue
                        if (
                            labels.get("com.docker.compose.project") != PROJECT
                            or labels.get("com.docker.compose.service") != service
                        ):
                            raise SystemExit(
                                f"Port {port} for Redmine {VERSION} ({service}) is already used "
                                f"by container {container['Name'].lstrip('/')}. "
                                "Stop the conflicting service and retry."
                            )
                        owned = True
            if owned:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                if os.name == "nt":
                    listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                try:
                    listener.bind((binding.get("host_ip", "127.0.0.1"), port))
                except OSError:
                    raise SystemExit(
                        f"Port {port} for Redmine {VERSION} ({service}) is unavailable. "
                        "Stop the conflicting service and retry."
                    ) from None


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "preflight":
        validate_volumes()
        check_ports()
    elif action == "compose":
        raise SystemExit(
            subprocess.call(compose_command(*sys.argv[2:]), cwd=ROOT, env=compose_environment())
        )
    elif action == "assert":
        validate_volumes()
        guard = (
            "abort 'Not the synthetic environment' unless "
            "ENV['REDMINE_TEST_MARKER'] == 'redmine-mcp-synthetic-v1'; "
            "abort 'Missing synthetic seed marker' unless "
            "JSON.parse(File.read('/seed-state/environment.json'))['kind'] "
            "== 'redmine-mcp-synthetic-v1'"
        )
        raise SystemExit(
            subprocess.call(
                compose_command("exec", "-T", "redmine", "ruby", "-rjson", "-e", guard),
                cwd=ROOT,
                env=compose_environment(),
            )
        )
    else:
        raise SystemExit("Unknown action")


if __name__ == "__main__":
    try:
        main()
    except OSError:
        raise SystemExit("Cannot access Docker; check that Docker Desktop is running.") from None
    except (ValueError, KeyError):
        raise SystemExit("Invalid local synthetic configuration or Docker metadata.") from None
