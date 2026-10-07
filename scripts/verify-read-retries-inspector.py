"""PREP-027 owned synthetic reader startup and read-only Inspector compatibility."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from redmine_mcp.auth import READ_OPERATIONS  # noqa: E402
from tests.e2e.conftest import preflight  # noqa: E402


def _verify(state: Path, config: Path, headers: dict[str, str]) -> None:
    with httpx.Client(base_url="http://127.0.0.1:3001", headers=headers, trust_env=False) as native:
        response = native.get("/issues.json", params={"limit": 1, "status_id": "*"})
        assert response.status_code == 200, "Owned native issue lookup failed"
        issues = response.json()["issues"]
        assert issues, "Owned caller has no visible synthetic issue"
        issue_id = issues[0]["id"]
        expected = native.get(f"/issues/{issue_id}.json")
        assert expected.status_code == 200, "Owned native detail lookup failed"
        project_id = expected.json()["issue"]["project"]["id"]
    config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "owned-reader": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:18087/mcp",
                        "headers": headers,
                    }
                }
            }
        )
    )
    os.chmod(config, 0o600)
    with (state / "server.log").open("w") as log:
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
                "18087",
                "--no-access-log",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            with httpx.Client(base_url="http://127.0.0.1:18087", trust_env=False) as client:
                for _ in range(120):
                    assert server.poll() is None, "Owned reader server exited; inspect private log"
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.2)
                else:
                    raise RuntimeError("Owned reader startup timed out")
            calls = [
                None,
                ("get_issue", {"issue_id": issue_id}),
                ("get_project", {"project_id": project_id}),
                ("list_issues", {"project_id": project_id, "limit": 1}),
            ]
            for index, call in enumerate(calls):
                command = [
                    "npx.cmd" if os.name == "nt" else "npx",
                    "--offline",
                    "--yes",
                    "@modelcontextprotocol/inspector@2.8.0",
                    "--cli",
                    "--config",
                    str(config),
                    "--server",
                    "owned-reader",
                    "--format",
                    "json",
                    "--method",
                    "tools/list" if call is None else "tools/call",
                ]
                if call is not None:
                    command += ["--tool-name", call[0], "--tool-args-json", json.dumps(call[1])]
                result = subprocess.run(
                    command, cwd=ROOT, capture_output=True, text=True, timeout=45
                )
                (state / f"inspector-{index}.log").write_text(result.stdout + result.stderr)
                assert result.returncode == 0, "Inspector failed; inspect private evidence"
                payload = json.loads(result.stdout)["result"]
                if call is None:
                    assert {tool["name"] for tool in payload["tools"]} == set(READ_OPERATIONS)
                else:
                    assert not payload.get("isError"), "Inspector reader tool failed"
                    data = json.loads(payload["content"][0]["text"])
                    if call[0] == "get_issue":
                        assert data["id"] == issue_id
                    elif call[0] == "get_project":
                        assert data["id"] == project_id
                    else:
                        assert all(issue["project"]["id"] == project_id for issue in data["items"])
            (state / "evidence.json").write_text(
                json.dumps(
                    {
                        "owner": "prep-027",
                        "redmine_version": "7.0.2",
                        "inspector_version": "2.8.0",
                        "reader_startup": "passed",
                        "discovery": "passed",
                        "read_calls": 3,
                        "mutations": 0,
                        "fault_injection": "offline only",
                    },
                    indent=2,
                )
            )
            print(
                "PREP-027 Inspector: startup, discovery and three read calls passed; zero mutations"
            )
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)


def main() -> None:
    manifest = preflight()
    state = ROOT / ".local/testing-e2e/prep-027"
    state.mkdir(parents=True, exist_ok=True)
    config = state / "inspector.json"
    headers = {"X-Redmine-API-Key": manifest["users"]["a"]["key"]}
    # Own credential cleanup before any partial write, chmod, log open or process launch.
    # Keep it independent of process shutdown, which can itself raise an exception.
    try:
        _verify(state, config, headers)
    finally:
        config.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
