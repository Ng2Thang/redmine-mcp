from typing import Any

import httpx
import pytest
from fastapi import status as http_status

from tests.helpers import ISSUE, PROJECT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("route", "path", "collection", "item"),
    [
        (
            "/api/v1/issue-statuses",
            "/issue_statuses.json",
            "issue_statuses",
            {"id": 1, "name": "New", "is_closed": False},
        ),
        (
            "/api/v1/trackers",
            "/trackers.json",
            "trackers",
            {"id": 2, "name": "Bug"},
        ),
        (
            "/api/v1/issue-priorities",
            "/enumerations/issue_priorities.json",
            "issue_priorities",
            {"id": 3, "name": "Normal", "is_default": True},
        ),
        (
            "/api/v1/projects/7/versions",
            "/projects/7/versions.json",
            "versions",
            {"id": 4, "name": "Sprint", "project": {"id": 7, "name": "Demo"}, "status": "open"},
        ),
        (
            "/api/v1/projects/7/issue-categories",
            "/projects/7/issue_categories.json",
            "issue_categories",
            {"id": 5, "name": "Backend", "project": {"id": 7, "name": "Demo"}},
        ),
    ],
)
async def test_lookup_collections_and_empty_response(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    route: str,
    path: str,
    collection: str,
    item: dict[str, Any],
) -> None:
    upstream["responses"] = {path: (200, {collection: [item], "total_count": 1})}
    populated = await rest_client.get(route)
    assert populated.status_code == 200
    assert populated.json()["items"][0]["id"] == item["id"]
    assert upstream["requests"][-1].url.path == path

    upstream["responses"][path] = (200, {collection: [], "total_count": 0})
    empty = await rest_client.get(route)
    assert empty.status_code == 200
    assert empty.json()["items"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("route", "path", "collection"),
    [
        ("/api/v1/issue-statuses", "/issue_statuses.json", "issue_statuses"),
        ("/api/v1/trackers", "/trackers.json", "trackers"),
        (
            "/api/v1/issue-priorities",
            "/enumerations/issue_priorities.json",
            "issue_priorities",
        ),
        ("/api/v1/projects/7/versions", "/projects/7/versions.json", "versions"),
        (
            "/api/v1/projects/7/issue-categories",
            "/projects/7/issue_categories.json",
            "issue_categories",
        ),
    ],
)
async def test_lookup_malformed_collection_is_safe(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    route: str,
    path: str,
    collection: str,
) -> None:
    upstream["responses"] = {path: (200, {collection: [{}], "total_count": 1})}
    response = await rest_client.get(route)
    assert response.status_code == http_status.HTTP_502_BAD_GATEWAY
    assert response.json()["error"]["code"] == "upstream_response"


@pytest.mark.asyncio
async def test_project_detail_and_collection_count(
    rest_client: httpx.AsyncClient, upstream: dict[str, Any]
) -> None:
    upstream["responses"] = {
        "/projects/7.json": (200, {"project": {**PROJECT, "is_public": False}}),
        "/projects/7/versions.json": (
            200,
            {
                "versions": [
                    {
                        "id": 4,
                        "name": "Sprint",
                        "project": {"id": 7, "name": "Demo"},
                        "status": "open",
                    }
                ],
                "total_count": 2,
            },
        ),
    }
    detail = await rest_client.get("/api/v1/projects/7")
    assert detail.status_code == 200
    assert detail.json()["is_public"] is False
    partial = await rest_client.get("/api/v1/projects/7/versions")
    assert partial.status_code == 502
    assert partial.json()["error"]["code"] == "upstream_response"


@pytest.mark.asyncio
async def test_current_user_selects_public_fields(
    rest_client: httpx.AsyncClient, upstream: dict[str, Any]
) -> None:
    result = await rest_client.get("/api/v1/users/current")
    assert result.status_code == 200
    body = result.json()
    assert body["id"] == 3
    assert body["memberships"] == []
    assert body["mail"] is None
    assert "api_key" not in body
    assert "upstream-secret-must-not-leak" not in result.text
    assert upstream["requests"][-1].url.params["include"] == "memberships"


@pytest.mark.asyncio
async def test_time_entry_attribution_and_exact_query(
    rest_client: httpx.AsyncClient, upstream: dict[str, Any]
) -> None:
    upstream["responses"] = {
        "/issues/42.json": (200, {"issue": ISSUE}),
        "/time_entries.json": (
            200,
            {
                "time_entries": [
                    {
                        "id": 9,
                        "issue": {"id": 42},
                        "user": {"id": 8, "name": "Credited User"},
                        "hours": 1.5,
                        "spent_on": "2026-09-30",
                    }
                ],
                "total_count": 1,
                "limit": 1,
                "offset": 0,
            },
        ),
    }
    response = await rest_client.get("/api/v1/issues/42/time-entries", params={"limit": 1})
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert (item["issue_id"], item["user"]["id"], item["hours"]) == (42, 8, 1.5)
    assert dict(upstream["requests"][-1].url.params) == {
        "issue_id": "42",
        "limit": "1",
        "offset": "0",
    }


@pytest.mark.asyncio
async def test_time_entry_cross_issue_is_rejected(
    rest_client: httpx.AsyncClient, upstream: dict[str, Any]
) -> None:
    upstream["responses"] = {
        "/issues/42.json": (200, {"issue": ISSUE}),
        "/time_entries.json": (
            200,
            {
                "time_entries": [
                    {
                        "id": 9,
                        "issue": {"id": 43},
                        "user": {"id": 8, "name": "Other"},
                        "hours": 1.5,
                        "spent_on": "2026-09-30",
                    }
                ],
                "total_count": 1,
                "limit": 25,
                "offset": 0,
            },
        ),
    }
    response = await rest_client.get("/api/v1/issues/42/time-entries")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "upstream_response"
