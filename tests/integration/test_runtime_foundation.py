"""Authorized prep-004 offline acceptance for the prep-003 runtime contracts."""

import asyncio
import gzip
import logging
from contextlib import asynccontextmanager
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import Depends, FastAPI
from mcp.types import Tool
from starlette.requests import Request

from redmine_mcp.api.middleware import RequestContextMiddleware
from redmine_mcp.api.runtime import get_upstream
from redmine_mcp.api.security import require_read_access
from redmine_mcp.common import ApplicationError
from redmine_mcp.config import Settings
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.transport import create_upstream_client
from redmine_mcp.lifecycle import RuntimeLifecycle
from redmine_mcp.mcp.catalog import (
    OPERATIONS,
    validate_generated_tools,
    validate_operation_catalog,
)
from redmine_mcp.mcp.registration import shutdown_mcp, start_mcp
from redmine_mcp.observability import request_id
from tests.helpers import PROJECT, mcp_session

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [("X-Redmine-API-Key", "")],
        [("X-Redmine-API-Key", "   ")],
        [("X-Redmine-API-Key", "a"), ("X-Redmine-API-Key", "b")],
        [("X-Redmine-API-Key", "a\x00b")],
        [("X-Redmine-API-Key", "a b")],
        [("X-Redmine-API-Key", "x" * 513)],
        [(b"X-Redmine-API-Key", b"\xff")],
    ],
)
async def test_foundation_001_invalid_headers_never_dispatch(
    app: FastAPI,
    upstream: dict[str, Any],
    headers: list[Any],
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        result = await client.get("/api/v1/projects", headers=headers)
    assert result.status_code == 401
    assert upstream["requests"] == []


@pytest.mark.parametrize(
    ("status", "body", "expected"),
    [
        (401, {}, 401),
        (403, {}, 401),
        (200, {"user": {}}, 502),
        (200, {"user": {"id": True}}, 502),
        (200, {"user": {"id": "3"}}, 502),
        (200, {"user": {"id": -1}}, 502),
        (200, {"user": []}, 502),
    ],
)
async def test_foundation_001_identity_failure(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    status: int,
    body: dict[str, Any],
    expected: int,
) -> None:
    upstream["identity_response"] = status, body
    result = await rest_client.get("/api/v1/projects")
    assert result.status_code == expected
    assert len(upstream["requests"]) == 1


async def test_foundation_002_concurrent_keys_cookies_default_auth_and_redirects() -> None:
    requests: list[httpx.Request] = []

    async def respond(req: httpx.Request) -> httpx.Response:
        requests.append(req)
        await asyncio.sleep(0)
        if req.url.path == "/redirect.json":
            return httpx.Response(302, headers={"Location": "http://other.invalid/"})
        return httpx.Response(
            200,
            json={"key": req.headers["X-Redmine-API-Key"]},
            headers={"Set-Cookie": "session=secret; Path=/"},
        )

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=httpx.MockTransport(respond),
        auth=("default", "secret"),
        headers={"Authorization": "Bearer secret"},
        cookies={"existing": "secret"},
    ) as http:
        clients = [RedmineClient(http, "synthetic-a"), RedmineClient(http, "synthetic-b")]
        results = await asyncio.gather(*(c.get("projects.json", {}) for c in clients))
        assert results == [{"key": "synthetic-a"}, {"key": "synthetic-b"}]
        await clients[0].get("projects.json", {})
        with pytest.raises(ApplicationError) as error:
            await clients[0].get("redirect.json", {})
        assert error.value.status == 502
        assert len(requests) == 4
        assert all("cookie" not in r.headers and "authorization" not in r.headers for r in requests)
        for path in [
            "",
            "/projects.json",
            "../x",
            "https://other.invalid",
            "x?key=y",
            "x#y",
            "x\\y",
        ]:
            with pytest.raises(ValueError):
                await clients[0].get(path, {})
        assert len(requests) == 4


async def test_foundation_002_transport_settings(fake_settings: Settings) -> None:
    async with create_upstream_client(fake_settings) as http:
        assert http.auth is None
        assert not http.follow_redirects
        assert "authorization" not in http.headers
        assert "x-redmine-api-key" not in http.headers
        assert http.timeout.connect == fake_settings.redmine_connect_timeout_seconds
        assert http.timeout.pool == fake_settings.redmine_pool_timeout_seconds
        assert http.timeout.read == fake_settings.redmine_timeout_seconds


