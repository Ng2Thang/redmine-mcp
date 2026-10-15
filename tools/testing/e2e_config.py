"""Side-effect-free selection of an existing synthetic Compose profile."""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIND = "redmine-mcp-synthetic-v1"
OWNER = "prep-018"
VERSION = os.environ.get("REDMINE_E2E_VERSION", "7.0.2")


def supported_version(value: str) -> bool:
    return re.fullmatch(r"6\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)|7\.0\.2", value) is not None


def repository_path(value: str) -> Path:
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("E2E profile paths must stay within the repository")
    return path


if not supported_version(VERSION):
    raise ValueError("REDMINE_E2E_VERSION must be an exact 6.x.x release or 7.0.2")

custom = os.environ.get("REDMINE_E2E_COMPOSE_FILE")
ENV_FILE: Path | None
if custom:
    required = ("REDMINE_E2E_COMPOSE_PROJECT", "REDMINE_E2E_ENV_FILE", "REDMINE_E2E_PORT")
    if any(not os.environ.get(name) for name in required):
        raise ValueError("A custom E2E profile requires COMPOSE_PROJECT, ENV_FILE and PORT settings")
    COMPOSE_FILE = repository_path(custom)
    PROJECT = os.environ["REDMINE_E2E_COMPOSE_PROJECT"]
    ENV_FILE = repository_path(os.environ["REDMINE_E2E_ENV_FILE"])
elif VERSION in {"6.0.1", "7.0.2"}:
    COMPOSE_FILE = ROOT / "deploy" / f"compose.test.{VERSION}.yaml"
    PROJECT = f"redmine-mcp-dev-{VERSION.replace('.', '-')}"
    ENV_FILE = None
    if os.environ.get("REDMINE_E2E_COMPOSE_PROJECT", PROJECT) != PROJECT:
        raise ValueError("Changing an E2E project requires a complete custom Compose profile")
    if os.environ.get("REDMINE_E2E_ENV_FILE"):
        raise ValueError("Built-in E2E profiles do not use an env file")
else:
    raise ValueError("This 6.x release requires an explicit REDMINE_E2E_COMPOSE_FILE profile")

if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", PROJECT):
    raise ValueError("Invalid E2E Compose project name")
if (
    ENV_FILE is not None
    and ENV_FILE != ROOT / ".env"
    and not ENV_FILE.is_relative_to((ROOT / ".local").resolve())
):
    raise ValueError("E2E credentials must be in the root .env or ignored .local directory")
if not COMPOSE_FILE.is_file():
    raise ValueError("Selected E2E Compose override does not exist")

STATE = ROOT / ".local/e2e" / (VERSION if custom else PROJECT)
PORT = int(os.environ.get("REDMINE_E2E_PORT", "3001" if VERSION == "6.0.1" else "3002"))
if not 1024 <= PORT <= 65535:
    raise ValueError("REDMINE_E2E_PORT must be between 1024 and 65535")
URL = f"http://127.0.0.1:{PORT}"


def validate_image(image: str) -> str:
    pattern = rf"redmine:{re.escape(VERSION)}(?:-[a-z0-9.-]+)?@sha256:[0-9a-f]{{64}}"
    if not re.fullmatch(pattern, image):
        raise ValueError("E2E image must be redmine:<selected-version>[-variant]@sha256:<digest>")
    if os.environ.get("REDMINE_E2E_IMAGE", image) != image:
        raise ValueError("REDMINE_E2E_IMAGE must match the selected Compose image pin")
    return image


def process_environment() -> dict[str, str]:
    return os.environ | {
        "MSYS_NO_PATHCONV": "1",
        "MSYS2_ARG_CONV_EXCL": "*",
        "REDMINE_E2E_VERSION": VERSION,
        "REDMINE_TEST_VERSION": VERSION,
        "REDMINE_E2E_STATE": STATE.as_posix(),
    }


def compose_command(*arguments: str) -> list[str]:
    if not custom:
        return [
            sys.executable,
            str(ROOT / "scripts/local_env.py"),
            "compose",
            "-f",
            str(ROOT / "deploy/compose.e2e.yaml"),
            *arguments,
        ]
    return [
        "docker",
        "compose",
        "-p",
        PROJECT,
        "--env-file",
        str(ENV_FILE),
        "-f",
        str(ROOT / "deploy/compose.yaml"),
        "-f",
        str(COMPOSE_FILE),
        *arguments,
    ]


def native_command(script: str, *arguments: str) -> list[str]:
    if not re.fullmatch(r"[a-z0-9_]+\.rb", script):
        raise ValueError("Invalid native E2E script name")
    return compose_command(
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
