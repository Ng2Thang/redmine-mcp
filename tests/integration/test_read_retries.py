"""PREP-027 REST/MCP retry ownership, permissions, pagination and writer receipts."""

import asyncio
import json
from collections import Counter
from importlib import import_module
from typing import Any

import httpx
import pytest

from redmine_mcp.common.read_budget import current_budget
from tests.helpers import mcp_session
from tests.retry_helpers import RetryClock


@pytest.fixture
def retry_clock(monkeypatch: Any) -> RetryClock:
    clock = RetryClock()
    module = import_module("redmine_mcp.integrations.redmine.client")
    monkeypatch.setattr(module, "RetryRuntime", clock.runtime)
    return clock


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("stage", ["identity", "detail", "exhausted", "malformed", "forbidden"])
@pytest.mark.asyncio
async def test_reader_recovery_and_errors_dispatch_operation_once(
    application_factory: Any,
    synthetic: Any,
    monkeypatch: Any,
    retry_clock: Any,
    boundary: str,
    stage: str,
) -> None:
    original = synthetic.respond
    counts: Counter[str] = Counter()

    async def respond(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        counts[path] += 1
        target = "/users/current.json" if stage == "identity" else "/issues/42.json"
        if path == target:
            if stage in ("identity", "detail") and counts[path] == 1 or stage == "exhausted":
                return httpx.Response(503, json={"private": "must-not-leak"})
            if stage == "forbidden":
                return httpx.Response(403)
            if stage == "malformed":
                return httpx.Response(200, json={"issue": {"id": "42"}})
        return await original(request)

    monkeypatch.setattr(synthetic, "respond", respond)
    async with application_factory() as app:
        if boundary == "rest":
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": "offline-redmine-key"},
            ) as http:
                response = await http.get("/api/v1/issues/42")
                result = response.json()
                is_error = response.is_error
        else:
            async with mcp_session(app) as session:
                response = await session.call_tool("get_issue", {"issue_id": 42})
                is_error = response.isError
                result = json.loads(response.content[0].text)
    if stage in ("identity", "detail"):
        assert not is_error and result["id"] == 42
    else:
        assert is_error and "must-not-leak" not in json.dumps(result)
        assert (
            result["error"]["code"]
            == {
                "exhausted": "upstream_unavailable",
                "malformed": "upstream_response",
                "forbidden": "access_denied",
            }[stage]
        )
    assert counts["/issues/42.json"] == (
        3 if stage == "exhausted" else 2 if stage == "detail" else 1
    )


@pytest.mark.parametrize("stage", ["profile", "roles"])
@pytest.mark.asyncio
async def test_discovery_recovers_only_its_failed_permission_get(
    writer_app: Any,
    synthetic: Any,
    monkeypatch: Any,
    retry_clock: Any,
    stage: str,
) -> None:
    original = synthetic.respond
    failures = 0
    counts: Counter[str] = Counter()

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal failures
        profile = (
            request.url.path == "/users/current.json"
            and request.url.params.get("include") == "memberships"
        )
        roles = request.url.path == "/roles/4.json"
        counts[str(request.url)] += 1
        if (profile if stage == "profile" else roles) and failures == 0:
            failures += 1
            return httpx.Response(502)
        return await original(request)

    monkeypatch.setattr(synthetic, "respond", respond)
    async with mcp_session(writer_app) as session:
        result = await session.list_tools()
    assert "update_issue" in {tool.name for tool in result.tools}
    assert failures == 1 and retry_clock.waits == [0.5]
    target = (
        "http://redmine.invalid/users/current.json?include=memberships"
        if stage == "profile"
        else "http://redmine.invalid/roles/4.json"
    )
    assert counts[target] == 2