@pytest.mark.parametrize(
    ("exception", "expected", "code"),
    [
        (httpx.PoolTimeout("secret"), 503, "upstream_busy"),
        (httpx.ConnectTimeout("secret"), 504, "upstream_timeout"),
        (httpx.ReadTimeout("secret"), 504, "upstream_timeout"),
        (httpx.ConnectError("secret"), 502, "upstream_unavailable"),
    ],
)
async def test_foundation_003_transport_errors_no_retry(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    fake_settings: Settings,
    exception: Exception,
    expected: int,
    code: str,
) -> None:
    # This legacy mapping test explicitly exercises the supported retry-disable mode.
    fake_settings.redmine_read_retry_max_attempts = 1
    upstream["exception"] = exception
    result = await rest_client.get("/api/v1/projects")
    assert result.status_code == expected
    assert result.json()["error"]["code"] == code
    assert "secret" not in result.text
    assert len(upstream["requests"]) == 2


class TrackingStream(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes], delay: float = 0) -> None:
        self.chunks = chunks
        self.delay = delay
        self.closed = False
        self.reads = 0
        self.entered = asyncio.Event()

    async def __aiter__(self):
        self.entered.set()
        for chunk in self.chunks:
            self.reads += 1
            if self.delay:
                await asyncio.sleep(self.delay)
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


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
async def test_foundation_003_011_error_status_does_not_read_body(
    status: int,
    expected: int,
    code: str,
) -> None:
    stream = TrackingStream([b"secret" * 100000])
    requests: list[httpx.Request] = []

    def respond(req: httpx.Request) -> httpx.Response:
        requests.append(req)
        return httpx.Response(status, stream=stream)

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        with pytest.raises(ApplicationError) as error:
            await RedmineClient(http, "synthetic", ReadPolicy(retry_max_attempts=1)).get(
                "projects.json", {}
            )
    assert (error.value.status, error.value.code) == (expected, code)
    assert stream.closed and stream.reads == 0
    assert len(requests) == 1
    assert "secret" not in str(error.value)


@pytest.mark.parametrize(
    ("body", "limit", "code"),
    [
        (b"{}", 2, None),
        (b"{} ", 2, "upstream_response_too_large"),
        (b"not-json-secret", 100, "upstream_response"),
        (b"[]", 100, "upstream_response"),
    ],
    ids=["exact-limit", "overflow", "invalid-json", "non-object"],
)
async def test_foundation_011_stream_limit_json_and_closure(
    body: bytes,
    limit: int,
    code: str | None,
) -> None:
    stream = TrackingStream([body[:1], body[1:]])
    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=httpx.MockTransport(lambda req: httpx.Response(200, stream=stream)),
    ) as http:
        client = RedmineClient(http, "synthetic", ReadPolicy(max_response_bytes=limit))
        if code is None:
            assert await client.get("projects.json", {}) == {}
        else:
            with pytest.raises(ApplicationError) as error:
                await client.get("projects.json", {})
            assert (error.value.status, error.value.code) == (502, code)
    assert stream.closed


async def test_foundation_011_parser_recursion_failure_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Python builds differ in accepted nesting depth. Exercise the parser failure boundary
    # without assuming that valid JSON at a particular depth must fail.
    def fail_parse(content):
        raise RecursionError("sensitive-upstream-content")

    stream = TrackingStream([b"{}"])
    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=httpx.MockTransport(lambda req: httpx.Response(200, stream=stream)),
    ) as http:
        monkeypatch.setattr(
            import_module("redmine_mcp.integrations.redmine.client").json, "loads", fail_parse
        )
        with pytest.raises(ApplicationError) as error:
            await RedmineClient(http, "synthetic").get("projects.json", {})
    assert (error.value.status, error.value.code) == (502, "upstream_response")
    assert "sensitive-upstream-content" not in str(error.value)
    assert stream.closed


@pytest.mark.parametrize("cancel", [False, True])
async def test_foundation_011_deadline_and_cancellation_close_stream(cancel: bool) -> None:
    stream = TrackingStream([b"{}"], delay=10)
    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=httpx.MockTransport(lambda req: httpx.Response(200, stream=stream)),
    ) as http:
        client = RedmineClient(http, "synthetic", ReadPolicy(deadline_seconds=0.02))
        task = asyncio.create_task(client.get("projects.json", {}))
        await asyncio.wait_for(stream.entered.wait(), timeout=1)
        if cancel:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            with pytest.raises(ApplicationError) as error:
                await task
            assert (error.value.status, error.value.code) == (504, "upstream_timeout")
    assert stream.closed


@pytest.mark.parametrize("failure", ["before", "after", "cancel"])
async def test_foundation_004_stream_safe_failure_and_context_cleanup(
    failure: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    messages: list[dict[str, Any]] = []

    async def endpoint(scope, receive, send):
        if failure == "after":
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"partial", "more_body": True})
        if failure == "cancel":
            raise asyncio.CancelledError
        raise ValueError("caller-key-and-upstream-secret")

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/secret",
        "headers": [],
        "query_string": b"key=secret",
    }
    with caplog.at_level(logging.INFO):
        middleware = RequestContextMiddleware(endpoint)
        if failure == "cancel":
            with pytest.raises(asyncio.CancelledError):
                await middleware(scope, receive, send)
        elif failure == "after":
            with pytest.raises(RuntimeError) as error:
                await middleware(scope, receive, send)
            assert "caller-key" not in str(error.value)
            assert len([m for m in messages if m["type"] == "http.response.start"]) == 1
        else:
            await middleware(scope, receive, send)
            assert messages[0]["status"] == 500
            assert b"internal_error" in messages[-1]["body"]
    assert request_id.get() == "-"
    assert "caller-key-and-upstream-secret" not in caplog.text


