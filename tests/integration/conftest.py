"""A stateful fake Redmine for complete reader and writer boundary checks."""

import copy
import json
from contextlib import asynccontextmanager
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import httpx
import pytest
import pytest_asyncio

from redmine_mcp.app import create_app
from redmine_mcp.auth import WRITE_OPERATIONS
from redmine_mcp.auth.capabilities import OPERATION_PERMISSIONS
from redmine_mcp.config import Settings
from tests.helpers import ISSUE, PROJECT
from tests.membership_helpers import membership


class SyntheticRedmine:
    def __init__(self) -> None:
        self.requests = []
        self.issues = {
            42: {
                **copy.deepcopy(ISSUE),
                "journals": [
                    {
                        "id": 1,
                        "user": {"id": 3, "name": "Writer"},
                        "notes": "original",
                        "created_on": "2026-10-05T00:00:00Z",
                        "private_notes": False,
                        "details": [],
                    }
                ],
                "watchers": [],
                "relations": [],
                "attachments": [],
            },
            43: {
                **copy.deepcopy(ISSUE),
                "id": 43,
                "journals": [],
                "relations": [],
                "watchers": [],
                "attachments": [],
            },
        }
        self.attachment = {
            "id": 9,
            "filename": "sample.txt",
            "filesize": 1,
            "content_type": "text/plain",
            "description": "original",
            "content_url": "http://redmine.invalid/attachments/download/9/sample.txt",
            "created_on": "2026-10-05T00:00:00Z",
            "author": {"id": 3, "name": "Writer"},
        }
        self.files = [self.attachment]
        self.attachment.update(digest="synthetic-digest", downloads=0)
        self.relation = {
            "id": 1,
            "issue_id": 42,
            "issue_to_id": 43,
            "relation_type": "relates",
            "delay": None,
        }
        self.permissions = sorted(
            set().union(*OPERATION_PERMISSIONS.values())
            | {
                "view_issues",
                "view_files",
                "view_time_entries",
                "view_issue_watchers",
                "set_notes_private",
            }
        )
        self.write_failure = None
        self.versions = {}
        self.readback_failure = False
        self.writes = 0
        self.members = {20: membership(), 21: membership(21, user_id=11)}
        self.protected_roles: set[int] = set()
        self.time_entries = [
            {
                "id": 1,
                "project": {"id": 7, "name": "Demo"},
                "user": {"id": 3, "name": "Writer"},
                "issue": {"id": 42},
                "hours": 0.1,
                "spent_on": "2026-09-01",
                "activity": {"id": 9, "name": "Development"},
                "comments": "original time",
            },
            {
                "id": 2,
                "project": {"id": 7, "name": "Demo"},
                "user": {"id": 8, "name": "Reader"},
                "hours": 0.2,
                "spent_on": "2026-09-30",
            },
        ]
        self.own_time_entries_only = False

    async def respond(self, request: Any) -> Any:
        self.requests.append(request)
        key = request.headers.get("X-Redmine-API-Key")
        if key not in ("offline-redmine-key", "offline-reader-key", "offline-rotated-key"):
            return httpx.Response(401, json={})
        uid, role_id = (8, 5) if key == "offline-reader-key" else (3, 4)
        path = request.url.path
        if path == "/users/current.json":
            return httpx.Response(
                200,
                json={
                    "user": {
                        "id": uid,
                        "login": "offline",
                        "firstname": "Offline",
                        "lastname": "User",
                        "admin": False,
                        "memberships": [
                            {
                                "id": 1,
                                "project": {"id": 7, "name": "Demo"},
                                "roles": [{"id": role_id, "name": "Role"}],
                            }
                        ],
                    }
                },
            )
        if path.startswith("/roles/"):
            return httpx.Response(
                200,
                json={
                    "role": {
                        "id": int(path.split("/")[2].split(".")[0]),
                        "permissions": self.permissions if role_id == 4 else [],
                    }
                },
            )
        if path == "/roles.json":
            return httpx.Response(
                200, json={"roles": [{"id": n, "name": f"Role {n}"} for n in (4, 5, 6)]}
            )
        if path.startswith("/users/") and path != "/users/current.json":
            user_id = int(path.split("/")[2].split(".")[0])
            return httpx.Response(
                200,
                json={
                    "user": {
                        "id": user_id,
                        "memberships": [
                            {k: copy.deepcopy(m[k]) for k in ("id", "project", "roles")}
                            for m in self.members.values()
                            if m.get("user", {}).get("id") == user_id
                        ],
                    }
                },
            )
        if request.method != "GET":
            self.writes += 1
            if self.write_failure is not None:
                if isinstance(self.write_failure, Exception):
                    raise self.write_failure
                return httpx.Response(self.write_failure, json={"secret": "must-not-leak"})
            payload = (
                json.loads(request.content)
                if request.content and request.headers.get("content-type") == "application/json"
                else {}
            )
            if path.startswith("/time_entries/") and request.method == "DELETE":
                entry_id = int(path.split("/")[2].split(".")[0])
                entry = next((row for row in self.time_entries if row["id"] == entry_id), None)
                if entry is None:
                    return httpx.Response(404)
                self.time_entries.remove(entry)
                return httpx.Response(204)
            if path.startswith("/time_entries/") and request.method == "PUT":
                entry_id = int(path.split("/")[2].split(".")[0])
                entry = next((row for row in self.time_entries if row["id"] == entry_id), None)
                if entry is None:
                    return httpx.Response(404)
                changes = payload["time_entry"].copy()
                if "activity_id" in changes:
                    activity_id = changes.pop("activity_id")
                    if activity_id not in (9, 10):
                        return httpx.Response(422, json={"errors": ["must-not-leak"]})
                    changes["activity"] = {"id": activity_id, "name": "Activity"}
                if "hours" in changes:
                    minutes = (Decimal(str(changes["hours"])) * 60).quantize(
                        Decimal("1"), rounding=ROUND_HALF_UP
                    )
                    changes["hours"] = float(
                        (minutes / 60).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    )
                entry.update(changes)
                return httpx.Response(204)
            if path == "/projects/7/memberships.json":
                values = payload["membership"]
                if any(
                    m.get("user", {}).get("id") == values["user_id"] for m in self.members.values()
                ):
                    return httpx.Response(422, json={"errors": ["must-not-leak"]})
                member_id = max(self.members, default=19) + 1
                member = membership(member_id, user_id=values["user_id"])
                member["roles"] = [{"id": n, "name": f"Role {n}"} for n in values["role_ids"]]
                self.members[member_id] = member
                return httpx.Response(201, json={"membership": copy.deepcopy(member)})
            if path.startswith("/memberships/"):
                member_id = int(path.split("/")[2].split(".")[0])
                if request.method == "DELETE":
                    self.members.pop(member_id, None)
                else:
                    member = self.members[member_id]
                    roles = set(payload["membership"]["role_ids"]) | {
                        r["id"]
                        for r in member["roles"]
                        if r.get("inherited") or r["id"] in self.protected_roles
                    }
                    old_roles = {r["id"]: r for r in member["roles"]}
                    member["roles"] = [
                        old_roles.get(n, {"id": n, "name": f"Role {n}"}) for n in sorted(roles)
                    ]
                return httpx.Response(204)
            if path == "/uploads.json":
                return httpx.Response(201, json={"upload": {"id": 9, "token": "9.abc"}})
            if path == "/projects/7/files.json":
                self.attachment.update(
                    {k: v for k, v in payload["file"].items() if k in ("filename", "description")}
                )
                return httpx.Response(204)
            if path == "/projects/7/versions.json":
                if any(v["name"] == payload["version"]["name"] for v in self.versions.values()):
                    return httpx.Response(422, json={"errors": ["must-not-leak"]})
                version_id = 100 + len(self.versions)
                version = {
                    "id": version_id,
                    "project": {"id": 7, "name": "Demo"},
                    "description": "",
                    "due_date": None,
                    **payload["version"],
                }
                self.versions[version_id] = version
                return httpx.Response(201, json={"version": version})
            if path == "/attachments/9.json":
                if request.method == "DELETE":
                    self.files = []
                else:
                    self.attachment.update(payload["attachment"])
                return httpx.Response(204)
            if path == "/issues.json":
                self.issues[44] = {**copy.deepcopy(ISSUE), "id": 44, **payload["issue"]}
                self.apply_assignment(self.issues[44], payload["issue"], uid)
                return httpx.Response(201, json={"issue": {"id": 44}})
            if path == "/issues/42.json":
                changes = payload["issue"].copy()
                note = changes.pop("notes", None)
                self.issues[42].update(changes)
                self.apply_assignment(self.issues[42], changes, uid)
                if note is not None:
                    self.issues[42]["journals"].append(
                        {
                            "id": 2,
                            "user": {"id": uid, "name": "Writer"},
                            "notes": note,
                            "created_on": "2026-10-05T00:00:00Z",
                            "private_notes": changes.get("private_notes", False),
                            "details": [],
                        }
                    )
                return httpx.Response(204)
            if path == "/journals/1.json":
                self.issues[42]["journals"][0].update(payload["journal"])
                return httpx.Response(204)
            if path == "/issues/42/relations.json":
                from redmine_mcp.features.issues.write_models import IssueRelationCreateRequest
                from redmine_mcp.integrations.redmine.issue_relations import expected_relation

                self.relation = {
                    "id": 1,
                    **expected_relation(42, IssueRelationCreateRequest(**payload["relation"])),
                }
                for issue in self.issues.values():
                    if issue["id"] in (42, 43):
                        issue["relations"] = [self.relation]
                return httpx.Response(201, json={"relation": self.relation})
            if path == "/relations/1.json":
                for issue in self.issues.values():
                    issue["relations"] = []
                return httpx.Response(204)
            if path.startswith("/issues/42/watchers"):
                self.issues[42]["watchers"] = (
                    [{"id": 3, "name": "Writer"}] if request.method == "POST" else []
                )
                return httpx.Response(204)
            return httpx.Response(404, json={})
        if self.readback_failure and self.writes:
            return httpx.Response(403, json={})
        if path == "/projects/7/memberships.json":
            limit = int(request.url.params.get("limit", 25))
            offset = int(request.url.params.get("offset", 0))
            members = list(self.members.values())
            return httpx.Response(
                200,
                json={
                    "memberships": members[offset : offset + limit],
                    "total_count": len(members),
                    "limit": limit,
                    "offset": offset,
                },
            )
        if path.startswith("/memberships/"):
            member_id = int(path.split("/")[2].split(".")[0])
            return (
                httpx.Response(200, json={"membership": copy.deepcopy(self.members[member_id])})
                if member_id in self.members
                else httpx.Response(404)
            )
        if path == "/projects.json":
            return httpx.Response(
                200,
                json={
                    "projects": [PROJECT],
                    "total_count": 1,
                    "limit": int(request.url.params.get("limit", 25)),
                    "offset": int(request.url.params.get("offset", 0)),
                },
            )
        if path == "/projects/7.json":
            project = copy.deepcopy(PROJECT)
            if request.url.params.get("include") == "time_entry_activities":
                project["time_entry_activities"] = [
                    {"id": 9, "name": "Development", "active": True},
                    {"id": 10, "name": "Review", "active": True},
                ]
            return httpx.Response(200, json={"project": project})
        if path.startswith("/versions/"):
            version_id = int(path.split("/")[2].split(".")[0])
            return (
                httpx.Response(200, json={"version": self.versions[version_id]})
                if version_id in self.versions
                else httpx.Response(404)
            )
        if path == "/issues.json":
            return httpx.Response(200, json={"issues": [self.issues[42]], "total_count": 1})
        if path.startswith("/issues/") and path.endswith(".json"):
            issue_id = int(path.split("/")[2].split(".")[0])
            return (
                httpx.Response(200, json={"issue": self.issues[issue_id]})
                if issue_id in self.issues
                else httpx.Response(404)
            )
        if path == "/attachments/9.json":
            return httpx.Response(200, json={"attachment": self.attachment})
        if path == "/relations/1.json":
            return httpx.Response(200, json={"relation": self.relation})
        if path.startswith("/time_entries/"):
            entry_id = int(path.split("/")[2].split(".")[0])
            entry = next((row for row in self.time_entries if row["id"] == entry_id), None)
            if entry is None:
                return httpx.Response(404)
            if self.own_time_entries_only and entry["user"]["id"] != uid:
                return httpx.Response(403)
            return httpx.Response(200, json={"time_entry": copy.deepcopy(entry)})
        if path == "/time_entries.json":
            params = request.url.params
            rows = self.time_entries
            if self.own_time_entries_only:
                rows = [row for row in rows if row["user"]["id"] == uid]
            for key, reference in [
                ("project_id", "project"),
                ("issue_id", "issue"),
                ("user_id", "user"),
            ]:
                if key in params:
                    value = uid if params[key] == "me" else int(params[key])
                    rows = [row for row in rows if row.get(reference, {}).get("id") == value]
            if "from" in params:
                rows = [row for row in rows if row["spent_on"] >= params["from"]]
            if "to" in params:
                rows = [row for row in rows if row["spent_on"] <= params["to"]]
            rows = sorted(rows, key=lambda row: (row["spent_on"], row["id"]))
            limit, offset = int(params.get("limit", 25)), int(params.get("offset", 0))
            return httpx.Response(
                200,
                json={
                    "time_entries": rows[offset : offset + limit],
                    "total_count": len(rows),
                    "limit": limit,
                    "offset": offset,
                },
            )
        collections = {
            "/projects/7/files.json": ("files", self.files),
            "/projects/7/versions.json": ("versions", list(self.versions.values())),
            "/projects/7/issue_categories.json": ("issue_categories", []),
            "/issue_statuses.json": ("issue_statuses", []),
            "/trackers.json": ("trackers", []),
            "/enumerations/issue_priorities.json": ("issue_priorities", []),
            "/enumerations/document_categories.json": ("document_categories", []),
        }
        if path in collections:
            name, items = collections[path]
            data = {name: items, "total_count": len(items)}
            if name == "time_entries":
                data.update(
                    limit=int(request.url.params.get("limit", 25)),
                    offset=int(request.url.params.get("offset", 0)),
                )
            return httpx.Response(200, json=data)
        return httpx.Response(404, json={})

    @staticmethod
    def apply_assignment(issue: Any, changes: Any, caller_id: int) -> None:
        if "assigned_to_id" not in changes or changes["assigned_to_id"] is None:
            return  # Native 7.0.2 ignores JSON null; empty string explicitly clears.
        value = changes["assigned_to_id"]
        issue.pop("assigned_to_id", None)
        if value == "":
            issue.pop("assigned_to", None)
        else:
            issue["assigned_to"] = {
                "id": caller_id if value == "me" else value,
                "name": "Assigned user",
            }