@pytest.mark.asyncio
async def test_pagination_probe_is_not_replayed_when_requested_page_retries(
    application_factory: Any,
    synthetic: Any,
    monkeypatch: Any,
    retry_clock: Any,
) -> None:
    original = synthetic.respond
    query_counts: Counter[str] = Counter()

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/issues.json":
            offset = request.url.params["offset"]
            query_counts[offset] += 1
            if offset == "1" and query_counts[offset] == 1:
                return httpx.Response(504)
        return await original(request)

    monkeypatch.setattr(synthetic, "respond", respond)
    async with application_factory() as app:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-redmine-key"},
        ) as http:
            response = await http.get("/api/v1/issues", params={"limit": 1, "offset": 1})
    assert response.status_code == 200
    assert query_counts == {"0": 1, "1": 2}


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("stage", ["preflight", "readback", "exhausted"])
@pytest.mark.asyncio
async def test_writer_retries_reads_and_preserves_single_accepted_mutation(
    writer_app: Any,
    synthetic: Any,
    monkeypatch: Any,
    retry_clock: Any,
    boundary: str,
    stage: str,
) -> None:
    original = synthetic.respond
    faults = 0
    readbacks = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal faults, readbacks
        issue_get = request.method == "GET" and request.url.path == "/issues/42.json"
        if issue_get and synthetic.writes:
            readbacks += 1
        selected = issue_get and (
            not synthetic.writes if stage == "preflight" else bool(synthetic.writes)
        )
        if selected and (faults == 0 or stage == "exhausted"):
            faults += 1
            return httpx.Response(503)
        response = await original(request)
        if request.method == "POST" and request.url.path == "/issues/42/watchers.json":
            synthetic.issues[42]["watchers"] = [{"id": 8, "name": "Reader"}]
        return response

    monkeypatch.setattr(synthetic, "respond", respond)
    if boundary == "rest":
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(writer_app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-redmine-key"},
        ) as http:
            response = await http.post("/api/v1/issues/42/watchers", json={"user_id": 8})
            assert response.status_code == 200
            result = response.json()
    else:
        async with mcp_session(writer_app) as session:
            response = await session.call_tool("add_issue_watcher", {"issue_id": 42, "user_id": 8})
            assert not response.isError
            result = json.loads(response.content[0].text)
    assert (
        synthetic.writes == 1
        and result["outcome"] == "accepted"
        and result["upstream_accepted"] is True
    )
    assert result["verification"] == ("unavailable" if stage == "exhausted" else "matched")
    assert faults == (3 if stage == "exhausted" else 1)
    assert readbacks == (3 if stage == "exhausted" else 2 if stage == "readback" else 1)


@pytest.mark.asyncio
async def test_cooperative_batch_expiry_keeps_accepted_peer_and_stops_later_writes(
    writer_app: Any,
    synthetic: Any,
    monkeypatch: Any,
    retry_clock: Any,
) -> None:
    original = synthetic.respond
    budget_module = import_module("redmine_mcp.common.read_budget")
    monkeypatch.setattr(budget_module, "monotonic", retry_clock.time)

    async def respond(request: httpx.Request) -> httpx.Response:
        if (
            synthetic.writes
            and request.method == "GET"
            and request.url.path == "/memberships/20.json"
        ):
            budget = current_budget.get()
            assert budget is not None
            retry_clock.now = budget.deadline + 0.01
            raise httpx.ReadError("private")
        return await original(request)

    monkeypatch.setattr(synthetic, "respond", respond)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(writer_app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-redmine-key"},
    ) as http:
        response = await http.put(
            "/api/v1/projects/memberships/batch",
            json={
                "items": [
                    {"project_id": 7, "membership_id": member, "role_ids": [4]}
                    for member in (20, 21)
                ]
            },
        )
    assert response.status_code == 200
    first, second = response.json()["results"]
    assert first["outcome"] == "accepted" and first["verification"] == "unavailable"
    assert first["error"]["code"] == "read_operation_timeout"
    assert second["outcome"] == "not_executed" and synthetic.writes == 1


@pytest.mark.asyncio
async def test_internal_asgi_timeout_setting_does_not_replay_or_end_the_tool(
    application_factory: Any,
    synthetic: Any,
    monkeypatch: Any,
) -> None:
    original = synthetic.respond
    issues = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal issues
        if request.url.path == "/issues/42.json":
            issues += 1
            await asyncio.sleep(0.005)
        return await original(request)

    monkeypatch.setattr(synthetic, "respond", respond)
    async with application_factory() as app:
        app.state.mcp._http_client.timeout = httpx.Timeout(0.000001)
        async with mcp_session(app) as session:
            response = await session.call_tool("get_issue", {"issue_id": 42})
    assert not response.isError and issues == 1
