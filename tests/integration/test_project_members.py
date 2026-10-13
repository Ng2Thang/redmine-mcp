"""TOOL-033 REST/MCP contracts with an isolated, stateful Redmine substitute."""

import copy
import json
from typing import Any

import httpx
import pytest

from redmine_mcp.auth import WRITE_OPERATIONS
from tests.helpers import mcp_session
from tests.membership_helpers import membership

ROUTE = "/api/v1/projects/memberships/batch"
OPERATIONS = {
    "add": "add_project_members",
    "update": "update_project_members",
    "delete": "delete_project_members",
}
METHODS = {"add": "POST", "update": "PUT", "delete": "DELETE"}


def item(action: str, target: int = 20, *, project_id: int = 7) -> dict[str, Any]:
    result = {"project_id": project_id}
    result["user_id" if action == "add" else "membership_id"] = target
    if action != "delete":
        result["role_ids"] = [5]
    return result


async def invoke(
    app: Any, action: str, items: Any, *, boundary: str = "rest", key: str = "offline-redmine-key"
) -> tuple[int, Any]:
    if boundary == "mcp":
        async with mcp_session(app, key) as session:
            result = await session.call_tool(OPERATIONS[action], {"items": items})
        return (422 if result.isError else 200), json.loads(result.content[0].text)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": key},
    ) as client:
        response = await client.request(METHODS[action], ROUTE, json={"items": items})
    return response.status_code, response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("action", OPERATIONS)
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_native_payload_single_attempt_and_readback(
    writer_app: Any, synthetic: Any, action: str, boundary: str
) -> None:
    status, result = await invoke(writer_app, action, [item(action)], boundary=boundary)
    assert status == 200, result
    assert result["phase"] == "executed"
    row = result["results"][0]
    assert row["outcome"] == "accepted" and row["verification"] == "matched", row
    writes = [r for r in synthetic.requests if r.method != "GET"]
    assert len(writes) == 1
    request = writes[0]
    assert request.method == METHODS[action]
    assert request.url.path == (
        "/projects/7/memberships.json" if action == "add" else "/memberships/20.json"
    )
    assert request.headers["X-Redmine-API-Key"] == "offline-redmine-key"
    if action == "delete":
        assert request.content == b"" and row["observed_present"] is False
        assert 20 not in synthetic.members
        assert any(r.url.path == "/projects/7/memberships.json" for r in synthetic.requests)
    else:
        expected = {"role_ids": [5]}
        if action == "add":
            expected["user_id"] = 20
        assert json.loads(request.content) == {"membership": expected}
        assert row["observed_present"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_reader_pagination_users_groups_and_repeated_roles(
    application_factory: Any, synthetic: Any, boundary: str
) -> None:
    synthetic.members[21] = membership(21, group=True, inherited=True)
    synthetic.members[20]["roles"] += [{**synthetic.members[20]["roles"][0], "inherited": True}]
    async with application_factory() as app:
        pages = []
        if boundary == "rest":
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": "offline-reader-key"},
            ) as client:
                for offset in (0, 1, 2):
                    response = await client.get(
                        "/api/v1/projects/memberships",
                        params={
                            "project_ids": 7,
                            "limit": 1,
                            "offset": offset,
                        },
                    )
                    assert response.status_code == 200
                    pages.append(response.json()["results"][0]["page"])
        else:
            async with mcp_session(app, "offline-reader-key") as session:
                assert "list_project_members" in {
                    t.name for t in (await session.list_tools()).tools
                }
                for offset in (0, 1, 2):
                    result = await session.call_tool(
                        "list_project_members",
                        {
                            "project_ids": [7],
                            "limit": 1,
                            "offset": offset,
                        },
                    )
                    assert not result.isError
                    pages.append(json.loads(result.content[0].text)["results"][0]["page"])
    assert [p["total"] for p in pages] == [2, 2, 2]
    assert [p["offset"] for p in pages] == [0, 1, 2]
    assert pages[2]["items"] == []
    assert pages[0]["items"][0]["roles"][0]["inherited"] is True
    assert len(pages[0]["items"][0]["roles"]) == 1
    assert pages[1]["items"][0]["group"]["id"] == 10
    assert pages[1]["items"][0]["user"] is None
    assert all(p["visibility"]["scope"] == "requesting_redmine_user" for p in pages)
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", ["group", "inherited", "project_mismatch", "missing", "unknown_role", "existing"]
)
async def test_one_known_error_prevents_entire_batch(
    writer_app: Any, synthetic: Any, failure: str
) -> None:
    action = "delete"
    if failure == "group":
        synthetic.members[21] = membership(21, group=True)
    elif failure == "inherited":
        synthetic.members[21]["roles"].append(
            {**synthetic.members[21]["roles"][0], "inherited": True}
        )
    elif failure == "project_mismatch":
        synthetic.members[21]["project"]["id"] = 8
    elif failure == "missing":
        del synthetic.members[21]
    elif failure == "unknown_role":
        action = "update"
    else:
        action = "add"
    items = [item(action, 20), item(action, 21)]
    if failure == "unknown_role":
        items[1]["role_ids"] = [999]
    if failure == "existing":
        items[1]["user_id"] = 10
    status, result = await invoke(writer_app, action, items)
    assert status == 200 and result["phase"] == "preflight_failed", result
    assert [r["outcome"] for r in result["results"]] == ["not_executed", "rejected"]
    if failure == "existing":
        assert result["results"][1]["error"]["code"] == "membership_already_exists"
        assert result["results"][1]["observed_membership"]["id"] == 20
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("action", OPERATIONS)
@pytest.mark.parametrize("gate", ["reader", "allowlist", "permission"])
async def test_writer_gates_prevent_native_mutation(
    application_factory: Any, synthetic: Any, action: str, gate: str
) -> None:
    overrides = (
        {}
        if gate == "reader"
        else {
            "redmine_write_enabled": True,
            "redmine_writer_operations": "create_issue"
            if gate == "allowlist"
            else OPERATIONS[action],
        }
    )
    async with application_factory(**overrides) as app:
        status, result = await invoke(
            app,
            action,
            [item(action)],
            key="offline-reader-key" if gate == "permission" else "offline-redmine-key",
        )
        if gate == "permission":
            assert status == 200 and result["phase"] == "preflight_failed"
            assert result["results"][0]["error"]["code"] == "permission_denied"
        else:
            assert status == 403, result
        async with mcp_session(
            app, "offline-reader-key" if gate == "permission" else "offline-redmine-key"
        ) as session:
            names = {t.name for t in (await session.list_tools()).tools}
            assert "list_project_members" in names
            assert OPERATIONS[action] not in names
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [200, 204])
@pytest.mark.parametrize("protected", ["inherited", "protected"])
async def test_update_retained_roles_are_accepted_but_mismatch(
    writer_app: Any, synthetic: Any, status_code: int, protected: str
) -> None:
    if protected == "inherited":
        synthetic.members[20]["roles"][0]["inherited"] = True
    else:
        synthetic.protected_roles = {4}
    original = synthetic.respond

    async def respond(request: Any) -> Any:
        response = await original(request)
        return httpx.Response(status_code) if request.method == "PUT" else response

    synthetic.respond = respond
    status, result = await invoke(writer_app, "update", [item("update")])
    row = result["results"][0]
    assert status == 200 and row["outcome"] == "accepted"
    assert row["verification"] == "mismatch"
    assert row["requested_role_ids"] == [5]
    assert {r["id"] for r in row["observed_membership"]["roles"]} == {4, 5}
    assert synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("action", OPERATIONS)
