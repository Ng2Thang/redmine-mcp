"""Credential-free reader acceptance scenarios assigned by prep-004."""

import asyncio
import json
import logging
from decimal import Decimal
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from redmine_mcp.config import Settings
from redmine_mcp.features.issues import ISSUE_INCLUDES
from redmine_mcp.mcp.catalog import OPERATIONS
from tests.helpers import ISSUE, PROJECT, mcp_session
from tests.retry_helpers import RetryClock

pytestmark = pytest.mark.asyncio

PROFILE = {
    "id": 3,
    "login": "reader",
    "firstname": "Offline",
    "lastname": "Reader",
    "memberships": [],
}
MEMBERSHIP = {
    "id": 10,
    "project": {"id": 7, "name": "Demo"},
    "roles": [{"id": 4, "name": "Reporter"}],
}
ENTRY = {
    "id": 1,
    "project": {"id": 7, "name": "Demo"},
    "issue": {"id": 42},
    "user": {"id": 8, "name": "Credited"},
    "hours": 1.5,
    "spent_on": "2026-09-30",
}
LOOKUPS = [
    (
        "list_issue_statuses",
        "/api/v1/issue-statuses",
        "/issue_statuses.json",
        "issue_statuses",
        {"id": 1, "name": "New", "is_closed": False},
    ),
    (
        "list_trackers",
        "/api/v1/trackers",
        "/trackers.json",
        "trackers",
        {
            "id": 1,
            "name": "Bug",
            "default_status": {"id": 1, "name": "New"},
            "description": "Defects",
            "enabled_standard_fields": ["assigned_to_id"],
        },
    ),
    (
        "list_issue_priorities",
        "/api/v1/issue-priorities",
        "/enumerations/issue_priorities.json",
        "issue_priorities",
        {"id": 2, "name": "Normal", "is_default": True},
    ),
    (
        "list_project_versions",
        "/api/v1/projects/7/versions",
        "/projects/7/versions.json",
        "versions",
        {
            "id": 4,
            "name": "Sprint",
            "project": {"id": 7, "name": "Demo"},
            "status": "open",
            "description": "Release",
            "due_date": "2026-10-31",
        },
    ),
    (
        "list_project_issue_categories",
        "/api/v1/projects/7/issue-categories",
        "/projects/7/issue_categories.json",
        "issue_categories",
        {
            "id": 5,
            "name": "Backend",
            "project": {"id": 7, "name": "Demo"},
            "assigned_to": {"id": 8, "name": "Credited"},
        },
    ),
]
READ_ROUTES = [
    "/api/v1/time-entries",
    "/api/v1/issues/42",
    "/api/v1/projects/7",
    "/api/v1/issues",
    "/api/v1/issues/42/time-entries",
    *(row[1] for row in LOOKUPS),
]


def reader_responses() -> dict[str, Any]:
    return {
        "/projects/7/memberships.json": (
            200,
            {"memberships": [], "total_count": 0, "limit": 25, "offset": 0},
        ),
        "/projects/7/files.json": (200, {"files": [], "total_count": 0}),
        "/enumerations/document_categories.json": (200, {"document_categories": []}),
        "/attachments/9.json": (
            200,
            {
                "attachment": {
                    "id": 9,
                    "filename": "sample.txt",
                    "filesize": 1,
                    "content_url": "http://redmine.invalid/attachments/download/9/sample.txt",
                    "created_on": "2026-10-05T00:00:00Z",
                }
            },
        ),
        "/projects.json": (200, {"projects": [PROJECT], "total_count": 1}),
        "/projects/7.json": (200, {"project": PROJECT}),
        "/issues.json": (200, {"issues": [ISSUE], "total_count": 1}),
        "/issues/42.json": (200, {"issue": ISSUE}),
        "/time_entries.json": (
            200,
            {"time_entries": [ENTRY], "total_count": 1, "limit": 25, "offset": 0},
        ),
        **{
            path: (200, {collection: [item], "total_count": 1})
            for _, _, path, collection, item in LOOKUPS
        },
    }


