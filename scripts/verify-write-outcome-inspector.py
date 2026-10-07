"""Check prep-019 writer discovery/schema compatibility using read-only Inspector calls."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS  # noqa: E402
from tests.e2e.conftest import preflight  # noqa: E402


def main() -> None:
    manifest = preflight()
    state = ROOT / ".local/testing-e2e/prep-019" / uuid4().hex
    state.mkdir(parents=True)
    config = state / "inspector.json"
    config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "owned": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:18083/mcp",
                        "headers": {"X-Redmine-API-Key": manifest["users"]["a"]["key"]},
                    }
                }
            }
        )
    )
    os.chmod(config, 0o600)
    calls = [None, ("get_issue", {"issue_id": manifest["issues"]["a"]})]
    with (state / "server.log").open("w") as log:
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "tests.e2e.server:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "18083",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            with httpx.Client(base_url="http://127.0.0.1:18083", trust_env=False) as client:
                for _ in range(150):
                    if server.poll() is not None:
                        raise RuntimeError(
                            "Owned Inspector server exited; inspect private evidence"
                        )
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.2)
                else:
                    raise RuntimeError("Owned Inspector server did not start")
            for index, call in enumerate(calls):
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
                (state / f"inspector-{index}.log").write_text(result.stdout + result.stderr)
                if result.returncode:
                    raise RuntimeError("Inspector failed; inspect ignored private evidence")
                payload = json.loads(result.stdout)["result"]
                if call is None:
                    tools = {tool["name"]: tool for tool in payload["tools"]}
                    assert set(tools) == set(READ_OPERATIONS) | set(WRITE_OPERATIONS)
                    for name in WRITE_OPERATIONS:
                        assert tools[name]["annotations"]["readOnlyHint"] is False
                    for name in (
                        "add_project_members",
                        "update_project_members",
                        "delete_project_members",
                    ):
                        schema = tools[name]["inputSchema"]
                        assert schema["additionalProperties"] is False
                        assert schema["properties"]["items"]["maxItems"] == 10
                        assert schema["properties"]["items"]["minItems"] == 1
                    assert "subject" in tools["create_issue"]["inputSchema"]["properties"]
                    assert "name" in tools["create_project_version"]["inputSchema"]["properties"]
                    assert (
                        "content_base64" in tools["upload_attachment"]["inputSchema"]["properties"]
                    )
                else:
                    assert not payload.get("isError"), "Inspector read call failed"
                    assert (
                        json.loads(payload["content"][0]["text"])["id"] == manifest["issues"]["a"]
                    )
            (state / "inspector-evidence.json").write_text(
                json.dumps(
                    {
                        "owner": "prep-019",
                        "version": "7.0.2",
                        "discovery": "passed",
                        "writer_schemas": "passed",
                        "read_calls": 1,
                        "mutation_calls": 0,
                    },
                    indent=2,
                )
            )
        finally:
            server.terminate()
            server.wait(timeout=15)
    print("Prep-019 Inspector discovery, writer schemas, and read call passed; server stopped.")


if __name__ == "__main__":
    main()