async def test_failed_readback_preserves_acceptance(
    writer_app: Any, synthetic: Any, action: str
) -> None:
    synthetic.readback_failure = True
    status, result = await invoke(writer_app, action, [item(action)])
    row = result["results"][0]
    assert status == 200 and row["outcome"] == "accepted"
    assert row["verification"] == "unavailable" and row["observed_present"] is None
    assert synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", [403, 422, 401, 500, 503, 504, httpx.ReadTimeout("private-error")]
)
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_partial_execution_and_shared_failure_stopping(
    writer_app: Any, synthetic: Any, failure: Any, boundary: str
) -> None:
    synthetic.members[22] = membership(22, user_id=12)
    original = synthetic.respond

    async def respond(request: Any) -> Any:
        if request.method == "PUT" and request.url.path == "/memberships/21.json":
            synthetic.write_failure = failure
        if request.method == "PUT" and request.url.path == "/memberships/22.json":
            synthetic.write_failure = None
        return await original(request)

    synthetic.respond = respond
    status, result = await invoke(
        writer_app, "update", [item("update", n) for n in (20, 21, 22)], boundary=boundary
    )
    assert status == 200 and result["phase"] == "executed", result
    expected = (
        ["accepted", "rejected", "accepted"]
        if failure in (403, 422)
        else ["accepted", "rejected" if failure == 401 else "uncertain", "not_executed"]
    )
    assert [r["outcome"] for r in result["results"]] == expected, result
    assert result["results"][0]["verification"] == "matched"
    assert synthetic.writes == (3 if failure in (403, 422) else 2)
    assert not any(r.method == "DELETE" for r in synthetic.requests)
    assert "must-not-leak" not in json.dumps(result) and "private-error" not in json.dumps(result)
    if failure in (500, 503, 504):
        second_write = next(
            i
            for i, r in enumerate(synthetic.requests)
            if r.method == "PUT" and r.url.path == "/memberships/21.json"
        )
        assert not any(
            r.method != "GET"
            or r.url.path.startswith("/memberships/")
            or r.url.path.endswith("/memberships.json")
            for r in synthetic.requests[second_write + 1 :]
        )
        assert result["results"][1]["verification"] == "unavailable"


