"""Deterministic synthetic data writer; never used by the read-only application."""

import base64
import json
import os
from pathlib import Path

import httpx

STATE = Path("/seed-state")
KIND = "redmine-mcp-synthetic-v1"


def save(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    if os.environ.get("REDMINE_TEST_MARKER") != KIND:
        raise SystemExit("Missing synthetic environment marker")
    if json.loads((STATE / "environment.json").read_text())["kind"] != KIND:
        raise SystemExit("Wrong environment")
    manifest_path = STATE / "manifest.json"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("status") == "complete":
            print("Dataset already complete; skipped. Use reset-test-env.sh to regenerate.")
            return
        raise SystemExit("Incomplete seed found. Reset the dedicated test environment first.")
    credentials = json.loads((STATE / "credentials.json").read_text())
    manifest = {
        "kind": KIND,
        "status": "in_progress",
        "projects": {},
        "issues": [],
        "hidden_issues": [],
        "private_journals": [],
        "attachments": [],
    }
    save(manifest_path, manifest)

    with httpx.Client(
        base_url=os.environ["REDMINE_URL"].rstrip("/") + "/",
        headers={"X-Redmine-API-Key": credentials["admin_key"]},
        timeout=30,
    ) as client:

        def call(method: str, path: str, **kwargs):
            response = client.request(method, path, **kwargs)
            if response.is_error or response.is_redirect:
                # No upstream response dump: it may contain credentials or issue content.
                raise RuntimeError(f"Seed request failed: {method} {path} ({response.status_code})")
            return response.json() if response.content else {}

        trackers = call("GET", "trackers.json")["trackers"]
        statuses = call("GET", "issue_statuses.json")["issue_statuses"]
        priorities = call("GET", "enumerations/issue_priorities.json")["issue_priorities"]
        open_status = next(s["id"] for s in statuses if not s["is_closed"])
        closed_status = next(s["id"] for s in statuses if s["is_closed"])
        for key, name in [
            ("main", "Demo Việt Nam"),
            ("child", "Demo API"),
            ("empty", "Demo Empty"),
            ("restricted", "Demo Restricted"),
        ]:
            project = {
                "name": name,
                "identifier": f"mcp-demo-{key}",
                "is_public": False,
                "enabled_module_names": ["issue_tracking"],
                "tracker_ids": [t["id"] for t in trackers],
            }
            if key == "child":
                project["parent_id"] = manifest["projects"]["main"]
                project["inherit_members"] = False
            result = call("POST", "projects.json", json={"project": project})["project"]
            pid = result["id"]
            manifest["projects"][key] = pid
            for username, role in [
                ("manager", "manager"),
                ("developer", "developer"),
                ("reporter", "reporter"),
                ("mcp-reader", "reader"),
            ]:
                if key == "restricted" and username == "mcp-reader":
                    continue
                call(
                    "POST",
                    f"projects/{pid}/memberships.json",
                    json={
                        "membership": {
                            "user_id": credentials["users"][username],
                            "role_ids": [credentials["roles"][role]],
                        }
                    },
                )
            save(manifest_path, manifest)

        fields = credentials["custom_fields"]
        for index in range(150):
            project_key = "main" if index < 110 else ("child" if index < 130 else "restricted")
            private = index in (5, 115)
            issue = {
                "project_id": manifest["projects"][project_key],
                "subject": f"[DEMO-{index + 1:03d}] Kiểm tra chức năng Redmine",
                "description": ""
                if index % 10 == 0
                else ("Dữ liệu mẫu tiếng Việt. " * (200 if index == 1 else 2)),
                "tracker_id": trackers[index % len(trackers)]["id"],
                "priority_id": priorities[index % len(priorities)]["id"],
                "status_id": open_status,
                "is_private": private,
                "custom_fields": [
                    {"id": fields[0]["id"], "value": "Docker local"},
                    {"id": fields[1]["id"], "value": "stable" if index % 2 else "beta"},
                    {"id": fields[2]["id"], "value": ["api", "web"]},
                ],
            }
            if index % 3:
                issue["assigned_to_id"] = credentials["users"]["developer"]
            if index in (2, 3):
                issue["parent_issue_id"] = manifest["issues"][0]
            result = call("POST", "issues.json", json={"issue": issue})["issue"]
            iid = result["id"]
            manifest["issues"].append(iid)
            if private or project_key == "restricted":
                manifest["hidden_issues"].append(iid)
            if index < 12:
                call(
                    "PUT",
                    f"issues/{iid}.json",
                    json={
                        "issue": {
                            "notes": "Bình luận công khai để kiểm tra MCP.",
                            "done_ratio": 30,
                        }
                    },
                )
                call(
                    "PUT",
                    f"issues/{iid}.json",
                    json={
                        "issue": {
                            "notes": "Ghi chú nội bộ chỉ dành cho quản lý.",
                            "private_notes": True,
                        }
                    },
                )
                manifest["private_journals"].append(iid)
            if index % 4 == 0 and index != 0:
                call(
                    "PUT",
                    f"issues/{iid}.json",
                    json={
                        "issue": {
                            "status_id": closed_status,
                            "notes": "Đã hoàn thành công việc mẫu.",
                        }
                    },
                )
            save(manifest_path, manifest)
            if (index + 1) % 25 == 0:
                print(f"Created {index + 1}/150 issues", flush=True)
        call(
            "POST",
            f"issues/{manifest['issues'][6]}/relations.json",
            json={
                "relation": {
                    "issue_to_id": manifest["issues"][7],
                    "relation_type": "relates",
                }
            },
        )
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aF1sAAAAASUVORK5CYII="
        )
        for filename, body, content_type in [
            ("sample.txt", "Tệp mẫu Redmine MCP".encode(), "text/plain"),
            ("sample.png", png, "image/png"),
        ]:
            uploaded = call(
                "POST",
                f"uploads.json?filename={filename}",
                content=body,
                headers={"Content-Type": "application/octet-stream"},
            )
            call(
                "PUT",
                f"issues/{manifest['issues'][0]}.json",
                json={
                    "issue": {
                        "uploads": [
                            {
                                "token": uploaded["upload"]["token"],
                                "filename": filename,
                                "content_type": content_type,
                            }
                        ]
                    }
                },
            )
            manifest["attachments"].append(filename)
        manifest["status"] = "complete"
        manifest["visible_issue_count"] = 128
        save(manifest_path, manifest)
        print("Synthetic dataset complete. Manifest saved; credentials not printed.")


if __name__ == "__main__":
    main()
