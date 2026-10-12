"""Run supplemental Inspector and browser acceptance with private owned credentials."""

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
from tools.testing.e2e_config import STATE, URL  # noqa: E402


def main() -> None:
    manifest = preflight()
    state = STATE
    key = manifest["users"]["a"]["key"]
    project_id = manifest["projects"]["a"]
    config = state / "inspector.json"
    config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "owned": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:18081/mcp",
                        "headers": {"X-Redmine-API-Key": key},
                    }
                }
            }
        )
    )
    evidence = {"inspector": "pending", "browser": "pending", "cleanup": "pending"}
    attachment_id = None
    with (state / "supplement-server.log").open("w") as log:
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
                "18081",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            with httpx.Client(
                base_url="http://127.0.0.1:18081",
                trust_env=False,
                headers={"X-Redmine-API-Key": key},
                timeout=30,
            ) as client:
                for _ in range(150):
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        time.sleep(0.2)
                else:
                    raise RuntimeError("Owned supplemental server did not start")
                upload = client.post(
                    "/api/v1/uploads", json={"filename": "e2e.txt", "content_base64": "aGVsbG8="}
                )
                if upload.status_code != 200 or upload.json()["outcome"] != "accepted":
                    raise RuntimeError(
                        "Supplemental upload was not accepted; reconcile before retry"
                    )
                attachment_id = upload.json()["attachment_id"]
                attached = client.post(
                    f"/api/v1/projects/{project_id}/files",
                    json={"filename": "e2e.txt", "token": upload.json()["token"]},
                )
                if attached.status_code != 200 or attached.json()["verification"] != "matched":
                    raise RuntimeError("Supplemental attachment verification failed")
                metadata = client.get(f"/api/v1/attachments/{attachment_id}").json()
                for method, extra in [
                    ("tools/list", []),
                    (
                        "tools/call",
                        [
                            "--tool-name",
                            "list_projects",
                            "--tool-args-json",
                            '{"limit":25,"offset":0}',
                        ],
                    ),
                ]:
                    command = [
                        "npx.cmd" if os.name == "nt" else "npx",
                        "--yes",
                        "@modelcontextprotocol/inspector@2.8.0",
                        "--cli",
                        "--config",
                        str(config),
                        "--server",
                        "owned",
                        "--method",
                        method,
                        "--format",
                        "json",
                        *extra,
                    ]
                    result = subprocess.run(
                        command, capture_output=True, text=True, cwd=ROOT, timeout=60
                    )
                    (state / f"inspector-{method.replace('/', '-')}.log").write_text(
                        result.stdout + result.stderr
                    )
                    if result.returncode:
                        raise RuntimeError("Inspector failed; inspect ignored private evidence")
                    payload = json.loads(result.stdout)["result"]
                    if method == "tools/list":
                        names = {tool["name"] for tool in payload["tools"]}
                        if names != set(READ_OPERATIONS) | set(WRITE_OPERATIONS):
                            raise RuntimeError("Inspector catalog does not match current tools")
                    elif (
                        payload.get("isError")
                        or not json.loads(payload["content"][0]["text"])["items"]
                    ):
                        raise RuntimeError("Inspector project call did not return visible data")
                evidence["inspector"] = "passed"
                browser_input = state / "browser-input.json"
                browser_input.write_text(
                    json.dumps(
                        {
                            "url": metadata["content_url"],
                            "key": key,
                            "origin": URL,
                            "state": str(state),
                        }
                    )
                )
                browser = subprocess.run(
                    ["node", str(ROOT / "tools/testing/browser_check.mjs"), str(browser_input)],
                    capture_output=True,
                    text=True,
                    cwd=ROOT,
                    timeout=45,
                )
                (state / "browser.log").write_text(browser.stdout + browser.stderr)
                if browser.returncode:
                    raise RuntimeError(
                        "Browser verification failed; inspect ignored private evidence"
                    )
                evidence["browser"] = "passed"
        finally:
            if attachment_id is not None:
                with httpx.Client(
                    base_url=URL,
                    trust_env=False,
                    headers={"X-Redmine-API-Key": manifest["users"]["admin"]["key"]},
                ) as admin:
                    response = admin.delete(f"/attachments/{attachment_id}.json")
                    evidence["cleanup"] = (
                        "passed" if response.status_code in (204, 404) else "failed"
                    )
            server.terminate()
            server.wait(timeout=15)
            (state / "supplement-evidence.json").write_text(json.dumps(evidence, indent=2))
    if any(value != "passed" for value in evidence.values()):
        raise RuntimeError("Supplemental acceptance or owned cleanup did not pass")
    print("Inspector discovery/call, authenticated browser attachment, and owned cleanup passed.")


if __name__ == "__main__":
    main()
