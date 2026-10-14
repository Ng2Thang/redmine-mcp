"""Temporary repositories and fail-closed boundaries for offline E2E setup tests."""

import json
import shutil
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPOSITORY = Path(__file__).resolve().parents[1]


class SetupSandbox:
    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.root = root
        self.monkeypatch = monkeypatch
        self.loads = 0
        for version in ("6.0.1", "7.0.2"):
            path = root / "deploy" / f"compose.test.{version}.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Offline placeholder; Docker must never read this file.\n")

    def load(self, relative: str) -> ModuleType:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text((REPOSITORY / relative).read_text(encoding="utf-8"), encoding="utf-8")
        self.loads += 1
        spec = spec_from_file_location(f"g02_{path.stem}_{self.loads}", path)
        assert spec is not None and spec.loader is not None
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def environment(self) -> ModuleType:
        config = self.load("tools/testing/e2e_config.py")
        self.monkeypatch.setitem(sys.modules, "tools.testing.e2e_config", config)
        module = self.load("tools/testing/e2e_environment.py")
        self.monkeypatch.setitem(sys.modules, "tools.testing.e2e_environment", module)
        return module

    def preparation(self) -> ModuleType:
        self.environment()
        return self.load("scripts/prepare-e2e.py")


@pytest.fixture
def setup_sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SetupSandbox:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Offline setup test reached a real process or recursive deletion")

    for method in ("run", "call", "Popen"):
        monkeypatch.setattr(subprocess, method, forbidden)
    monkeypatch.setattr(shutil, "rmtree", forbidden)
    # prepare-e2e.py modifies sys.path at import; do not leak that change to other tests.
    monkeypatch.setattr(sys, "path", sys.path.copy())
    return SetupSandbox(tmp_path / "repo", monkeypatch)


def configuration(module: ModuleType) -> dict[str, Any]:
    project = module.PROJECT
    return {
        "name": project,
        "services": {
            "redmine": {
                "image": f"redmine:{module.VERSION}@sha256:" + "a" * 64,
                "environment": {
                    "REDMINE_TEST_MARKER": "redmine-mcp-synthetic-v1",
                    "REDMINE_E2E_OWNER": "prep-018",
                    "REDMINE_E2E_VERSION": module.VERSION,
                    "REDMINE_E2E_PROJECT": project,
                },
                "ports": [{"host_ip": "127.0.0.1", "published": module.PORT, "target": 3000}],
                "volumes": [
                    {
                        "target": "/opt/testing",
                        "type": "bind",
                        "source": str(module.ROOT / "tools/testing"),
                        "read_only": True,
                    },
                    {
                        "target": "/e2e-state",
                        "type": "bind",
                        "source": str(module.STATE),
                        "read_only": False,
                    },
                    {
                        "target": "/usr/src/redmine/files",
                        "type": "volume",
                        "source": "redmine_files",
                    },
                ],
            },
            "postgres": {
                "image": "postgres:17",
                "ports": [{"host_ip": "127.0.0.1", "published": 5433, "target": 5432}],
                "volumes": [
                    {
                        "target": "/var/lib/postgresql/data",
                        "type": "volume",
                        "source": "redmine_db_data",
                    }
                ],
            },
        },
        "volumes": {
            key: {
                "name": f"{project}_{key}",
                "labels": {
                    "redmine-mcp.environment": "synthetic-test",
                    "redmine-mcp.redmine-version": module.VERSION,
                },
            }
            for key in ("redmine_db_data", "redmine_files")
        },
    }


def volume(module: ModuleType, name: str) -> dict[str, Any]:
    return {
        "Name": name,
        "Labels": {
            "com.docker.compose.project": module.PROJECT,
            "com.docker.compose.volume": name.removeprefix(module.PROJECT + "_"),
            "redmine-mcp.environment": "synthetic-test",
            "redmine-mcp.redmine-version": module.VERSION,
        },
    }


def containers(module: ModuleType, data: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for service in ("redmine", "postgres"):
        config = data["services"][service]
        result[service] = {
            "Id": f"owned-{service}",
            "State": {"Running": True},
            "Config": {
                "Image": config["image"],
                "Labels": {
                    "com.docker.compose.project": module.PROJECT,
                    "com.docker.compose.service": service,
                },
                "Env": [f"{k}={v}" for k, v in config.get("environment", {}).items()],
            },
            "Mounts": [
                {
                    "Destination": mount["target"],
                    "Type": mount["type"],
                    "Name": f"{module.PROJECT}_{mount['source']}",
                    "Source": mount["source"],
                    "RW": not mount.get("read_only", False),
                }
                for mount in config["volumes"]
            ],
            "NetworkSettings": {
                "Ports": {"3000/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(module.PORT)}]}
            },
        }
    return result


def replace(data: Any, path: tuple[str | int, ...], value: Any) -> None:
    for key in path[:-1]:
        data = data[key]
    data[path[-1]] = value


def completed(command: list[str], *, code: int = 0, data: Any = None) -> Any:
    return subprocess.CompletedProcess(command, code, json.dumps(data), "")