@pytest.mark.asyncio
async def test_concurrent_duplicate_is_observed_without_update_or_retry(
    writer_app: Any, synthetic: Any
) -> None:
    original = synthetic.respond

    async def respond(request: Any) -> Any:
        if request.method == "POST":
            synthetic.members[22] = membership(22, user_id=20)
            synthetic.members[22]["roles"].append(
                {**synthetic.members[22]["roles"][0], "inherited": True}
            )
        return await original(request)

    synthetic.respond = respond
    status, result = await invoke(writer_app, "add", [item("add")])
    row = result["results"][0]
    assert status == 200 and row["outcome"] == "rejected"
    assert row["error"]["code"] == "membership_already_exists"
    assert row["observed_membership"]["id"] == 22
    assert row["observed_membership"]["roles"][0]["inherited"] is True
    assert len(row["observed_membership"]["roles"]) == 1
    assert synthetic.writes == 1
    assert [r.method for r in synthetic.requests if r.method != "GET"] == ["POST"]


@pytest.mark.asyncio
async def test_caller_permission_revoked_after_first_item_is_refreshed(
    writer_app: Any, synthetic: Any
) -> None:
    original = synthetic.respond

    async def respond(request: Any) -> Any:
        response = await original(request)
        if request.method == "PUT":
            synthetic.permissions.remove("manage_members")
        return response

    synthetic.respond = respond
    status, result = await invoke(writer_app, "update", [item("update", n) for n in (20, 21)])
    assert status == 200
    assert [r["outcome"] for r in result["results"]] == ["accepted", "rejected"]
    assert result["results"][1]["error"]["code"] == "permission_denied"
    assert synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("action", OPERATIONS)
