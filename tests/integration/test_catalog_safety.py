"""Every registered tool must retain authentication, validation and write gates."""

import copy
from typing import Any

import httpx
import pytest

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS
from tests.catalog_cases import CATALOG_CASES, ToolCase
from tests.helpers import mcp_session
from tests.integration.test_current_tools import WRITES

INVALID_CASES = [case for case in CATALOG_CASES if case.invalid is not None]
WRITE_CASES = [case for case in CATALOG_CASES if case.operation in WRITE_OPERATIONS]


def route_request(
    app: Any, case: ToolCase, arguments: dict[str, Any]
) -> tuple[str, str, dict[str, Any]]:
    matches = [
        (method, path, operation)
        for path, methods in app.openapi()["paths"].items()
        for method, operation in methods.items()
        if isinstance(operation, dict) and operation.get("operationId") == case.operation
    ]
    assert len(matches) == 1, f"Missing or ambiguous REST contract for {case.operation}"
    method, path, operation = matches[0]
    remaining = copy.deepcopy(arguments)
    query = {}
    for parameter in operation.get("parameters", []):
        name = parameter["name"]
        if parameter["in"] == "path":
            path = path.replace("{" + name + "}", str(remaining.pop(name)))
        elif parameter["in"] == "query" and name in remaining:
            query[name] = remaining.pop(name)
    options: dict[str, Any] = {"params": query}
    if operation.get("requestBody"):
        options["json"] = remaining
    else:
        assert not remaining, f"Unmapped arguments for {case.operation}"
    return method.upper(), path, options


def test_catalog_has_explicit_cases_and_writer_success_owners() -> None:
    names = [case.operation for case in CATALOG_CASES]
    assert len(names) == len(set(names))
    assert set(names) == set(READ_OPERATIONS) | set(WRITE_OPERATIONS)
    # Memberships have dedicated batch success/fault tests; every other write uses WRITES.
    assert {row[0] for row in WRITES} | {
        "add_project_members",
        "update_project_members",
        "delete_project_members",
    } == set(WRITE_OPERATIONS)
    assert {case.operation for case in CATALOG_CASES if case.invalid is None} == {
        "get_current_user",
        "list_issue_statuses",
        "list_issue_priorities",
        "list_document_categories",
        "list_trackers",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CATALOG_CASES, ids=lambda case: case.operation)
@pytest.mark.parametrize("key", [None, "invalid-catalog-key"], ids=["missing", "invalid"])
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_every_tool_rejects_missing_or_invalid_credentials_before_work(
    writer_app: Any, synthetic: Any, case: ToolCase, key: str | None, boundary: str
) -> None:
    before = copy.deepcopy((synthetic.issues, synthetic.time_entries, synthetic.members))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": key} if key is not None else {},
    ) as client:
        if boundary == "rest":
            method, path, options = route_request(writer_app, case, case.arguments)
            response = await client.request(method, path, **options)
        else:
            response = await client.post(
                "/mcp",
                headers={"Accept": "application/json, text/event-stream"},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": case.operation, "arguments": case.arguments},
                },
            )
    assert response.status_code == 401
    assert synthetic.writes == 0
    assert before == (synthetic.issues, synthetic.time_entries, synthetic.members)
    assert all(r.url.path == "/users/current.json" for r in synthetic.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", INVALID_CASES, ids=lambda case: case.operation)
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_every_tool_with_inputs_rejects_a_contract_invalid_value(
    writer_app: Any, synthetic: Any, case: ToolCase, boundary: str
) -> None:
    assert case.invalid is not None
    arguments = {**case.arguments, **case.invalid}
    before = copy.deepcopy((synthetic.issues, synthetic.time_entries, synthetic.members))
    if boundary == "mcp":
        async with mcp_session(writer_app) as session:
            result = await session.call_tool(case.operation, arguments)
        assert result.isError, case.operation
    else:
        method, path, options = route_request(writer_app, case, arguments)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=writer_app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-redmine-key"},
        ) as client:
            response = await client.request(method, path, **options)
        assert response.status_code == 422
    assert synthetic.writes == 0
    assert before == (synthetic.issues, synthetic.time_entries, synthetic.members)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", WRITE_CASES, ids=lambda case: case.operation)
@pytest.mark.parametrize("gate", ["reader_deployment", "operation_disabled"])
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_every_write_requires_deployment_and_operation_enablement(
    application_factory: Any, synthetic: Any, case: ToolCase, gate: str, boundary: str
) -> None:
    async with application_factory(
        redmine_write_enabled=gate == "operation_disabled",
        redmine_writer_operations="",
    ) as app:
        if boundary == "mcp":
            async with mcp_session(app) as session:
                names = {tool.name for tool in (await session.list_tools()).tools}
                assert case.operation not in names
                result = await session.call_tool(case.operation, case.arguments)
            assert result.isError
        else:
            method, path, options = route_request(app, case, case.arguments)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": "offline-redmine-key"},
            ) as client:
                response = await client.request(method, path, **options)
            assert response.status_code == 403
    assert synthetic.writes == 0
