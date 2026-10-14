"""Supplement G05 ASGI acceptance with localhost socket calls through Inspector 2.8.0."""

import asyncio
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.e2e.conftest import preflight  # noqa: E402
from tests.e2e.g05_helpers import VariantEnvironment, fixture_command  # noqa: E402
from tools.testing.e2e_config import PROJECT, STATE, VERSION  # noqa: E402


async def verify() -> None:
    preflight()
    data = await asyncio.to_thread(fixture_command, "setup")
    environment = VariantEnvironment(data)
    config = STATE / "g05-inspector-config.json"
    server = None
    calls: list[str] = []
    try:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        config.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "owned": {
                            "type": "streamable-http",
                            "url": f"http://127.0.0.1:{port}/mcp",
                            "headers": {"X-Redmine-API-Key": environment.key("writer")},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        config.chmod(0o600)
        with (STATE / "g05-inspector-server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "tests.e2e.g05_helpers:inspector_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            async with httpx.AsyncClient(trust_env=False) as client:
                for _ in range(150):
                    if server.poll() is not None:
                        raise AssertionError("G05 Inspector server exited; inspect private log")
                    try:
                        if (await client.get(f"http://127.0.0.1:{port}/health")).status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(0.2)
                else:
                    raise AssertionError("G05 Inspector server did not become healthy")

            async def call(operation: str | None, arguments: Any = None) -> Any:
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
                    "tools/list" if operation is None else "tools/call",
                ]
                if operation:
                    command.extend(
                        ["--tool-name", operation, "--tool-args-json", json.dumps(arguments)]
                    )
                result = await asyncio.to_thread(
                    subprocess.run, command, cwd=ROOT, capture_output=True, text=True, timeout=60
                )
                path = STATE / f"g05-inspector-{len(calls)}.log"
                path.write_text(result.stdout + result.stderr, encoding="utf-8")
                path.chmod(0o600)
                assert result.returncode == 0, "Inspector failed; inspect private output"
                payload = json.loads(result.stdout)["result"]
                calls.append(operation or "tools/list")
                if operation is None:
                    assert len(payload["tools"]) == 36
                    return payload
                assert not payload.get("isError"), "Inspector call failed; inspect private output"
                return json.loads(payload["content"][0]["text"])

            await call(None)
            user = await call("get_current_user", {})
            assert user["id"] == data["users"]["writer"]["id"]
            tagged = await call(
                "list_issues", {"tags_any": data["tags"], "status_id": "*", "limit": 100}
            )
            assert {r["id"] for r in tagged["items"]} == {
                data["issues"][n] for n in ("a", "b", "ab", "private", "child", "other")
            }
            issue = data["issues"]["a"]
            note = await call(
                "update_issue_note",
                {
                    "issue_id": issue,
                    "journal_id": data["journals"]["writer"],
                    "notes": "G05 Inspector edited",
                },
            )
            assert note["verification"] == "matched"
            relation = await call(
                "create_issue_relation",
                {"issue_id": issue, "issue_to_id": data["issues"]["b"], "relation_type": "blocked"},
            )
            assert relation["verification"] == "matched"
            deleted = await call("delete_issue_relation", {"relation_id": relation["resource_id"]})
            assert deleted["verification"] == "matched"
            target = data["users"]["reader"]["id"]
            watcher = await call("add_issue_watcher", {"issue_id": issue, "user_id": target})
            assert watcher["verification"] == "matched"
            removed = await call("remove_issue_watcher", {"issue_id": issue, "user_id": target})
            assert removed["verification"] == "matched"
            attachments = await asyncio.to_thread(fixture_command, "attachments")
            for container in ("issue", "version"):
                attachment = attachments[container]["target"]
                context = {
                    "container_type": container,
                    "container_id": issue if container == "issue" else data["version_id"],
                }
                updated = await call(
                    "update_attachment",
                    {"attachment_id": attachment, **context, "description": "G05 Inspector edited"},
                )
                assert updated["verification"] == "matched"
                deleted = await call("delete_attachment", {"attachment_id": attachment, **context})
                assert deleted["verification"] == "matched"
            entry = await call(
                "create_time_entry",
                {
                    "issue_id": issue,
                    "hours": 1,
                    "spent_on": data["today"],
                    "activity_id": data["activities"]["active"],
                    "comments": "G05 Inspector",
                },
            )
            assert entry["verification"] == "matched"
            updated = await call(
                "update_time_entry",
                {"issue_id": issue, "time_entry_id": entry["resource_id"], "hours": 1.234},
            )
            assert updated["verification"] == "matched"
            native = (
                await environment.redmine("GET", f"time_entries/{entry['resource_id']}.json")
            )["time_entry"]
            assert native["user"]["id"] == data["users"]["writer"]["id"]
        (STATE / "g05-inspector-evidence.json").write_text(
            json.dumps(
                {
                    "owner": "g05",
                    "version": VERSION,
                    "project": PROJECT,
                    "inspector": "2.8.0",
                    "caller": "ordinary writer",
                    "transport": "localhost uvicorn socket",
                    "calls": calls,
                    "limitations": "Socket evidence only; container/browser/reset remain separate",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    finally:
        if server is not None:
            server.terminate()
            try:
                await asyncio.to_thread(server.wait, timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                await asyncio.to_thread(server.wait, timeout=15)
        config.unlink(missing_ok=True)
        cleanup = await asyncio.to_thread(fixture_command, "cleanup")
        assert cleanup["cleanup"] == "passed"
    print(f"G05 Inspector {VERSION}: {len(calls)} calls passed; server and fixtures cleaned.")


if __name__ == "__main__":
    asyncio.run(verify())
