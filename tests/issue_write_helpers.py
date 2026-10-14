"""Independent native fixtures and REST/MCP calls for older writer regression tests."""

import json
from collections.abc import Callable
from typing import Any

import httpx

from tests.helpers import mcp_session

# Literal native results, independently read from Redmine 7.0.2 IssueRelation TYPES,
# reverse_if_needed and handle_issue_order. Never call the adapter to construct responses.
# https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/models/issue_relation.rb
RELATION_CASES = [
    (42, 43, "relates", None, (42, 43, "relates", None)),
    (42, 43, "duplicates", None, (42, 43, "duplicates", None)),
    (42, 43, "duplicated", None, (43, 42, "duplicates", None)),
    (42, 43, "blocks", None, (42, 43, "blocks", None)),
    (42, 43, "blocked", None, (43, 42, "blocks", None)),
    (42, 43, "precedes", None, (42, 43, "precedes", 0)),
    (42, 43, "follows", None, (43, 42, "precedes", 0)),
    (42, 43, "copied_to", None, (42, 43, "copied_to", None)),
    (42, 43, "copied_from", None, (43, 42, "copied_to", None)),
    (43, 42, "relates", None, (42, 43, "relates", None)),
    (43, 42, "duplicates", None, (43, 42, "duplicates", None)),
    (43, 42, "duplicated", None, (42, 43, "duplicates", None)),
    (43, 42, "blocks", None, (43, 42, "blocks", None)),
    (43, 42, "blocked", None, (42, 43, "blocks", None)),
    (43, 42, "precedes", None, (43, 42, "precedes", 0)),
    (43, 42, "follows", None, (42, 43, "precedes", 0)),
    (43, 42, "copied_to", None, (43, 42, "copied_to", None)),
    (43, 42, "copied_from", None, (42, 43, "copied_to", None)),
    (42, 43, "precedes", -2, (42, 43, "precedes", -2)),
    (42, 43, "follows", -2, (43, 42, "precedes", -2)),
    (43, 42, "precedes", 3, (43, 42, "precedes", 3)),
    (43, 42, "follows", 3, (42, 43, "precedes", 3)),
    (42, 43, "precedes", 0, (42, 43, "precedes", 0)),
    (42, 43, "follows", 0, (43, 42, "precedes", 0)),
]
RELATION_RESPONSES = {
    row[:4]: dict(zip(("issue_id", "issue_to_id", "relation_type", "delay"), row[4], strict=True))
    for row in RELATION_CASES
}

ROUTES = {
    "create_issue": ("POST", "/api/v1/issues", ()),
    "update_issue": ("PUT", "/api/v1/issues/{issue_id}", ("issue_id",)),
    "update_issue_note": (
        "PUT",
        "/api/v1/issues/{issue_id}/notes/{journal_id}",
        ("issue_id", "journal_id"),
    ),
    "create_issue_relation": ("POST", "/api/v1/issues/{issue_id}/relations", ("issue_id",)),
    "delete_issue_relation": ("DELETE", "/api/v1/relations/{relation_id}", ("relation_id",)),
    "add_issue_watcher": ("POST", "/api/v1/issues/{issue_id}/watchers", ("issue_id",)),
    "remove_issue_watcher": (
        "DELETE",
        "/api/v1/issues/{issue_id}/watchers/{user_id}",
        ("issue_id", "user_id"),
    ),
    "update_attachment": ("PATCH", "/api/v1/attachments/{attachment_id}", ("attachment_id",)),
    "delete_attachment": ("DELETE", "/api/v1/attachments/{attachment_id}", ("attachment_id",)),
}


async def invoke(
    app: Any,
    boundary: str,
    operation: str,
    arguments: dict[str, Any],
    *,
    key: str = "offline-redmine-key",
) -> tuple[int, dict[str, Any]]:
    if boundary == "mcp":
        async with mcp_session(app, key) as session:
            result = await session.call_tool(operation, arguments)
        if result.isError:
            return 422, {"mcp_error": result.content[0].text}
        return 200, json.loads(result.content[0].text)
    method, template, path_keys = ROUTES[operation]
    payload = arguments.copy()
    path = template.format(**{name: payload.pop(name) for name in path_keys})
    options = {"params": payload} if operation == "delete_attachment" else {"json": payload or None}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": key},
    ) as client:
        response = await client.request(method, path, **options)
    return response.status_code, response.json()


def override(synthetic: Any, callback: Callable[[httpx.Request], httpx.Response | None]) -> None:
    original = synthetic.respond

    def record(request: httpx.Request) -> None:
        synthetic.requests.append(request)
        if request.method != "GET":
            synthetic.writes += 1

    async def respond(request: httpx.Request) -> httpx.Response:
        try:
            replacement = callback(request)
        except httpx.RequestError:
            record(request)
            raise
        if replacement is None:
            return await original(request)
        record(request)
        return replacement

    synthetic.respond = respond


def writes(synthetic: Any) -> list[httpx.Request]:
    return [request for request in synthetic.requests if request.method != "GET"]


def assert_error(data: dict[str, Any], boundary: str, code: str) -> None:
    if boundary == "rest":
        assert data["error"]["code"] == code
    else:
        assert code in data["mcp_error"]
