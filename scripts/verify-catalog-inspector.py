"""Prep-020 Inspector discovery and native read parity under allowed_all."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS  # noqa: E402
from tests.e2e.conftest import preflight  # noqa: E402


def main() -> None:
    manifest = preflight()
    run = sys.argv[1]
    if len(run) != 32 or any(char not in "0123456789abcdef" for char in run):
        raise ValueError("Invalid owned fixture run identifier")
    state = ROOT / ".local/testing-e2e/prep-020" / run
    fixture = json.loads((state / "fixture.json").read_text())
    assert fixture["owner"] == "prep-020" and fixture["run"] == run
    project = fixture["projects"]["parent"]
    headers = {"X-Redmine-API-Key": manifest["users"]["a"]["key"]}
    config = state / "inspector.json"
    config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "owned": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:18084/mcp",
                        "headers": headers,
                    }
                }
            }
        )
    )
    os.chmod(config, 0o600)
    calls = [
        None,
        ("list_project_versions", {"project_id": project}),
        ("list_project_members", {"project_ids": [project]}),
        ("list_my_project_capabilities", {"project_id": project}),
    ]
    with (state / "inspector-server.log").open("w") as log:
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "tests.e2e.server:create_allowed_all_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "18084",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            with httpx.Client(base_url="http://127.0.0.1:18084", trust_env=False) as client:
                for _ in range(150):
                    if server.poll() is not None:
                        raise RuntimeError("Owned Inspector server exited")
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.2)
                else:
                    raise RuntimeError("Owned Inspector server did not start")
            with httpx.Client(
                base_url="http://127.0.0.1:3001", headers=headers, trust_env=False
            ) as native:
                ownership = native.get(f"/projects/{project}.json")
                assert ownership.status_code == 200
                assert ownership.json()["project"]["identifier"] == fixture["prefix"] + "-parent"
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
                        command, cwd=ROOT, capture_output=True, text=True, timeout=60
                    )
                    (state / f"inspector-{index}.log").write_text(result.stdout + result.stderr)
                    assert result.returncode == 0, "Inspector failed; inspect private evidence"
                    payload = json.loads(result.stdout)["result"]
                    if call is None:
                        tools = {tool["name"]: tool for tool in payload["tools"]}
                        assert set(tools) == set(READ_OPERATIONS) | set(WRITE_OPERATIONS)
                        assert all(
                            not tools[name]["annotations"]["readOnlyHint"]
                            for name in WRITE_OPERATIONS
                        )
                        assert (
                            tools["delete_project_members"]["inputSchema"]["properties"]["items"][
                                "maxItems"
                            ]
                            == 10
                        )
                        continue
                    assert not payload.get("isError"), "Inspector read failed"
                    body = json.loads(payload["content"][0]["text"])
                    if call[0] == "list_my_project_capabilities":
                        assert {"manage_versions", "manage_members"} <= set(
                            body["items"][0]["permissions"]
                        )
                    else:
                        kind = "versions" if call[0] == "list_project_versions" else "memberships"
                        response = native.get(
                            f"/projects/{project}/{kind}.json", params={"limit": 100}
                        )
                        assert response.status_code == 200
                        rows = (
                            body["items"]
                            if kind == "versions"
                            else body["results"][0]["page"]["items"]
                        )
                        assert {row["id"] for row in rows} == {
                            row["id"] for row in response.json()[kind]
                        }

                # Preparation regressions use only disposable fixture state and private headers.
                def invoke_preparation(name, arguments):
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
                        "tools/call",
                        "--tool-name",
                        name,
                        "--tool-args-json",
                        json.dumps(arguments),
                    ]
                    result = subprocess.run(
                        command, cwd=ROOT, capture_output=True, text=True, timeout=60
                    )
                    (state / f"inspector-preparation-{name}.log").write_text(
                        result.stdout + result.stderr
                    )
                    assert result.returncode == 0, "Preparation Inspector call failed"
                    payload = json.loads(result.stdout)["result"]
                    assert not payload.get("isError"), "Preparation Inspector tool failed"
                    return json.loads(payload["content"][0]["text"])

                issue_id = attachment_id = None
                try:
                    created = invoke_preparation(
                        "create_issue",
                        {
                            "project_id": project,
                            "subject": "Prep022 Inspector disposable issue",
                            "description": "clear",
                            "estimated_hours": 2,
                            "due_date": "2026-10-20",
                        },
                    )
                    issue_id = created["resource_id"]
                    assert created["outcome"] == "accepted"
                    for assignment in ("me", None):
                        updated = invoke_preparation(
                            "update_issue",
                            {
                                "issue_id": issue_id,
                                "assigned_to_id": assignment,
                                "description": None,
                                "estimated_hours": None,
                                "due_date": None,
                            },
                        )
                        assert updated["outcome"] == "accepted"
                        observed = native.get(f"/issues/{issue_id}.json")
                        assert observed.status_code == 200
                        raw = observed.json()["issue"]
                        expected = manifest["users"]["a"]["id"] if assignment == "me" else None
                        assert raw.get("assigned_to", {}).get("id") == expected
                        assert not raw.get("description") and raw.get("estimated_hours") is None
                        assert raw.get("due_date") is None
                    uploaded = invoke_preparation(
                        "upload_attachment",
                        {
                            "filename": "prep024-inspector.txt",
                            "content_base64": "aGVsbG8=",
                        },
                    )
                    attachment_id = uploaded["attachment_id"]
                    assert uploaded["outcome"] == "accepted"
                    attached = native.put(
                        f"/issues/{issue_id}.json",
                        json={
                            "issue": {
                                "uploads": [
                                    {
                                        "token": uploaded["token"],
                                        "filename": "prep024-inspector.txt",
                                    }
                                ]
                            }
                        },
                    )
                    assert attached.status_code == 204
                    oversized = httpx.post(
                        "http://127.0.0.1:18084/mcp",
                        content=b"x" * (10 * 1024 * 1024 + 1),
                        headers=headers,
                        trust_env=False,
                    )
                    assert oversized.status_code == 413
                finally:
                    with httpx.Client(
                        base_url="http://127.0.0.1:3001",
                        trust_env=False,
                        headers={"X-Redmine-API-Key": manifest["users"]["admin"]["key"]},
                    ) as cleanup:
                        if issue_id is not None:
                            observed = cleanup.get(f"/issues/{issue_id}.json")
                            assert observed.status_code == 200
                            assert observed.json()["issue"]["project"]["id"] == project
                            assert (
                                observed.json()["issue"]["subject"]
                                == "Prep022 Inspector disposable issue"
                            )
                            assert cleanup.delete(f"/issues/{issue_id}.json").status_code == 204
                        if attachment_id is not None:
                            assert cleanup.delete(
                                f"/attachments/{attachment_id}.json"
                            ).status_code in (204, 404)
            (state / "inspector-evidence.json").write_text(
                json.dumps(
                    {
                        "owner": "prep-020",
                        "version": "7.0.2",
                        "allowed_all_catalog": "passed",
                        "native_read_parity": "passed",
                        "read_calls": 3,
                        "mutation_calls": 4,
                        "preparation_schema_null_assignment_upload_body_limit": "passed",
                    },
                    indent=2,
                )
            )
        finally:
            server.terminate()
            server.wait(timeout=15)
    print("Prep-020 Inspector catalog and three native-parity read calls passed; server stopped.")


if __name__ == "__main__":
    main()
