"""SDK-026: fail closed on incompatible hooks and own lifecycle cleanup."""

import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from mcp import types

from redmine_mcp.mcp import compatibility as boundary
from redmine_mcp.mcp.compatibility import MCPCompatibility

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def adapter():
    app = FastAPI()

    @app.get("/example", operation_id="example")
    async def example(value: int = 1):
        return {"value": value}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://offline"
    ) as client:
        yield FastApiMCP(app, http_client=client)


@pytest.mark.parametrize("package,version", [("mcp", "1.31.0"), ("fastapi-mcp", "0.5.0")])
async def test_version_mismatch_is_safe(adapter, monkeypatch, package, version):
    original = boundary.version
    monkeypatch.setattr(
        boundary, "version", lambda name: version if name == package else original(name)
    )
    with pytest.raises(RuntimeError, match="^MCP session manager startup failed$"):
        MCPCompatibility(adapter)


@pytest.mark.parametrize("fault", ["cache", "cache_entry", "handler", "request", "tools", "mount"])
async def test_registration_shape_fault_is_safe(adapter, fault):
    if fault == "cache":
        adapter.server._tool_cache = []
    elif fault == "cache_entry":
        adapter.server._tool_cache = {"sensitive": object()}
    elif fault == "handler":
        adapter.server.request_handlers[types.CallToolRequest] = lambda request: None
    elif fault == "request":
        adapter._request = lambda *args: None
    elif fault == "tools":
        adapter.tools = [object()]
    else:
        adapter.mount_http = lambda mandatory: None
    with pytest.raises(RuntimeError, match="^MCP session manager startup failed$"):
        MCPCompatibility(adapter)


@pytest.mark.parametrize(
    "field,value",
    [
        ("_startup_lock", None),
        ("_manager_started", 1),
        ("json_response", "true"),
        ("_manager_task", object()),
        ("_session_manager", object()),
        ("security_settings", {}),
        ("event_store", object()),
        ("mcp_server", object()),
    ],
)
async def test_transport_shape_fault_is_safe(adapter, field, value):
    compatibility = MCPCompatibility(adapter)
    compatibility.mount_transport()
    setattr(adapter._http_transport, field, value)
    with pytest.raises(RuntimeError, match="^MCP session manager startup failed$"):
        await compatibility.start()


async def test_cache_and_snapshot_are_deep_copies_per_application(adapter):
    compatibility = MCPCompatibility(adapter)
    compatibility.seed_tool_cache()
    snapshot = compatibility.snapshot_tools()
    adapter.tools[0].inputSchema["properties"].clear()
    assert snapshot[0].inputSchema["properties"]
    assert adapter.server._tool_cache["example"].inputSchema["properties"]
    snapshot[0].inputSchema["properties"].clear()
    assert adapter.server._tool_cache["example"].inputSchema["properties"]
    assert compatibility.original_request() is None


async def test_cancel_before_manager_first_step_completes_startup(adapter, monkeypatch):
    compatibility = MCPCompatibility(adapter)
    compatibility.mount_transport()
    original = asyncio.create_task

    def cancel_task(coroutine):
        task = original(coroutine)
        task.cancel()
        return task

    monkeypatch.setattr(boundary.asyncio, "create_task", cancel_task)
    with pytest.raises(RuntimeError, match="^MCP session manager startup failed$"):
        await asyncio.wait_for(compatibility.start(), 1)
    assert adapter._http_transport._manager_task.done()
    assert not adapter._http_transport._manager_started
    await compatibility.shutdown()


async def test_real_manager_start_shutdown_and_duplicate_start(adapter):
    compatibility = MCPCompatibility(adapter)
    compatibility.mount_transport()
    await asyncio.wait_for(compatibility.start(), 1)
    assert adapter._http_transport._manager_started
    with pytest.raises(RuntimeError, match="^MCP session manager startup failed$"):
        await compatibility.start()
    await asyncio.wait_for(compatibility.shutdown(), 1)
    assert adapter._http_transport._manager_task.done()
    assert not adapter._http_transport._manager_started


async def test_shutdown_cancellation_propagates_and_cleans_flag(adapter, monkeypatch):
    closed = asyncio.Event()
    exiting = asyncio.Event()

    class SlowExit(boundary.StreamableHTTPSessionManager):
        @asynccontextmanager
        async def run(self):
            try:
                yield
            finally:
                exiting.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    closed.set()

    monkeypatch.setattr(boundary, "StreamableHTTPSessionManager", SlowExit)
    compatibility = MCPCompatibility(adapter)
    compatibility.mount_transport()
    await compatibility.start()
    shutdown = asyncio.create_task(compatibility.shutdown())
    await asyncio.wait_for(exiting.wait(), 1)
    shutdown.cancel()
    with pytest.raises(asyncio.CancelledError):
        await shutdown
    assert closed.is_set() and adapter._http_transport._manager_task.done()
    assert not adapter._http_transport._manager_started
