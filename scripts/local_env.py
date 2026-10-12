"""Local credential management for Git Bash scripts; never print credentials."""

import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = os.environ.get("REDMINE_TEST_VERSION", "7.0.2")
if VERSION not in {"7.0.2", "6.0.1"}:
    raise SystemExit("Unsupported synthetic Redmine version.")
STATE = ROOT / ".local" / "redmine-6.0.1" if VERSION == "6.0.1" else ROOT / ".local"
ENV = STATE / ".env" if VERSION == "6.0.1" else ROOT / ".env"
KIND = "redmine-mcp-synthetic-v1"


def read_env() -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for line in ENV.read_text(encoding="utf-8-sig").splitlines()
        if line and not line.startswith("#") and "=" in line
    )


def write_env(values: dict[str, str]) -> None:
    ENV.write_text(
        "".join(f"{key}={value}\n" for key, value in sorted(values.items())), encoding="utf-8"
    )


def main() -> None:
    action = sys.argv[1]
    STATE.mkdir(parents=True, exist_ok=True)
    if action == "init" and not ENV.exists():
        write_env(
            {
                "REDMINE_URL": f"http://localhost:{3001 if VERSION == '6.0.1' else 3002}",
                "POSTGRES_PASSWORD": secrets.token_hex(32),
                "TEST_USER_PASSWORD": secrets.token_hex(24),
                "REDMINE_SECRET_KEY_BASE": secrets.token_hex(64),
                "REDMINE_TEST_MARKER": KIND,
                "REDMINE_TIMEOUT_SECONDS": "20",
                "LOG_LEVEL": "INFO",
            }
        )
    if not ENV.exists() or read_env().get("REDMINE_TEST_MARKER") != KIND:
        raise SystemExit("Not a marked synthetic .env; keep real configuration separate.")
    original = read_env()
    values = original.copy()
    if VERSION == "7.0.2" and values.get("REDMINE_URL") in {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }:
        values["REDMINE_URL"] = "http://localhost:3002"
    values.setdefault("MCP_HOST_PORT", "8002" if VERSION == "6.0.1" else "8000")
    values.setdefault("MCP_WRITER_HOST_PORT", "8003" if VERSION == "6.0.1" else "8001")
    values.setdefault("REDMINE_PUBLIC_URL", f"http://localhost:{3001 if VERSION == '6.0.1' else 3002}")
    for legacy_key in ("REDMINE_API_KEY", "MCP_API_TOKEN"):
        values.pop(legacy_key, None)
    if values != original:
        write_env(values)
    if action in {"assert", "runtime", "reset-state"}:
        marker = STATE / "environment.json"
        if not marker.exists() or json.loads(marker.read_text())["kind"] != KIND:
            raise SystemExit("Missing/invalid synthetic environment marker.")
    if action == "reset-state":
        for name in (
            "manifest.json",
            "manifest.tmp",
            "history-manifest.json",
            "history-manifest.tmp",
            "credentials.json",
            "environment.json",
        ):
            target = (STATE / name).resolve()
            if target.parent != STATE.resolve():
                raise SystemExit("Path outside local state")
            target.unlink(missing_ok=True)
    elif action not in {"init", "assert", "runtime"}:
        raise SystemExit("Unknown action")


if __name__ == "__main__":
    main()
