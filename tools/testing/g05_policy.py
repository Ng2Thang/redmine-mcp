"""Allocate one fresh two-service policy stack; never reuse or reset existing data."""

import copy
import json
import socket
import subprocess
from uuid import uuid4

from tools.testing.e2e_config import ROOT, VERSION, process_environment
from tools.testing.e2e_environment import compose_configuration


class PolicyStack:
    def __init__(self) -> None:
        self.allocated = False
        self.project = f"redmine-mcp-g05-policy-{VERSION.replace('.', '-')}-{uuid4().hex[:12]}"
        self.state = ROOT / ".local/testing" / self.project
        self.state.mkdir(parents=True, exist_ok=False)
        self.file = self.state / "compose.json"
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        source = compose_configuration()
        services = copy.deepcopy({n: source["services"][n] for n in ("redmine", "postgres")})
        for service in services.values():
            service.pop("container_name", None)
            service["restart"] = "no"
        services["postgres"]["ports"] = []
        redmine = services["redmine"]
        redmine["ports"] = [{"target": 3000, "published": str(port), "host_ip": "127.0.0.1"}]
        redmine["environment"].update(REDMINE_E2E_PROJECT=self.project, REDMINE_G05_POLICY="1")
        redmine["volumes"] = [
            mount
            for mount in redmine["volumes"]
            if mount["target"] not in ("/seed-state", "/opt/seed")
        ]
        for mount in redmine["volumes"]:
            if mount["target"] == "/e2e-state":
                mount["source"] = self.state.as_posix()
        volumes = copy.deepcopy(
            {n: source["volumes"][n] for n in ("redmine_db_data", "redmine_files")}
        )
        for name, volume in volumes.items():
            volume["name"] = f"{self.project}_{name}"
            volume["labels"]["redmine-mcp.owner"] = "g05"
        config = {
            "name": self.project,
            "services": services,
            "volumes": volumes,
            "networks": {"default": {"name": f"{self.project}_default"}},
        }
        self.file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.file.chmod(0o600)

    def compose(self, *arguments: str) -> list[str]:
        return ["docker", "compose", "-p", self.project, "-f", str(self.file), *arguments]

    def native(self, script: str, *arguments: str) -> list[str]:
        if script not in {"g05_policy.rb", "g05_fixtures.rb", "e2e_guard.rb"}:
            raise ValueError("Unexpected G05 policy script")
        return self.compose(
            "exec",
            "-T",
            "redmine",
            "bundle",
            "exec",
            "rails",
            "runner",
            f"/opt/testing/{script}",
            *arguments,
        )

    def run(self, command: list[str], label: str, timeout: int = 180) -> None:
        with (self.state / f"{label}.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=process_environment(),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        if result.returncode:
            raise AssertionError(f"G05 isolated {label} failed; inspect its private log")

    def start(self) -> None:
        # Refuse reuse even on the extremely unlikely generated-name collision.
        for name in ("redmine_db_data", "redmine_files"):
            found = subprocess.run(
                ["docker", "volume", "inspect", f"{self.project}_{name}"],
                capture_output=True,
                env=process_environment(),
                check=False,
            )
            if found.returncode == 0:
                raise AssertionError("Refusing pre-existing G05 policy volume")
        self.allocated = True
        self.run(self.compose("up", "-d", "--wait", "--wait-timeout", "600"), "up", 660)
        self.run(self.native("g05_policy.rb", "initialize"), "initialize")

    def cleanup(self) -> None:
        if not self.allocated:
            return
        # Check the actual volume labels before any removal, not just a generated path.
        for name in ("redmine_db_data", "redmine_files"):
            found = subprocess.run(
                ["docker", "volume", "inspect", f"{self.project}_{name}"],
                capture_output=True,
                text=True,
                env=process_environment(),
                check=False,
            )
            if found.returncode:
                raise AssertionError("Cannot verify disposable G05 policy volume")
            labels = json.loads(found.stdout)[0].get("Labels") or {}
            expected = {
                "com.docker.compose.project": self.project,
                "redmine-mcp.owner": "g05",
                "redmine-mcp.redmine-version": VERSION,
                "redmine-mcp.environment": "synthetic-test",
            }
            if any(labels.get(k) != v for k, v in expected.items()):
                raise AssertionError("Refusing foreign G05 policy volume removal")
        self.run(self.native("e2e_guard.rb"), "cleanup-guard")
        self.run(self.compose("down", "--volumes"), "down")
        (self.state / "cleanup.json").write_text(
            json.dumps(
                {
                    "owner": "g05",
                    "version": VERSION,
                    "project": self.project,
                    "cleanup": "passed",
                    "global_settings_changed_only_in_disposable_stack": True,
                }
            ),
            encoding="utf-8",
        )