@pytest.mark.parametrize("route", READ_ROUTES)
@pytest.mark.parametrize(
    ("status", "expected", "code"),
    [
        (401, 401, "invalid_credentials"),
        (403, 403, "access_denied"),
        (404, 404, "resource_not_found"),
        (429, 502, "upstream_rate_limited"),
        (503, 502, "upstream_unavailable"),
        (504, 504, "upstream_timeout"),
        (500, 502, "upstream_error"),
    ],
)
async def test_reader_error_contracts(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    monkeypatch: Any,
    route: str,
    status: int,
    expected: int,
    code: str,
) -> None:
    clock = RetryClock()
    monkeypatch.setattr("redmine_mcp.integrations.redmine.client.RetryRuntime", clock.runtime)
    upstream.update(status=status, body={"secret": "must-not-leak"})
    result = await rest_client.get(route)
    assert result.status_code == expected
    assert result.json()["error"]["code"] == code
    assert "must-not-leak" not in result.text
    attempts = 3 if status in (429, 503, 504) else 1
    requests = upstream["requests"]
    assert len(requests) == 1 + attempts
    assert requests[0].url.path == "/users/current.json"
    assert all(request.url == requests[1].url for request in requests[1:])


@pytest.mark.parametrize("route", READ_ROUTES)
async def test_reader_missing_auth_and_timeout(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    route: str,
) -> None:
    result = await rest_client.get(route, headers={"X-Redmine-API-Key": ""})
    assert result.status_code == 401
    assert upstream["requests"] == []
    upstream["exception"] = httpx.ReadTimeout("secret")
    result = await rest_client.get(route)
    assert result.status_code == 504
    assert result.json()["error"]["code"] == "upstream_timeout"


@pytest.mark.parametrize("lookup", LOOKUPS, ids=[row[0] for row in LOOKUPS])
async def test_lookup_complete_optional_fields_and_counts(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    lookup: tuple[Any, ...],
) -> None:
    _, route, path, collection, item = lookup
    upstream["responses"] = {path: (200, {collection: [item], "total_count": 1})}
    result = await rest_client.get(route)
    assert result.status_code == 200
    mapped = result.json()["items"][0]
    assert all(mapped[key] == value for key, value in item.items())
    assert result.json()["visibility"]["scope"] == "requesting_redmine_user"
    assert dict(upstream["requests"][-1].url.params) == {}
    if collection in {"versions", "issue_categories"}:
        for count in [None, True, "1", -1, 2]:
            upstream["responses"][path] = (200, {collection: [item], "total_count": count})
            invalid = await rest_client.get(route)
            assert invalid.status_code == 502
        upstream["responses"][path] = (200, {collection: [], "total_count": 0})
        assert (await rest_client.get(route)).json()["items"] == []


@pytest.mark.parametrize("lookup", LOOKUPS, ids=[row[0] for row in LOOKUPS])
@pytest.mark.parametrize("value", [None, {}, [None], [{}]])
async def test_lookup_invalid_shapes(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    lookup: tuple[Any, ...],
    value: Any,
) -> None:
    _, route, path, collection, _ = lookup
    upstream["responses"] = {path: (200, {collection: value, "total_count": 1})}
    result = await rest_client.get(route)
    assert result.status_code == 502
    assert result.json()["error"]["code"] == "upstream_response"


