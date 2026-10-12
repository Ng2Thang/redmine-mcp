"""Provision isolated, version-selected Redmine fixtures; never reset shared data."""

import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.testing.e2e_config import (  # noqa: E402
    PORT,
    PROJECT,
    STATE,
    VERSION,
    validate_image,
)

OWNER = "prep-018"
KIND = "redmine-mcp-synthetic-v1"


def selected_image() -> str:
    supplied = os.environ.get("REDMINE_E2E_IMAGE")
    if supplied:
        return validate_image(supplied)
    # Reuse an existing immutable selection instead of following a changed tag.
    saved = STATE / "compose.json"
    if saved.exists():
        return validate_image(json.loads(saved.read_text())["services"]["redmine"]["image"])
    template = ROOT / "deploy" / f"compose.test.{VERSION}.yaml"
    if template.exists():
        target = re.search(r"image: (redmine:[^\s]+)", template.read_text())
        if target:
            return validate_image(target.group(1))
    # Other 6.x releases resolve the official exact tag once, then persist its digest.
    tag = f"redmine:{VERSION}"
    subprocess.run(["docker", "pull", tag], check=True)
    inspected = subprocess.run(
        ["docker", "image", "inspect", tag], capture_output=True, text=True, check=True
    )
    for digest in json.loads(inspected.stdout)[0].get("RepoDigests", []):
        if digest.startswith("redmine@sha256:"):
            return validate_image(tag + "@" + digest.split("@", 1)[1])
    raise SystemExit("Official Redmine image has no immutable repository digest")


def main() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    environment = os.environ | {"MSYS_NO_PATHCONV": "1", "MSYS2_ARG_CONV_EXCL": "*"}
    target = selected_image()
    manifest_path = STATE / "fixtures.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if (manifest.get("kind"), manifest.get("owner"), manifest.get("version")) != (
            KIND,
            OWNER,
            VERSION,
        ):
            raise SystemExit("Refusing to reuse an unowned or incompatible fixture manifest")
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
        "redmine-mcp.redmine-version": VERSION,
    }
    compose = {
        "name": PROJECT,
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
                "image": target,
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
                    "REDMINE_E2E_VERSION": VERSION,
                },
                "ports": [f"127.0.0.1:{PORT}:3000"],
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
    for name in (f"{PROJECT}_database", f"{PROJECT}_files"):
        inspected = subprocess.run(
            ["docker", "volume", "inspect", name], capture_output=True, text=True
        )
        if inspected.returncode == 0:
            labels = json.loads(inspected.stdout)[0].get("Labels", {})
            if (
                labels.get("redmine-mcp.owner") != OWNER
                or labels.get("redmine-mcp.redmine-version") != VERSION
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
    print(
        f"Owned Redmine {VERSION} fixtures ready; credentials remain in {STATE.relative_to(ROOT)}."
    )


if __name__ == "__main__":
    main()
