"""Read-only Inspector discovery/invocation for tasks 034 and 035 on owned Redmine."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from redmine_mcp.auth import READ_OPERATIONS  # noqa: E402
from tests.e2e.conftest import preflight  # noqa: E402
from tools.testing.e2e_config import STATE, VERSION  # noqa: E402


def main() -> None:
    manifest = preflight()
    state = STATE
    config = state / "reporting-inspector.json"
    config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "owned": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:18082/mcp",
                        "headers": {"X-Redmine-API-Key": manifest["users"]["a"]["key"]},
                    }
                }
            }
        )
    )
    os.chmod(config, 0o600)
    calls: list[tuple[str, dict[str, Any]]] = [
        ("list_issues", {"project_id": manifest["projects"]["a"], "status_id": "*"}),
        ("get_issue", {"issue_id": manifest["issues"]["a"]}),
        ("list_time_entries", {}),
        ("list_time_entries", {"user_id": "me"}),
        ("list_time_entries", {"user_id": manifest["users"]["a"]["id"]}),
        (
            "list_time_entries",
            {
                "project_id": manifest["projects"]["parent"],
                "include_subprojects": True,
                "spent_from": "2026-09-01",
                "spent_to": "2026-09-30",
                "issue_id": manifest["issues"]["child"],
            },
        ),
    ]
    with (state / "reporting-inspector-server.log").open("w") as log:
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "tests.e2e.server:create_reader_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "18082",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            with httpx.Client(base_url="http://127.0.0.1:18082", trust_env=False) as client:
                for _ in range(150):
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        time.sleep(0.2)
                else:
                    raise RuntimeError("Owned reporting server did not start")
            for index, call in enumerate([None, *calls]):
                command = [
                    "npx.cmd" if os.name == "nt" else "npx",
                    "--yes",
                    "@modelcontextprotocol/inspector@2.8.0",
                    "--cli",
                    "--config",
                    str(config),
                    "--server",
                    "owned",
                    "--format",
                    "json",
                    "--method",
                    "tools/list" if call is None else "tools/call",
                ]
                if call is not None:
                    command += ["--tool-name", call[0], "--tool-args-json", json.dumps(call[1])]
                result = subprocess.run(
                    command, capture_output=True, text=True, cwd=ROOT, timeout=60
                )
                (state / f"reporting-inspector-{index}.log").write_text(
                    result.stdout + result.stderr
                )
                if result.returncode:
                    raise RuntimeError(
                        "Reporting Inspector failed; inspect ignored private evidence"
                    )
                payload = json.loads(result.stdout)["result"]
                if call is None:
                    assert {tool["name"] for tool in payload["tools"]} == set(READ_OPERATIONS)
                else:
                    assert not payload.get("isError"), "Reporting Inspector call failed"
                    body = json.loads(payload["content"][0]["text"])
                    if call[0] in {"list_issues", "get_issue"}:
                        rows = body["items"] if call[0] == "list_issues" else [body]
                        assert all(
                            "estimated_hours" in row and "total_estimated_hours" in row
                            for row in rows
                        )
                    else:
                        assert body["visibility"]["scope"] == "requesting_redmine_user"
            (state / "reporting-inspector-evidence.json").write_text(
                json.dumps(
                    {
                        "owner": "prep-018",
                        "version": VERSION,
                        "discovery": "passed",
                        "calls_passed": len(calls),
                        "access": "read-only",
                    },
                    indent=2,
                )
            )
        finally:
            server.terminate()
            server.wait(timeout=15)
    print("Reporting Inspector discovery and six read-only calls passed; server stopped.")


if __name__ == "__main__":
    main()