async def test_project_001_optional_fields_and_list_regression(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    upstream["responses"] = reader_responses()
    minimal = (await rest_client.get("/api/v1/projects/7")).json()
    assert minimal["is_public"] is None
    assert minimal["created_on"] is None
    extra = {
        "is_public": False,
        "description": "Private project",
        "parent": {"id": 2, "name": "Parent"},
        "created_on": "2026-09-01T00:00:00Z",
        "updated_on": "2026-09-30T00:00:00Z",
    }
    upstream["responses"]["/projects/7.json"] = (200, {"project": {**PROJECT, **extra}})
    result = await rest_client.get("/api/v1/projects/7")
    assert all(result.json()[key] == value for key, value in extra.items())
    assert (await rest_client.get("/api/v1/projects")).json()["items"][0]["id"] == 7
    upstream["responses"]["/projects/7.json"] = (200, {"project": {**PROJECT, "id": 8}})
    assert (await rest_client.get("/api/v1/projects/7")).status_code == 502


@pytest.mark.parametrize(
    "include", [None, "", *sorted(ISSUE_INCLUDES), ",".join(sorted(ISSUE_INCLUDES))]
)
async def test_detail_001_002_includes_and_nested_mapping(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    include: str | None,
) -> None:
    expansions = {
        "journals": [
            {
                "id": 5,
                "user": {"id": 3, "name": "Reader"},
                "notes": "Visible",
                "created_on": "2026-09-30T00:00:00Z",
                "private_notes": True,
                "details": [
                    {"property": "attr", "name": "status_id", "old_value": "1", "new_value": "2"}
                ],
            }
        ],
        "attachments": [
            {
                "id": 6,
                "filename": "report.txt",
                "filesize": 10,
                "created_on": "2026-09-30T00:00:00Z",
                "author": {"id": 3, "name": "Reader"},
            }
        ],
        "children": [
            {"id": 43, "subject": "Child", "children": [{"id": 44, "subject": "Grandchild"}]}
        ],
        "relations": [
            {"id": 7, "issue_id": 42, "issue_to_id": 45, "relation_type": "blocks", "delay": 1}
        ],
        "changesets": [{"revision": "abc", "comments": "Fix"}],
        "watchers": [{"id": 8, "name": "Watcher"}],
        "allowed_statuses": [{"id": 2, "name": "Closed", "is_closed": True}],
    }
    selected = (
        {"journals", "attachments"} if include is None else set(filter(None, include.split(",")))
    )
    upstream["responses"] = {
        "/issues/42.json": (
            200,
            {
                "issue": {
                    **ISSUE,
                    **{key: value for key, value in expansions.items() if key in selected},
                }
            },
        )
    }
    result = await rest_client.get(
        "/api/v1/issues/42", params={} if include is None else {"include": include}
    )
    assert result.status_code == 200
    body = result.json()
    for field in ISSUE_INCLUDES:
        assert bool(body[field]) == (field in selected)
    query = dict(upstream["requests"][-1].url.params)
    assert query == (
        {"include": "journals,attachments"}
        if include is None
        else {"include": include}
        if include
        else {}
    )
    observations = {row["path"]: row["state"] for row in body["visibility"]["observations"]}
    for field in ISSUE_INCLUDES - selected:
        assert observations[f"/{field}"] == "not_requested"
    if "children" in selected:
        assert body["children"][0]["children"][0]["id"] == 44
    if "journals" in selected:
        assert body["journals"][0]["details"][0]["new_value"] == "2"


@pytest.mark.parametrize(
    ("route", "params"),
    [
        ("/api/v1/issues/0", {}),
        ("/api/v1/projects/0", {}),
        ("/api/v1/projects/0/versions", {}),
        ("/api/v1/projects/0/issue-categories", {}),
        ("/api/v1/issues/42", {"include": "journals,journals"}),
        ("/api/v1/issues/42", {"include": "unknown"}),
        ("/api/v1/issues", {"category_id": 1}),
        ("/api/v1/issues", {"project_id": 7, "category_id": 0}),
        ("/api/v1/issues", {"project_id": 7, "category_id": "invalid"}),
        ("/api/v1/issues", {"fixed_version_id": 0}),
        ("/api/v1/issues", {"fixed_version_id": "invalid"}),
        ("/api/v1/issues", {"include_subprojects": "false"}),
        ("/api/v1/issues", {"include_subprojects": "invalid"}),
        ("/api/v1/issues/42/time-entries", {"limit": 101}),
        ("/api/v1/issues/42/time-entries", {"offset": -1}),
    ],
)
async def test_invalid_reader_inputs_prevent_resource_dispatch(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    route: str,
    params: dict[str, Any],
) -> None:
    result = await rest_client.get(route, params=params)
    assert result.status_code == 422
    assert all(req.url.path == "/users/current.json" for req in upstream["requests"])


@pytest.mark.parametrize("include_subprojects", [None, True, False])
async def test_catissue_001_targetissue_001_exact_query_and_pagination(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    include_subprojects: bool | None,
) -> None:
    upstream["body"] = {"issues": [ISSUE], "total_count": 3, "limit": 1, "offset": 1}
    params = {
        "project_id": 7,
        "category_id": 5,
        "fixed_version_id": 4,
        "tracker_id": 1,
        "status_id": "*",
        "assigned_to_id": "me",
        "parent_id": 41,
        "sort": "updated_on:desc",
        "limit": 1,
        "offset": 1,
    }
    if include_subprojects is not None:
        params["include_subprojects"] = str(include_subprojects).lower()
    result = await rest_client.get("/api/v1/issues", params=params)
    assert result.status_code == 200
    assert (result.json()["total"], result.json()["limit"], result.json()["offset"]) == (3, 1, 1)
    expected = {key: str(value) for key, value in params.items() if key != "include_subprojects"}
    if include_subprojects is False:
        expected["subproject_id"] = "!*"
    assert dict(upstream["requests"][-1].url.params) == expected
    upstream["body"] = {"issues": [], "total_count": 3, "limit": 1, "offset": 4}
    result = await rest_client.get("/api/v1/issues", params={**params, "offset": 4})
    assert result.status_code == 200 and result.json()["items"] == []


@pytest.mark.parametrize("detail", [False, True])
@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("category", {"id": 5, "name": "Backend"}, 200),
        ("category", None, 200),
        ("category", {}, 502),
        ("fixed_version", {"id": 4, "name": "Sprint"}, 200),
        ("fixed_version", None, 200),
        ("fixed_version", {}, 502),
        ("start_date", "2026-09-01", 200),
        ("due_date", "2026-09-30", 200),
        ("start_date", None, 200),
        ("due_date", None, 200),
        ("start_date", "2026-02-30", 502),
        ("due_date", "not-date", 502),
        ("due_date", 123, 502),
        ("spent_hours", 1.5, 200),
        ("spent_hours", 0, 200),
        ("total_spent_hours", 2, 200),
        ("spent_hours", None, 200),
        ("spent_hours", -1, 502),
        ("total_spent_hours", "2", 502),
        ("spent_hours", True, 502),
    ],
)
async def test_issue_reference_schedule_and_hours_mapping(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    detail: bool,
    field: str,
    value: Any,
    expected: int,
) -> None:
    row = {**ISSUE, field: value}
    upstream["body"] = {"issue": row} if detail else {"issues": [row], "total_count": 1}
    result = await rest_client.get("/api/v1/issues/42" if detail else "/api/v1/issues")
    assert result.status_code == expected
    if expected == 200:
        mapped = result.json() if detail else result.json()["items"][0]
        assert mapped[field] == value
    else:
        assert result.json()["error"]["code"] == "upstream_response"


