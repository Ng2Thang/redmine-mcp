"""Provision an isolated, owned Redmine 7.0.2 fixture environment; never reset shared data."""

import json
import os
import re
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".local" / "testing-e2e"
OWNER = "prep-018"
KIND = "redmine-mcp-synthetic-v1"


def main() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    environment = os.environ | {"MSYS_NO_PATHCONV": "1", "MSYS2_ARG_CONV_EXCL": "*"}
    target = re.search(r"image: (redmine:[^\s]+)", (ROOT / "deploy/compose.test.yaml").read_text())
    if target is None:
        raise SystemExit("Missing pinned Redmine image")
    env_path = STATE / "compose.env"
    if not env_path.exists():
        env_path.write_text(
            f"POSTGRES_PASSWORD={secrets.token_hex(32)}\n"
            f"REDMINE_SECRET_KEY_BASE={secrets.token_hex(64)}\n",
            encoding="utf-8",
        )
    label = {
        "redmine-mcp.environment": "synthetic-test",
        "redmine-mcp.owner": OWNER,
        "redmine-mcp.redmine-version": "7.0.2",
    }
    compose = {
        "name": "redmine-mcp-e2e",
        "services": {
            "postgres": {
                "image": "postgres:16.8-bookworm",
                "environment": {
                    "POSTGRES_DB": "redmine",
                    "POSTGRES_USER": "redmine",
                    "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}",
                },
                "volumes": ["database:/var/lib/postgresql/data"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U redmine -d redmine"],
                    "interval": "3s",
                    "timeout": "3s",
                    "retries": 60,
                },
            },
            "redmine": {
                "image": target.group(1),
                "environment": {
                    "REDMINE_DB_POSTGRES": "postgres",
                    "REDMINE_DB_DATABASE": "redmine",
                    "REDMINE_DB_USERNAME": "redmine",
                    "REDMINE_DB_PASSWORD": "${POSTGRES_PASSWORD}",
                    "REDMINE_SECRET_KEY_BASE": "${REDMINE_SECRET_KEY_BASE}",
                    "SECRET_KEY_BASE": "${REDMINE_SECRET_KEY_BASE}",
                    "RAILS_ENV": "production",
                    "REDMINE_TEST_MARKER": KIND,
                    "REDMINE_E2E_OWNER": OWNER,
                },
                "ports": ["127.0.0.1:3001:3000"],
                "volumes": [
                    "files:/usr/src/redmine/files",
                    f"{(ROOT / 'tools/testing').as_posix()}:/opt/testing:ro",
                    f"{STATE.as_posix()}:/seed-state",
                ],
                "depends_on": {"postgres": {"condition": "service_healthy"}},
                "healthcheck": {
                    "test": [
                        "CMD",
                        "ruby",
                        "-rnet/http",
                        "-e",
                        "exit(Net::HTTP.get_response(URI('http://127.0.0.1:3000/login'))"
                        ".code == '200' ? 0 : 1)",
                    ],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 90,
                    "start_period": "20s",
                },
            },
        },
        "volumes": {"database": {"labels": label}, "files": {"labels": label}},
    }
    path = STATE / "compose.json"
    for name in ("redmine-mcp-e2e_database", "redmine-mcp-e2e_files"):
        inspected = subprocess.run(
            ["docker", "volume", "inspect", name], capture_output=True, text=True
        )
        if inspected.returncode == 0:
            labels = json.loads(inspected.stdout)[0].get("Labels", {})
            if (
                labels.get("redmine-mcp.owner") != OWNER
                or labels.get("redmine-mcp.redmine-version") != "7.0.2"
            ):
                raise SystemExit("Refusing to reuse an unowned or incompatible E2E volume")
    path.write_text(json.dumps(compose, indent=2), encoding="utf-8")
    command = ["docker", "compose", "--env-file", str(env_path), "-f", str(path)]
    subprocess.run(
        [*command, "up", "-d", "--wait", "--wait-timeout", "600"], check=True, env=environment
    )
    seeded = subprocess.run(
        [
            *command,
            "exec",
            "-T",
            "redmine",
            "bundle",
            "exec",
            "rails",
            "runner",
            "/opt/testing/e2e_seed.rb",
        ],
        check=False,
        env=environment,
        capture_output=True,
        text=True,
    )
    (STATE / "seed.log").write_text(seeded.stdout + seeded.stderr, encoding="utf-8")
    if seeded.returncode:
        raise SystemExit("Owned fixture preparation failed; inspect ignored seed.log")
    if not (STATE / "fixtures.json").exists():
        raise SystemExit("Fixture preparation did not produce its private manifest")
    print("Owned Redmine 7.0.2 fixtures ready; credentials remain in ignored .local/testing-e2e.")


if __name__ == "__main__":
    main()