@pytest.mark.parametrize("invalid", ["duplicate", "extra", "bool", "empty"])
async def test_invalid_input_never_reaches_mutation(
    writer_app: Any, synthetic: Any, action: str, invalid: str
) -> None:
    values = [item(action)]
    if invalid == "duplicate":
        values += copy.deepcopy(values)
    elif invalid == "extra":
        values[0]["group_id"] = 12
    elif invalid == "bool":
        values[0]["project_id"] = True
    else:
        values = []
    status, _ = await invoke(writer_app, action, values)
    assert status == 422
    assert all(r.url.path == "/users/current.json" for r in synthetic.requests)
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malformed", ["missing_metadata", "wrong_project", "duplicate", "principal", "roles"]
)
async def test_malformed_pages_are_sanitized(
    writer_app: Any, synthetic: Any, malformed: str
) -> None:
    original = synthetic.respond

    async def respond(request: Any) -> Any:
        if request.url.path != "/projects/7/memberships.json":
            return await original(request)
        member = membership()
        values = [member]
        data = {"memberships": values, "total_count": 1, "limit": 25, "offset": 0}
        if malformed == "missing_metadata":
            del data["total_count"]
        elif malformed == "wrong_project":
            member["project"]["id"] = 8
        elif malformed == "duplicate":
            values.append(member.copy())
            data["total_count"] = 2
        elif malformed == "principal":
            member["group"] = {"id": 12, "name": "private-error"}
        else:
            member["roles"] = [{"id": 4, "name": "private-error"}, {"id": 4, "name": "Different"}]
        return httpx.Response(200, json=data)

    synthetic.respond = respond
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-redmine-key"},
    ) as client:
        response = await client.get("/api/v1/projects/memberships", params={"project_ids": 7})
    row = response.json()["results"][0]
    assert row["outcome"] == "rejected" and row["error"]["code"] == "upstream_response"
    assert "private-error" not in response.text


@pytest.mark.asyncio
async def test_mcp_schemas_annotations_and_capabilities(writer_app: Any) -> None:
    async with mcp_session(writer_app) as session:
        tools = {t.name: t for t in (await session.list_tools()).tools}
        for operation in OPERATIONS.values():
            tool = tools[operation]
            assert tool.inputSchema["additionalProperties"] is False
            items_schema = tool.inputSchema["properties"]["items"]
            assert items_schema["maxItems"] == 10 and items_schema["minItems"] == 1
            assert tool.annotations.readOnlyHint is False
            assert tool.annotations.idempotentHint is False
            assert tool.annotations.destructiveHint is (operation != "add_project_members")
        assert tools["list_project_members"].annotations.readOnlyHint is True
        result = await session.call_tool("list_my_project_capabilities", {"project_id": 7})
        assert not result.isError
        data = json.loads(result.content[0].text)
        project = data["items"][0]
        for operation in OPERATIONS.values():
            report = next(t for t in project["tools"] if t["operation_id"] == operation)
            assert report["state"] == "conditional"
        assert "manage_members" in project["permissions"]


@pytest.mark.asyncio
async def test_scoped_writer_allowlist_exposes_only_selected_operation(
    application_factory: Any,
) -> None:
    async with application_factory(
        redmine_write_enabled=True,
        redmine_writer_operations="delete_project_members",
    ) as app:
        async with mcp_session(app) as session:
            names = {t.name for t in (await session.list_tools()).tools}
            assert names.intersection(WRITE_OPERATIONS) == {"delete_project_members"}
            assert "list_project_members" in names


@pytest.mark.asyncio
@pytest.mark.parametrize("budget", ["requests", "bytes"])
async def test_preflight_budget_rejection_has_zero_writes(
    application_factory: Any, synthetic: Any, budget: str
) -> None:
    settings = {
        "redmine_write_enabled": True,
        "redmine_writer_operations": "update_project_members",
    }
    settings[
        "redmine_membership_batch_max_requests"
        if budget == "requests"
        else "redmine_membership_batch_max_read_bytes"
    ] = 1 if budget == "requests" else 300
    async with application_factory(**settings) as app:
        status, result = await invoke(app, "update", [item("update", n) for n in (20, 21)])
    assert status == 200 and result["phase"] == "preflight_failed", result
    assert result["results"][0]["error"]["code"] == "scan_budget_exceeded"
    assert result["results"][1]["outcome"] == "not_executed"
    assert synthetic.writes == 0


