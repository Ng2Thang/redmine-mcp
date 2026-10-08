"""Read-only TOOL-036 Inspector checks on the explicitly selected synthetic port 3000."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.e2e.test_issue_tag_filters import UNKNOWN, owned_manifest  # noqa: E402


def main() -> None:
    manifest = owned_manifest()
    state = ROOT / ".local"
    config = state / "tool-036-inspector-config.json"
    server = None
    try:
        config.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "owned": {
                            "type": "streamable-http",
                            "url": "http://127.0.0.1:18083/mcp",
                            "headers": {"X-Redmine-API-Key": manifest["credentials"]["admin_key"]},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        os.chmod(config, 0o600)
        with (state / "tool-036-inspector-server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "tests.e2e.test_issue_tag_filters:create_tag_reader_app",
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
            with httpx.Client(base_url="http://127.0.0.1:18083", trust_env=False) as client:
                for _ in range(100):
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.2)
                else:
                    raise RuntimeError("TOOL-036 reader did not start")
            calls = [
                None,
                {"tags_any": ["notification", UNKNOWN], "status_id": "*"},
                {"tags_any": [UNKNOWN], "status_id": "*"},
            ]
            for index, args in enumerate(calls):
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
                    "tools/list" if args is None else "tools/call",
                ]
                if args is not None:
                    command += ["--tool-name", "list_issues", "--tool-args-json", json.dumps(args)]
                result = subprocess.run(
                    command, capture_output=True, text=True, cwd=ROOT, timeout=60
                )
                (state / f"tool-036-inspector-{index}.log").write_text(
                    result.stdout + result.stderr,
                    encoding="utf-8",
                )
                if result.returncode:
                    raise RuntimeError("Inspector failed; inspect ignored private evidence")
                payload = json.loads(result.stdout)["result"]
                if args is None:
                    tool = next(t for t in payload["tools"] if t["name"] == "list_issues")
                    assert tool["inputSchema"]["properties"]["tags_any"]["type"] == "array"
                else:
                    assert not payload.get("isError")
                    body = json.loads(payload["content"][0]["text"])
                    assert body["total"] > 0 if index == 1 else body["total"] == 0
            (state / "tool-036-inspector-evidence.json").write_text(
                json.dumps(
                    {
                        "task": "TOOL-036",
                        "target": "http://localhost:3000",
                        "version": "6.0.5",
                        "inspector": "2.8.0",
                        "discovery": "passed",
                        "read_calls_passed": 2,
                        "access": "read-only",
                        "limitations": "No existing two-tag overlap or 7.0.2 acceptance",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
    finally:
        try:
            if server is not None:
                server.terminate()
                try:
                    server.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=15)
        finally:
            config.unlink(missing_ok=True)
    print("TOOL-036 Inspector discovery and two reads passed; server stopped; config removed.")


if __name__ == "__main__":
    main()