@pytest.mark.parametrize("hours", [float("inf"), float("nan")])
async def test_hours_003_nonfinite_numbers_are_rejected(
    upstream: dict[str, Any], app: FastAPI, hours: float
) -> None:
    # HTTPX JSON encoding disallows these values; supply an actual upstream byte response.
    async def respond(req):
        if req.url.path == "/users/current.json":
            return httpx.Response(200, json={"user": {"id": 3}})
        return httpx.Response(200, content=json.dumps({"issue": {**ISSUE, "spent_hours": hours}}))

    upstream["handler"] = respond
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-redmine-key"},
    ) as client:
        result = await client.get("/api/v1/issues/42")
    assert result.status_code == 502


@pytest.mark.parametrize(
    "changes",
    [
        {"memberships": None},
        {"memberships": {}},
        {"memberships": [None]},
        {"memberships": [{"id": 1, "project": {}, "roles": []}]},
        {"memberships": [{**MEMBERSHIP, "roles": None}]},
        {
            "memberships": [
                {**MEMBERSHIP, "roles": [{"id": 4, "name": "Role", "inherited": "true"}]}
            ]
        },
        {"id": 8},
        {"id": True},
        {"id": "3"},
        {"id": 0},
    ],
)
async def test_user_002_003_007_malformed_profile(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    changes: dict[str, Any],
) -> None:
    upstream["profile_response"] = 200, {"user": {**PROFILE, **changes}}
    result = await rest_client.get("/api/v1/users/current")
    assert result.status_code == 502
    assert result.json()["error"]["code"] == "upstream_response"


