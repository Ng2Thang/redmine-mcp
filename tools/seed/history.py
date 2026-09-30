"""Add a repeatable, dated fixture to the marked synthetic Redmine instance."""

import fcntl
import json
import os
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from tools.seed.generator import KIND, STATE, save

MANIFEST_PATH = STATE / "history-manifest.json"
PROJECTS = (
    ("alpha", "History Alpha", None),
    ("alpha-api", "History Alpha API", "alpha"),
    ("alpha-web", "History Alpha Web", "alpha"),
    ("alpha-ops", "History Alpha Operations", "alpha"),
    ("beta", "History Beta", None),
    ("beta-api", "History Beta API", "beta"),
    ("beta-web", "History Beta Web", "beta"),
    ("beta-private", "History Beta Private", "beta"),
)
PROJECT_KEYS = tuple(project[0] for project in PROJECTS)


class Redmine:
    def __init__(self, api_key: str) -> None:
        self.client = httpx.Client(
            base_url=os.environ["REDMINE_URL"].rstrip("/") + "/",
            headers={"X-Redmine-API-Key": api_key},
            timeout=30,
        )

    def __enter__(self) -> "Redmine":
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()

    def call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self.client.request(method, path, **kwargs)
        if response.is_error or response.is_redirect:
            raise RuntimeError(
                f"History seed request failed: {method} {path} ({response.status_code})"
            )
        return response.json() if response.content else {}

    def all(
        self, path: str, key: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = self.call("GET", path, params={**(params or {}), "limit": 100, "offset": offset})
            items = page[key]
            result.extend(items)
            total = page.get("total_count", len(result))
            if len(result) >= total or not items:
                return result
            offset += len(items)


def checkpoint(manifest: dict[str, Any]) -> None:
    save(MANIFEST_PATH, manifest)


def inspect_existing(redmine: Redmine, manifest: dict[str, Any]) -> dict[str, Any]:
    """Recover a create that succeeded immediately before its checkpoint was written."""
    remote: dict[str, Any] = {}
    remote["users"] = {
        user["login"]: user["id"] for user in redmine.all("users.json", "users", {"status": 1})
    }
    remote["projects"] = {
        project["identifier"]: project["id"] for project in redmine.all("projects.json", "projects")
    }
    remote["versions"] = {}
    remote["memberships"] = {}
    remote["issues"] = {}
    remote["time_entries"] = {}
    for key, _, parent in PROJECTS:
        project_id = manifest["projects"].get(key) or remote["projects"].get(f"mcp-history-{key}")
        if not project_id:
            continue
        remote["memberships"][key] = {
            membership["user"]["id"]: membership["id"]
            for membership in redmine.all(f"projects/{project_id}/memberships.json", "memberships")
        }
        remote["issues"][key] = {
            issue["subject"]: issue["id"]
            for issue in redmine.all(
                "issues.json", "issues", {"project_id": project_id, "status_id": "*"}
            )
        }
        remote["time_entries"][key] = {
            entry["comments"]: entry["id"]
            for entry in redmine.all(
                "time_entries.json", "time_entries", {"project_id": project_id}
            )
            if entry.get("comments", "").startswith("History fixture ")
        }
        if parent is None:
            remote["versions"][key] = {
                version["name"]: version["id"]
                for version in redmine.all(f"projects/{project_id}/versions.json", "versions")
                if version["project"]["id"] == project_id
            }
    return remote


def ensure_projects(redmine: Redmine, manifest: dict[str, Any], remote: dict[str, Any]) -> None:
    for key, name, parent in PROJECTS:
        if key in manifest["projects"]:
            continue
        identifier = f"mcp-history-{key}"
        project_id = remote.get("projects", {}).get(identifier)
        if project_id is None:
            payload: dict[str, Any] = {
                "name": name,
                "identifier": identifier,
                "is_public": False,
                "inherit_members": False,
                "enabled_module_names": ["issue_tracking", "time_tracking"],
                "description": "Synthetic history for manual Redmine and MCP checks.",
            }
            if parent is not None:
                payload["parent_id"] = manifest["projects"][parent]
            project_id = redmine.call("POST", "projects.json", json={"project": payload})[
                "project"
            ]["id"]
        manifest["projects"][key] = project_id
        checkpoint(manifest)


def ensure_users(
    redmine: Redmine, manifest: dict[str, Any], remote: dict[str, Any], password: str
) -> None:
    for number in range(1, 21):
        login = f"history-user-{number:02d}"
        if login in manifest["users"]:
            continue
        user_id = remote.get("users", {}).get(login)
        if user_id is None:
            user_id = redmine.call(
                "POST",
                "users.json",
                json={
                    "user": {
                        "login": login,
                        "firstname": "History",
                        "lastname": f"User {number:02d}",
                        "mail": f"history.user.{number:02d}@example.invalid",
                        "password": password,
                        "password_confirmation": password,
                        "mail_notification": "none",
                    }
                },
            )["user"]["id"]
        manifest["users"][login] = user_id
        checkpoint(manifest)


def ensure_memberships(
    redmine: Redmine,
    manifest: dict[str, Any],
    remote: dict[str, Any],
    roles: dict[str, int],
    reader_id: int,
) -> None:
    for project_index, key in enumerate(PROJECT_KEYS):
        cohort = 0 if project_index < 4 else 10
        members = [
            (f"history-user-{number:02d}", number) for number in range(cohort + 1, cohort + 11)
        ]
        if key != "beta-private":
            members.append(("mcp-reader", 0))
        for login, number in members:
            member_key = f"{key}:{login}"
            if member_key in manifest["memberships"]:
                continue
            user_id = reader_id if number == 0 else manifest["users"][login]
            membership_id = remote.get("memberships", {}).get(key, {}).get(user_id)
            if membership_id is None:
                position = (number - 1) % 10
                role = (
                    "reader"
                    if number == 0
                    else (
                        "manager" if position == 0 else "reporter" if position == 9 else "developer"
                    )
                )
                membership_id = redmine.call(
                    "POST",
                    f"projects/{manifest['projects'][key]}/memberships.json",
                    json={"membership": {"user_id": user_id, "role_ids": [roles[role]]}},
                )["membership"]["id"]
            manifest["memberships"][member_key] = membership_id
            checkpoint(manifest)


def sprint_dates(anchor: date, sprint_index: int) -> tuple[date, date]:
    start = anchor - timedelta(days=90 - sprint_index * 15)
    return start, start + timedelta(days=14)


def ensure_versions(redmine: Redmine, manifest: dict[str, Any], remote: dict[str, Any]) -> None:
    anchor = date.fromisoformat(manifest["anchor_date"])
    for root in ("alpha", "beta"):
        for sprint_index in range(6):
            version_key = f"{root}:{sprint_index + 1:02d}"
            if version_key in manifest["versions"]:
                continue
            name = f"History Sprint {sprint_index + 1:02d}"
            version_id = remote.get("versions", {}).get(root, {}).get(name)
            if version_id is None:
                start, end = sprint_dates(anchor, sprint_index)
                version_id = redmine.call(
                    "POST",
                    f"projects/{manifest['projects'][root]}/versions.json",
                    json={
                        "version": {
                            "name": name,
                            "description": f"Sprint {start.isoformat()} to {end.isoformat()}",
                            "due_date": end.isoformat(),
                            "sharing": "descendants",
                            "status": "open",
                        }
                    },
                )["version"]["id"]
            manifest["versions"][version_key] = version_id
            checkpoint(manifest)


def issue_details(index: int, manifest: dict[str, Any]) -> tuple[str, int, int, date, date]:
    project_key = PROJECT_KEYS[index % 8]
    root = "alpha" if index % 8 < 4 else "beta"
    sprint_index = (index // 8) % 6
    start, end = sprint_dates(date.fromisoformat(manifest["anchor_date"]), sprint_index)
    return (
        project_key,
        manifest["versions"][f"{root}:{sprint_index + 1:02d}"],
        sprint_index,
        start,
        end,
    )


def ensure_issues(
    redmine: Redmine,
    manifest: dict[str, Any],
    remote: dict[str, Any],
    trackers: list[dict[str, Any]],
    statuses: list[dict[str, Any]],
    priorities: list[dict[str, Any]],
) -> None:
    open_status = next(status["id"] for status in statuses if not status["is_closed"])
    closed_status = next(status["id"] for status in statuses if status["is_closed"])
    for index in range(300):
        issue_key = f"{index + 1:03d}"
        if issue_key in manifest["issues"]:
            continue
        project_key, version_id, _, start, end = issue_details(index, manifest)
        subject = f"[HISTORY-{issue_key}] {('Build', 'Review', 'Fix', 'Document')[index % 4]} work"
        issue_id = remote.get("issues", {}).get(project_key, {}).get(subject)
        if issue_id is None:
            cohort = 0 if index % 8 < 4 else 10
            assignee = manifest["users"][f"history-user-{cohort + 2 + (index % 8):02d}"]
            issue_id = redmine.call(
                "POST",
                "issues.json",
                json={
                    "issue": {
                        "project_id": manifest["projects"][project_key],
                        "subject": subject,
                        "description": "Synthetic scheduled work for manual history checks.",
                        "tracker_id": trackers[index % len(trackers)]["id"],
                        "priority_id": priorities[index % len(priorities)]["id"],
                        "status_id": closed_status if index % 4 == 0 else open_status,
                        "fixed_version_id": version_id,
                        "assigned_to_id": assignee,
                        "start_date": (start + timedelta(days=1)).isoformat(),
                        "due_date": end.isoformat(),
                        "estimated_hours": (8, 12, 16, 24)[index % 4],
                        "done_ratio": 100 if index % 4 == 0 else (30 if index % 3 == 0 else 0),
                    }
                },
            )["issue"]["id"]
        manifest["issues"][issue_key] = issue_id
        checkpoint(manifest)
        if (index + 1) % 50 == 0:
            print(f"History issues: {index + 1}/300", flush=True)


def ensure_time_entries(
    redmine: Redmine,
    manifest: dict[str, Any],
    remote: dict[str, Any],
    activities: list[dict[str, Any]],
) -> None:
    for issue_index in range(300):
        issue_key = f"{issue_index + 1:03d}"
        project_key, _, _, start, _ = issue_details(issue_index, manifest)
        cohort = 0 if issue_index % 8 < 4 else 10
        for entry_index in range(3):
            entry_key = f"{issue_key}-{entry_index + 1}"
            if entry_key in manifest["time_entries"]:
                continue
            comment = f"History fixture {entry_key}"
            entry_id = remote.get("time_entries", {}).get(project_key, {}).get(comment)
            if entry_id is None:
                worker = cohort + 2 + ((issue_index + entry_index) % 8)
                entry_id = redmine.call(
                    "POST",
                    "time_entries.json",
                    json={
                        "time_entry": {
                            "issue_id": manifest["issues"][issue_key],
                            "user_id": manifest["users"][f"history-user-{worker:02d}"],
                            "spent_on": (
                                start + timedelta(days=(2, 6, 10)[entry_index])
                            ).isoformat(),
                            "hours": (1.0, 1.5, 2.0)[entry_index],
                            "activity_id": activities[
                                (issue_index + entry_index) % len(activities)
                            ]["id"],
                            "comments": comment,
                        }
                    },
                )["time_entry"]["id"]
            manifest["time_entries"][entry_key] = entry_id
            checkpoint(manifest)
        if (issue_index + 1) % 50 == 0:
            print(f"History time entries: {(issue_index + 1) * 3}/900", flush=True)


def main() -> None:
    if os.environ.get("REDMINE_TEST_MARKER") != KIND:
        raise SystemExit("Missing synthetic environment marker")
    if json.loads((STATE / "environment.json").read_text(encoding="utf-8"))["kind"] != KIND:
        raise SystemExit("Wrong environment")
    base = json.loads((STATE / "manifest.json").read_text(encoding="utf-8"))
    if base.get("kind") != KIND or base.get("status") != "complete":
        raise SystemExit("Complete base synthetic seed required")
    password = os.environ["TEST_USER_PASSWORD"]
    if len(password) < 12:
        raise SystemExit("Synthetic user password must be at least 12 characters")
    credentials = json.loads((STATE / "credentials.json").read_text(encoding="utf-8"))
    with (STATE / "history-seed.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if MANIFEST_PATH.exists():
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            if manifest.get("kind") != KIND or manifest.get("base_projects") != base["projects"]:
                raise SystemExit("History manifest does not match this synthetic base dataset")
            if manifest.get("status") == "complete":
                print("History dataset already complete; skipped.")
                return
        else:
            manifest = {
                "kind": KIND,
                "status": "in_progress",
                "anchor_date": datetime.now(UTC).date().isoformat(),
                "base_projects": base["projects"],
                "projects": {},
                "users": {},
                "memberships": {},
                "versions": {},
                "issues": {},
                "time_entries": {},
            }
            checkpoint(manifest)
        with Redmine(credentials["admin_key"]) as redmine:
            remote = inspect_existing(redmine, manifest)
            trackers = redmine.call("GET", "trackers.json")["trackers"]
            statuses = redmine.call("GET", "issue_statuses.json")["issue_statuses"]
            priorities = redmine.call("GET", "enumerations/issue_priorities.json")[
                "issue_priorities"
            ]
            activities = redmine.call("GET", "enumerations/time_entry_activities.json")[
                "time_entry_activities"
            ]
            if not all((trackers, statuses, priorities, activities)):
                raise SystemExit("Required Redmine catalog is empty")
            ensure_projects(redmine, manifest, remote)
            ensure_users(redmine, manifest, remote, password)
            ensure_memberships(
                redmine, manifest, remote, credentials["roles"], credentials["users"]["mcp-reader"]
            )
            ensure_versions(redmine, manifest, remote)
            ensure_issues(redmine, manifest, remote, trackers, statuses, priorities)
            ensure_time_entries(redmine, manifest, remote, activities)
        manifest["status"] = "complete"
        checkpoint(manifest)
        print("History complete: 8 projects, 20 users, 12 versions, 300 issues, 900 time entries.")


if __name__ == "__main__":
    main()