async def test_foundation_005_concurrent_correlation_and_nested_inheritance(
    rest_client: httpx.AsyncClient,
    upstream: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    upstream["body"] = {"projects": [PROJECT], "total_count": 1}
    with caplog.at_level(logging.INFO):
        results = await asyncio.gather(
            *(
                rest_client.get(
                    "/api/v1/projects",
                    headers={
                        "X-Request-ID": "malicious-secret",
                        "X-Redmine-API-Key": "offline-redmine-key",
                    },
                )
                for _ in range(2)
            )
        )
    ids = [result.headers["x-request-id"] for result in results]
    assert len(set(ids)) == 2
    assert all(len(value) == 32 and value != "malicious-secret" for value in ids)
    log_ids = {
        getattr(record, "request_id", None)
        for record in caplog.records
        if record.name == "redmine_mcp.requests"
    }
    assert set(ids).issubset(log_ids)
    assert "malicious-secret" not in caplog.text
    assert "offline-redmine-key" not in caplog.text
    token = request_id.set("inherited-id")
    try:
        nested = await rest_client.get("/health")
        assert nested.headers["x-request-id"] == "inherited-id"
        assert request_id.get() == "inherited-id"
    finally:
        request_id.reset(token)
    assert request_id.get() == "-"


@pytest.mark.parametrize("failure", ["startup", "mcp-start", "shutdown", "none"])
async def test_foundation_009_partial_startup_cleanup_and_repeat_lifespan(
    fake_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    module = import_module("redmine_mcp.lifecycle")
    internal = httpx.AsyncClient()
    upstream = httpx.AsyncClient()
    mcp = AsyncMock()
    if failure == "startup":

        def factory(settings):
            raise RuntimeError("acquisition failure")
    else:

        def factory(settings):
            return upstream

    shutdown = AsyncMock(
        side_effect=RuntimeError("cleanup failure") if failure == "shutdown" else None
    )
    monkeypatch.setattr(module, "create_upstream_client", factory)
    monkeypatch.setattr(module, "shutdown_mcp", shutdown)
    monkeypatch.setattr(
        module,
        "start_mcp",
        AsyncMock(
            side_effect=RuntimeError("MCP startup failure") if failure == "mcp-start" else None
        ),
    )
    runtime = RuntimeLifecycle(fake_settings, internal, mcp)
    app = FastAPI()
    app.state.upstream = None
    try:
        if failure == "none":
            async with runtime.lifespan(app):
                assert app.state.upstream is upstream
        else:
            with pytest.raises(RuntimeError):
                async with runtime.lifespan(app):
                    assert app.state.upstream is upstream
        assert internal.is_closed
        if failure != "startup":
            assert upstream.is_closed and app.state.upstream is None
            shutdown.assert_awaited_once_with(mcp)
        with pytest.raises(RuntimeError):
            async with runtime.lifespan(app):
                pass
    finally:
        await upstream.aclose()
        await internal.aclose()


async def test_foundation_009_closed_client_runtime_error() -> None:
    app = FastAPI()
    client = httpx.AsyncClient()
    await client.aclose()
    app.state.upstream = client
    with pytest.raises(ApplicationError) as error:
        get_upstream(Request({"type": "http", "app": app}))
    assert (error.value.status, error.value.code) == (503, "service_unavailable")


@pytest.mark.parametrize("flat", [False, True])
@pytest.mark.parametrize("invalid", [None, "hidden", "duplicate", "schema", "auth", "method"])
async def test_foundation_012_catalog_rejects_invalid_exposure(
    monkeypatch: pytest.MonkeyPatch,
    flat: bool,
    invalid: str | None,
) -> None:
    app = FastAPI()
    for index, operation in enumerate(OPERATIONS):
        options = {
            "operation_id": operation,
            "response_model": dict,
            "dependencies": [Depends(require_read_access)],
        }
        if index == 0:
            if invalid == "hidden":
                options["include_in_schema"] = False
            if invalid == "schema":
                options["response_model"] = None
            if invalid == "auth":
                options["dependencies"] = []
        app.add_api_route(
            f"/api/v1/{operation}",
            lambda: {},
            methods=["POST" if index == 0 and invalid == "method" else "GET"],
            **options,
        )
    if invalid == "duplicate":
        app.add_api_route("/api/v1/duplicate", lambda: {}, operation_id=OPERATIONS[0])
    if flat:
        monkeypatch.setattr(import_module("fastapi.routing"), "iter_route_contexts", None)
    if invalid is None:
        validate_operation_catalog(app)
    else:
        with pytest.raises(ValueError):
            validate_operation_catalog(app)


async def test_foundation_012_generated_tool_mismatch() -> None:
    tools = [Tool(name=name, inputSchema={}) for name in OPERATIONS]
    validate_generated_tools(tools)
    for invalid in [tools[:-1], [*tools, tools[0]], [*tools, Tool(name="hidden", inputSchema={})]]:
        with pytest.raises(ValueError):
            validate_generated_tools(invalid)


async def test_foundation_007_009_mcp_hints_and_active_session_shutdown(
    app: FastAPI,
    upstream: dict[str, Any],
) -> None:
    upstream["body"] = {"projects": [PROJECT], "total_count": 1}
    async with mcp_session(app) as session:
        tools = (await session.list_tools()).tools
        assert {tool.name for tool in tools} == set(OPERATIONS)
        for tool in tools:
            assert tool.annotations is not None
            assert tool.annotations.readOnlyHint is True
            assert tool.annotations.destructiveHint is False
            assert tool.annotations.idempotentHint is True
            assert tool.annotations.openWorldHint is True
        result = await session.call_tool("list_projects", {})
        assert not result.isError


@pytest.mark.parametrize("outcome", ["ready", "cancel", "failure"])
async def test_mcp_startup_waits_for_readiness_and_cleans_failed_start(
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
) -> None:
    from fastapi_mcp import FastApiMCP
    from fastapi_mcp.transport.http import FastApiHttpSessionManager
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

    entered = asyncio.Event()
    release = asyncio.Event()
    closed = asyncio.Event()

    class ControlledManager(StreamableHTTPSessionManager):
        def __init__(self, **kwargs):
            pass

        @asynccontextmanager
        async def run(self):
            try:
                entered.set()
                if outcome == "failure":
                    raise ValueError("sensitive-startup-details")
                await release.wait()
                yield
            finally:
                closed.set()

    monkeypatch.setattr(
        import_module("redmine_mcp.mcp.compatibility"),
        "StreamableHTTPSessionManager",
        ControlledManager,
    )
    mcp = FastApiMCP(FastAPI())
    transport = FastApiHttpSessionManager(mcp.server)
    mcp._http_transport = transport
    start = asyncio.create_task(start_mcp(mcp))
    await asyncio.wait_for(entered.wait(), 1)
    assert not transport._manager_started
    if outcome == "ready":
        assert not start.done()
        release.set()
        await start
        assert transport._manager_started
        await shutdown_mcp(mcp)
    elif outcome == "cancel":
        start.cancel()
        with pytest.raises(asyncio.CancelledError):
            await start
    else:
        with pytest.raises(RuntimeError) as error:
            await start
        assert "sensitive-startup-details" not in str(error.value)
    assert closed.is_set()
    assert transport._manager_task.done()
    assert not transport._manager_started


async def test_foundation_009_shutdown_with_an_open_mcp_session(
    fake_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from redmine_mcp.app import create_app

    upstream = httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"user": {"id": 3}})),
    )
    monkeypatch.setattr(
        import_module("redmine_mcp.lifecycle"), "create_upstream_client", lambda settings: upstream
    )
    instance = create_app(fake_settings)
    async with instance.router.lifespan_context(instance):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=instance), base_url="http://testserver"
        ) as http:
            result = await http.post(
                "/mcp",
                headers={
                    "X-Redmine-API-Key": "synthetic",
                    "Accept": "application/json, text/event-stream",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "offline", "version": "1"},
                    },
                },
            )
        assert result.status_code == 200
        assert "mcp-session-id" in result.headers
        transport = instance.state.mcp._http_transport
        assert not transport._manager_task.done()
        assert not instance.state.mcp._http_client.is_closed
    assert transport._manager_task.done()
    assert not transport._manager_started
    assert instance.state.mcp._http_client.is_closed
    assert upstream.is_closed


async def test_foundation_011_limit_applies_to_decoded_gzip_body() -> None:
    stream = TrackingStream([gzip.compress(b'{"text":"' + b"x" * 1000 + b'"}')])
    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=httpx.MockTransport(
            lambda req: httpx.Response(200, stream=stream, headers={"Content-Encoding": "gzip"})
        ),
    ) as http:
        with pytest.raises(ApplicationError) as error:
            await RedmineClient(http, "synthetic", ReadPolicy(max_response_bytes=100)).get(
                "projects.json", {}
            )
    assert error.value.code == "upstream_response_too_large"
    assert stream.closed