@pytest.mark.parametrize("missing", ["id", "memberships"])
async def test_user_002_007_required_profile_fields(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    missing: str,
) -> None:
    upstream["profile_response"] = 200, {"user": {k: v for k, v in PROFILE.items() if k != missing}}
    assert (await rest_client.get("/api/v1/users/current")).status_code == 502


@pytest.mark.parametrize("inherited", [None, True, False])
@pytest.mark.parametrize("email", ["missing", None, "reader@example.invalid"])
async def test_user_001_003_004_memberships_roles_and_email_observations(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    inherited: bool | None,
    email: Any,
) -> None:
    role = {"id": 4, "name": "Reporter", "unknown": "secret"}
    if inherited is not None:
        role["inherited"] = inherited
    profile = {**PROFILE, "memberships": [{**MEMBERSHIP, "roles": [role]}]}
    if email != "missing":
        profile["mail"] = email
    upstream["profile_response"] = 200, {"user": profile}
    result = await rest_client.get("/api/v1/users/current")
    assert result.status_code == 200
    body = result.json()
    assert body["memberships"][0]["roles"] == [
        {"id": 4, "name": "Reporter", "inherited": inherited or False}
    ]
    assert body["memberships"][0]["project"] == MEMBERSHIP["project"]
    assert body["mail"] == (None if email == "missing" else email)
    assert body["visibility"]["observations"] == (
        [{"path": "/mail", "state": "not_returned"}] if email == "missing" else []
    )
    requests = upstream["requests"]
    assert len(requests) == 2
    assert all(req.headers["X-Redmine-API-Key"] == "offline-redmine-key" for req in requests)
    assert dict(requests[0].url.params) == {}
    assert dict(requests[1].url.params) == {"include": "memberships"}


@pytest.mark.parametrize(
    ("status", "expected"), [(401, 401), (403, 403), (404, 404), (429, 502), (503, 502), (504, 504)]
)
async def test_user_006_008_profile_revocation_and_errors(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    monkeypatch: Any,
    status: int,
    expected: int,
) -> None:
    clock = RetryClock()
    monkeypatch.setattr("redmine_mcp.integrations.redmine.client.RetryRuntime", clock.runtime)
    upstream["profile_response"] = status, {"secret": "must-not-leak"}
    result = await rest_client.get("/api/v1/users/current")
    assert result.status_code == expected
    assert "must-not-leak" not in result.text
    attempts = 3 if status in (429, 503, 504) else 1
    requests = upstream["requests"]
    assert len(requests) == 1 + attempts
    assert dict(requests[0].url.params) == {}
    assert all(dict(request.url.params) == {"include": "memberships"} for request in requests[1:])


@pytest.mark.parametrize(
    "changes",
    [
        {"user": None},
        {"user": {}},
        {"user": {"id": True, "name": "Invalid"}},
        {"issue": None},
        {"issue": {"id": 43}},
        {"hours": None},
        {"hours": -1},
        {"hours": "1.5"},
        {"spent_on": "2026-02-30"},
        {"spent_on": None},
    ],
)
async def test_entry_004_malformed_fields_no_partial_result(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    changes: dict[str, Any],
) -> None:
    upstream["responses"] = reader_responses()
    upstream["responses"]["/time_entries.json"] = (
        200,
        {
            "time_entries": [ENTRY, {**ENTRY, "id": 2, **changes}],
            "total_count": 2,
            "limit": 25,
            "offset": 0,
        },
    )
    result = await rest_client.get("/api/v1/issues/42/time-entries")
    assert result.status_code == 502
    assert "items" not in result.json()