@pytest.mark.asyncio
async def test_deadline_after_acceptance_keeps_receipt_and_stops_next_item(
    writer_app: Any, synthetic: Any
) -> None:
    from redmine_mcp.common.read_budget import current_budget

    original = synthetic.respond

    async def respond(request: Any) -> Any:
        response = await original(request)
        if request.method == "PUT":
            current_budget.get().started -= 1000
        return response

    synthetic.respond = respond
    status, result = await invoke(writer_app, "update", [item("update", n) for n in (20, 21)])
    assert status == 200 and result["phase"] == "executed", result
    first, second = result["results"]
    assert first["outcome"] == "accepted" and first["verification"] == "unavailable"
    assert first["error"]["code"] == "read_operation_timeout"
    assert second["outcome"] == "not_executed"
    assert synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["complete", "scope", "changed", "short"])
async def test_missing_user_expansion_requires_complete_inventory(
    application_factory: Any, synthetic: Any, mode: str
) -> None:
    synthetic.members = {n: membership(n, user_id=n + 1000) for n in range(1, 102)}
    original = synthetic.respond
    inventory_requests = []

    async def respond(request: Any) -> Any:
        response = await original(request)
        if request.url.path == "/users/20.json":
            return httpx.Response(200, json={"user": {"id": 20}})
        if request.method == "GET" and request.url.path == "/projects/7/memberships.json":
            inventory_requests.append(int(request.url.params["offset"]))
            data = response.json()
            if mode == "changed" and request.url.params["offset"] == "100":
                data["total_count"] += 1
            elif mode == "short":
                data["memberships"] = []
            return httpx.Response(200, json=data)
        return response

    synthetic.respond = respond
    async with application_factory(
        redmine_write_enabled=True,
        redmine_writer_operations="add_project_members",
        redmine_max_query_pages=1 if mode == "scope" else 10,
    ) as app:
        status, result = await invoke(app, "add", [item("add")])
    assert status == 200
    if mode == "complete":
        assert result["results"][0]["outcome"] == "accepted"
        # Each continuation uses a fresh offset-zero scope probe before page 100.
        assert inventory_requests == [0, 0, 100, 0, 0, 100]
        assert synthetic.writes == 1
    else:
        assert result["phase"] == "preflight_failed" and synthetic.writes == 0
        expected = {
            "scope": "scope_required",
            "changed": "membership_inventory_changed",
            "short": "upstream_response",
        }[mode]
        assert result["results"][0]["error"]["code"] == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("observation", ["not_found", "retained", "incomplete"])
async def test_delete_requires_positive_inventory_absence_proof(
    writer_app: Any, synthetic: Any, observation: str
) -> None:
    saved = copy.deepcopy(synthetic.members[20])
    original = synthetic.respond

    async def respond(request: Any) -> Any:
        response = await original(request)
        if synthetic.writes and request.url.path == "/projects/7/memberships.json":
            if observation == "not_found":
                return httpx.Response(404)
            data = response.json()
            if observation == "retained":
                data["memberships"].append(saved)
                data["total_count"] += 1
            else:
                data["total_count"] += 100
            return httpx.Response(200, json=data)
        return response

    synthetic.respond = respond
    status, result = await invoke(writer_app, "delete", [item("delete")])
    row = result["results"][0]
    assert status == 200 and row["outcome"] == "accepted"
    assert row["verification"] == ("mismatch" if observation == "retained" else "unavailable")
    assert row["observed_present"] is (True if observation == "retained" else None)
    assert synthetic.writes == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ["offline-redmine-key", "offline-rotated-key"])
async def test_writer_accepts_each_valid_caller_key(
    application_factory: Any, synthetic: Any, key: str
) -> None:
    async with application_factory(
        redmine_write_enabled=True,
        redmine_writer_operations="update_project_members",
    ) as app:
        status, result = await invoke(app, "update", [item("update")], key=key)
        assert status == 200 and result["results"][0]["outcome"] == "accepted"
    assert synthetic.writes == 1