@pytest.fixture
def synthetic() -> Any:
    return SyntheticRedmine()


@pytest.fixture
def application_factory(monkeypatch: Any, synthetic: Any) -> Any:
    @asynccontextmanager
    async def factory(**overrides: Any) -> Any:
        settings = Settings(_env_file=None, redmine_url="http://redmine.invalid", **overrides)
        import asyncio

        from redmine_mcp.integrations.redmine.transport import AdmittedTransport

        async def streamed(request: Any) -> Any:
            response = await synthetic.respond(request)
            return httpx.Response(
                response.status_code,
                headers=response.headers,
                stream=httpx.ByteStream(response.content),
            )

        http = httpx.AsyncClient(
            base_url="http://redmine.invalid/",
            transport=AdmittedTransport(
                httpx.MockTransport(streamed),
                asyncio.Semaphore(settings.redmine_max_concurrent_requests),
                settings.redmine_admission_timeout_seconds,
            ),
        )
        monkeypatch.setattr("redmine_mcp.lifecycle.create_upstream_client", lambda settings: http)
        app = create_app(settings)
        async with app.router.lifespan_context(app):
            yield app
        assert http.is_closed

    return factory


@pytest_asyncio.fixture
async def writer_app(application_factory: Any) -> Any:
    async with application_factory(
        redmine_write_enabled=True,
        redmine_writer_operations=",".join(WRITE_OPERATIONS),
    ) as app:
        yield app