async def test_entry_001_002_003_page_001_attribution_and_multiple_pages(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    entries = [
        {
            **ENTRY,
            "id": n + 1,
            "user": {"id": 8 + n % 2, "name": "Credited"},
            "hours": 0 if n == 0 else 0.1,
            "spent_on": "2026-09-29" if n % 2 else "2026-09-30",
        }
        for n in range(101)
    ]
    upstream["responses"] = reader_responses()
    all_rows = []
    for offset in [0, 100, 200]:
        upstream["responses"]["/time_entries.json"] = (
            200,
            {
                "time_entries": entries[offset : offset + 100],
                "total_count": 101,
                "limit": 100,
                "offset": offset,
            },
        )
        result = await rest_client.get(
            "/api/v1/issues/42/time-entries", params={"limit": 100, "offset": offset}
        )
        assert result.status_code == 200
        body = result.json()
        assert body["total"] == 101 and body["visibility"]["scope"] == "requesting_redmine_user"
        assert dict(upstream["requests"][-1].url.params) == {
            "issue_id": "42",
            "limit": "100",
            "offset": str(offset),
        }
        all_rows.extend(body["items"])
    assert len(all_rows) == 101
    assert all_rows[0]["hours"] == 0
    assert {row["user"]["id"] for row in all_rows} == {8, 9}
    assert ISSUE["author"]["id"] not in {row["user"]["id"] for row in all_rows}
    upstream["responses"]["/time_entries.json"] = (
        200,
        {"time_entries": [], "total_count": 0, "limit": 25, "offset": 0},
    )
    empty = await rest_client.get("/api/v1/issues/42/time-entries")
    assert empty.json()["total"] == 0


async def test_vis_001_time_entry_permission_after_visible_issue(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    upstream["responses"] = reader_responses()
    upstream["responses"]["/time_entries.json"] = 403, {}
    result = await rest_client.get("/api/v1/issues/42/time-entries")
    assert result.status_code == 403
    assert [req.url.path for req in upstream["requests"]] == [
        "/users/current.json",
        "/issues/42.json",
        "/time_entries.json",
    ]


async def test_user_005_009_all_reader_mcp_invocation_and_sanitized_errors(
    app: FastAPI,
    upstream: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    upstream["responses"] = reader_responses()
    upstream["profile_response"] = (
        200,
        {
            "user": {
                **PROFILE,
                "api_key": "hidden-profile-secret",
                "admin": True,
                "last_login_on": "secret",
            }
        },
    )
    arguments = {
        "list_project_members": {"project_ids": [7]},
        "list_project_time_entry_activities": {"project_id": 7},
        "list_project_files": {"project_id": 7},
        "get_attachment": {"attachment_id": 9},
        "get_project": {"project_id": 7},
        "get_issue": {"issue_id": 42},
        "list_project_versions": {"project_id": 7},
        "list_project_issue_categories": {"project_id": 7},
        "list_issue_time_entries": {"issue_id": 42},
    }
    with caplog.at_level(logging.INFO):
        async with mcp_session(app) as session:
            tools = (await session.list_tools()).tools
            assert [tool.name for tool in tools].count("get_current_user") == 1
            assert {tool.name for tool in tools} == set(OPERATIONS)
            current = next(tool for tool in tools if tool.name == "get_current_user")
            assert current.inputSchema.get("properties", {}) == {}
            for name in OPERATIONS:
                result = await session.call_tool(name, arguments.get(name, {}))
                assert not result.isError, (name, result)
                assert "hidden-profile-secret" not in str(result.content)
                assert "last_login_on" not in str(result.content)
                if name == "get_current_user":
                    assert "admin" not in json.loads(result.content[0].text)
            invalids = [
                {"category_id": 0},
                {"category_id": 5},
                {"fixed_version_id": 0},
                {"include_subprojects": False},
                {"include_subprojects": "invalid"},
            ]
            for args in invalids:
                before = len(upstream["requests"])
                result = await session.call_tool("list_issues", args)
                assert result.isError
                assert all(
                    req.url.path == "/users/current.json" for req in upstream["requests"][before:]
                )
            for name in OPERATIONS:
                if name == "get_current_user":
                    upstream["profile_response"] = 403, {"secret": "error-content-secret"}
                else:
                    upstream["responses"] = {}
                    upstream.update(status=403, body={"secret": "error-content-secret"})
                result = await session.call_tool(name, arguments.get(name, {}))
                if name == "list_project_members":
                    # Selected-project failures are reported as individual read outcomes.
                    assert not result.isError
                    assert json.loads(result.content[0].text)["results"][0]["outcome"] == "rejected"
                else:
                    assert result.isError
                assert "access_denied" in str(result.content)
                assert "error-content-secret" not in str(result.content)
    assert "hidden-profile-secret" not in caplog.text
    assert "error-content-secret" not in caplog.text


async def test_foundation_007_user_001_concurrent_rest_mcp_visibility_isolation(
    app: FastAPI,
    upstream: dict[str, Any],
) -> None:
    keys = {"synthetic-a": 3, "synthetic-b": 8}

    async def respond(req):
        key = req.headers["X-Redmine-API-Key"]
        await asyncio.sleep(0)
        user_id = keys[key]
        if req.url.path == "/users/current.json":
            return httpx.Response(
                200, json={"user": {**PROFILE, "id": user_id, "login": key, "memberships": []}}
            )
        assert req.url.path == "/projects.json"
        return httpx.Response(
            200, json={"projects": [{**PROJECT, "id": user_id}], "total_count": 1}
        )

    upstream["handler"] = respond

    async def check(key):
        async with mcp_session(app, key) as session:
            result = await session.call_tool("get_current_user", {})
            assert not result.isError
            assert json.loads(result.content[0].text)["id"] == keys[key]
            projects = await session.call_tool("list_projects", {})
            assert json.loads(projects.content[0].text)["items"][0]["id"] == keys[key]
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": key},
        ) as client:
            assert (await client.get("/api/v1/users/current")).json()["id"] == keys[key]

    await asyncio.gather(*(check(key) for key in keys))
    assert {req.headers["X-Redmine-API-Key"] for req in upstream["requests"]} == set(keys)


async def test_agg_issue_direct_hours_pagination_boundaries_and_incomplete(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    rows = [
        {
            **ISSUE,
            "id": 41,
            "start_date": "2026-09-01",
            "due_date": "2026-09-30",
            "spent_hours": 1.5,
            "total_spent_hours": 3.5,
            "children": [{"id": 42, "subject": "Child"}],
        },
        {**ISSUE, "start_date": "2026-09-01", "due_date": "2026-09-30", "spent_hours": 2},
        {**ISSUE, "id": 43, "start_date": None, "due_date": "2026-09-30", "spent_hours": 9},
        {**ISSUE, "id": 44, "start_date": "2026-08-31", "due_date": "2026-09-30", "spent_hours": 9},
    ]
    unique = {}
    for offset in [0, 2]:
        upstream["body"] = {
            "issues": rows[offset : offset + 2],
            "total_count": 4,
            "limit": 2,
            "offset": offset,
        }
        result = await rest_client.get(
            "/api/v1/issues",
            params={
                "limit": 2,
                "offset": offset,
                "project_id": 7,
                "tracker_id": 1,
                "status_id": "*",
                "include_subprojects": "false",
            },
        )
        assert result.status_code == 200
        for row in result.json()["items"]:
            if (
                row["start_date"]
                and row["due_date"]
                and row["start_date"] >= "2026-09-01"
                and row["due_date"] <= "2026-09-30"
            ):
                unique[row["id"]] = row
    assert sum(Decimal(str(row["spent_hours"])) for row in unique.values()) == Decimal("3.5")
    upstream["body"] = {"issues": [{**rows[0], "spent_hours": None}], "total_count": 1}
    incomplete = (await rest_client.get("/api/v1/issues")).json()["items"]
    assert any(row["spent_hours"] is None for row in incomplete)


async def test_agg_time_entries_six_issues_decimal_sum_and_deduplication(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    unique = {}
    for issue_id in range(42, 48):
        upstream["responses"] = {
            f"/issues/{issue_id}.json": (200, {"issue": {**ISSUE, "id": issue_id}}),
            "/time_entries.json": (
                200,
                {
                    "time_entries": [
                        {**ENTRY, "id": issue_id * 2, "issue": {"id": issue_id}, "hours": 0.1},
                        {
                            **ENTRY,
                            "id": issue_id * 2 + 1,
                            "issue": {"id": issue_id},
                            "hours": 0.2,
                            "user": {"id": 9, "name": "Second"},
                        },
                    ],
                    "total_count": 2,
                    "limit": 25,
                    "offset": 0,
                },
            ),
        }
        result = await rest_client.get(f"/api/v1/issues/{issue_id}/time-entries")
        assert result.status_code == 200
        for row in [*result.json()["items"], *result.json()["items"]]:
            unique[row["id"]] = row
    sums: dict[int, Decimal] = {}
    for row in unique.values():
        user_id = row["user"]["id"]
        sums[user_id] = sums.get(user_id, Decimal(0)) + Decimal(str(row["hours"]))
    assert len(unique) == 12
    assert sums == {8: Decimal("0.6"), 9: Decimal("1.2")}


@pytest.mark.parametrize(
    ("mode", "expected", "code"),
    [
        ("timeout", 504, "upstream_timeout"),
        ("transport", 502, "upstream_unavailable"),
        ("json", 502, "upstream_response"),
        ("overflow", 502, "upstream_response_too_large"),
        ("envelope", 502, "upstream_response"),
    ],
)
async def test_user_008_profile_acquisition_failure(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    fake_settings: Settings,
    monkeypatch: Any,
    mode: str,
    expected: int,
    code: str,
) -> None:
    clock = RetryClock()
    monkeypatch.setattr("redmine_mcp.integrations.redmine.client.RetryRuntime", clock.runtime)
    fake_settings.redmine_max_response_bytes = 200

    async def respond(req):
        if not req.url.params:
            return httpx.Response(200, json={"user": {"id": 3}})
        if mode == "timeout":
            raise httpx.ReadTimeout("sensitive-profile-data")
        if mode == "transport":
            raise httpx.ConnectError("sensitive-profile-data")
        if mode == "json":
            return httpx.Response(200, content=b"not-json-sensitive-profile-data")
        if mode == "overflow":
            return httpx.Response(200, json={"user": {**PROFILE, "unknown": "x" * 500}})
        return httpx.Response(200, json={"user": []})

    upstream["handler"] = respond
    result = await rest_client.get("/api/v1/users/current")
    assert (result.status_code, result.json()["error"]["code"]) == (expected, code)
    assert "sensitive-profile-data" not in result.text
    attempts = 3 if mode in ("timeout", "transport") else 1
    requests = upstream["requests"]
    assert len(requests) == 1 + attempts
    assert dict(requests[0].url.params) == {}
    assert all(dict(request.url.params) == {"include": "memberships"} for request in requests[1:])


async def test_detail_004_requested_omissions_and_malformed_expansion(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
) -> None:
    upstream["body"] = {"issue": ISSUE}
    result = await rest_client.get("/api/v1/issues/42", params={"include": "journals"})
    assert result.status_code == 200
    assert {"path": "/journals", "state": "not_returned"} in result.json()["visibility"][
        "observations"
    ]
    upstream["body"] = {"issue": {**ISSUE, "journals": [{}]}}
    assert (await rest_client.get("/api/v1/issues/42")).status_code == 502
    upstream["body"] = {"issue": {**ISSUE, "id": 43}}
    assert (await rest_client.get("/api/v1/issues/42")).status_code == 502