@pytest.mark.asyncio
async def test_mixed_project_permission_preflight(writer_app: Any, synthetic: Any) -> None:
    original = synthetic.respond

    async def respond(request: Any) -> Any:
        response = await original(request)
        if request.url.path == "/users/current.json":
            data = response.json()
            data["user"]["memberships"].append(
                {
                    "id": 2,
                    "project": {"id": 8, "name": "Other"},
                    "roles": [{"id": 5, "name": "Reader"}],
                }
            )
            return httpx.Response(200, json=data)
        if request.url.path == "/roles/5.json":
            return httpx.Response(200, json={"role": {"id": 5, "permissions": []}})
        return response

    synthetic.respond = respond
    status, result = await invoke(writer_app, "add", [item("add"), item("add", project_id=8)])
    assert status == 200 and result["phase"] == "preflight_failed"
    assert [r["outcome"] for r in result["results"]] == ["not_executed", "rejected"]
    assert result["results"][1]["permission_state"] == "denied"
    assert synthetic.writes == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("action", OPERATIONS)
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("failure", [500, 503, 504])
async def test_received_server_error_preserves_batch_item_contract(
    writer_app: Any, synthetic: Any, action: str, boundary: str, failure: int
) -> None:
    synthetic.write_failure = failure
    status, result = await invoke(writer_app, action, [item(action)], boundary=boundary)
    assert status == 200 and result["phase"] == "executed"
    assert "outcome" not in result and "upstream_accepted" not in result
    row = result["results"][0]
    assert row["outcome"] == "uncertain" and row["verification"] == "unavailable"
    assert row["observed_present"] is None
    assert synthetic.writes == 1
    write_index = next(i for i, r in enumerate(synthetic.requests) if r.method != "GET")
    assert not any(
        r.method != "GET"
        or r.url.path.startswith("/memberships/")
        or r.url.path.endswith("/memberships.json")
        for r in synthetic.requests[write_index + 1 :]
    )
    assert "must-not-leak" not in json.dumps(result)


@pytest.mark.asyncio
@pytest.mark.parametrize("action", OPERATIONS)
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_allowed_all_admits_each_membership_writer(
    application_factory: Any, synthetic: Any, action: str, boundary: str
) -> None:
    async with application_factory(
        redmine_write_enabled=True,
        redmine_writer_operations="allowed_all",
    ) as app:
        await test_native_payload_single_attempt_and_readback(app, synthetic, action, boundary)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [500, 503, 504])
@pytest.mark.parametrize("stage", ["preflight", "readback", "recheck"])
async def test_batch_get_failures_preserve_phase_and_prior_receipts(
    writer_app: Any, synthetic: Any, failure: int, stage: str
) -> None:
    synthetic.members[22] = membership(22, user_id=12)
    original = synthetic.respond

    async def respond(request: Any) -> Any:
        response = await original(request)
        target = "/memberships/21.json" if stage == "recheck" else "/memberships/20.json"
        if request.method == "GET" and request.url.path == target:
            if stage == "preflight" or synthetic.writes:
                return httpx.Response(failure, json={"secret": "must-not-leak"})
        return response

    synthetic.respond = respond
    status, result = await invoke(writer_app, "update", [item("update", n) for n in (20, 21, 22)])
    assert status == 200
    outcomes = [row["outcome"] for row in result["results"]]
    if stage == "preflight":
        assert result["phase"] == "preflight_failed"
        assert outcomes == ["rejected", "not_executed", "not_executed"]
        assert synthetic.writes == 0
    elif stage == "readback":
        assert outcomes == ["accepted", "not_executed", "not_executed"]
        assert result["results"][0]["verification"] == "unavailable"
        assert synthetic.writes == 1
    else:
        assert outcomes == ["accepted", "rejected", "not_executed"]
        assert result["results"][0]["verification"] == "matched"
        assert synthetic.writes == 1
    assert "must-not-leak" not in json.dumps(result)
