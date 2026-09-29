"""Local credential management for Git Bash scripts; never print credentials."""

import json
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
STATE = ROOT / ".local"
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
    STATE.mkdir(exist_ok=True)
    if action == "init" and not ENV.exists():
        write_env(
            {
                "REDMINE_URL": "http://localhost:3000",
                "REDMINE_API_KEY": "bootstrap-pending",
                "MCP_API_TOKEN": secrets.token_hex(32),
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
    if action in {"assert", "reader", "reset-state"}:
        marker = STATE / "environment.json"
        if not marker.exists() or json.loads(marker.read_text())["kind"] != KIND:
            raise SystemExit("Missing/invalid synthetic environment marker.")
    if action == "reader":
        credentials = json.loads((STATE / "credentials.json").read_text())
        values = read_env()
        values["REDMINE_API_KEY"] = credentials["reader_key"]
        write_env(values)
    elif action == "reset-state":
        for name in ("manifest.json", "manifest.tmp", "credentials.json", "environment.json"):
            target = (STATE / name).resolve()
            if target.parent != STATE.resolve():
                raise SystemExit("Path outside local state")
            target.unlink(missing_ok=True)
    elif action not in {"init", "assert"}:
        raise SystemExit("Unknown action")


if __name__ == "__main__":
    main()
