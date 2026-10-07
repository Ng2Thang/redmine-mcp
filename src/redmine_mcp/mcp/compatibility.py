"""Own private hooks for FastAPI-MCP 0.4.0 and MCP SDK 1.30.0."""

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from importlib.metadata import version
from typing import Any, cast

import httpx
from fastapi import Request
from fastapi_mcp import FastApiMCP
from fastapi_mcp.transport.http import FastApiHttpSessionManager
from mcp import types
from mcp.server.lowlevel.server import Server
from mcp.server.streamable_http import EventStore
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings

from redmine_mcp.config import Settings
from redmine_mcp.constants import runtime as runtime_text

CallToolHandler = Callable[[types.CallToolRequest], Awaitable[types.ServerResult]]
ListToolsHandler = Callable[[types.ListToolsRequest | None], Awaitable[types.ServerResult]]
RestRequestHook = Callable[
    [httpx.AsyncClient, str, str, dict[str, Any], dict[str, str], Any], Awaitable[Any]
]


def _failure() -> RuntimeError:
    return RuntimeError(runtime_text.MCP_START_FAILED)


def _async_callable(value: object, *arguments: object) -> bool:
    if not inspect.iscoroutinefunction(value):
        return False
    try:
        inspect.signature(value).bind(*arguments)
    except (TypeError, ValueError):
        return False
    return True


class MCPCompatibility:
    """Per-application access to checked vendor hooks; policy stays in callers."""

    def __init__(self, mcp: FastApiMCP) -> None:
        self.mcp = mcp
        self.check_versions()
        self._validate_registration()

    def _manager_options(self, transport: FastApiHttpSessionManager) -> dict[str, Any]:
        options: dict[str, Any] = {
            "app": transport.mcp_server,
            "event_store": transport.event_store,
            "json_response": transport.json_response,
            "stateless": False,
            "security_settings": transport.security_settings,
        }
        settings = getattr(self.mcp.fastapi.state, "settings", None)
        if isinstance(settings, Settings):
            # Keep SDK admission aligned with the outer, pre-authentication byte cap.
            options["max_request_body_size"] = settings.effective_max_request_body_bytes
        return options

    @staticmethod
    def check_versions() -> None:
        try:
            if version("fastapi-mcp") != "0.4.0" or version("mcp") != "1.30.0":
                raise _failure()
        except Exception:
            raise _failure() from None

    def _validate_registration(self) -> None:
        try:
            server = self.mcp.server
            if not isinstance(server, Server):
                raise _failure()
            if not isinstance(inspect.getattr_static(server, "request_context"), property):
                raise _failure()
            handlers = server.request_handlers
            cache = server._tool_cache
            if not isinstance(handlers, dict) or not isinstance(cache, dict):
                raise _failure()
            if not all(
                isinstance(name, str) and isinstance(tool, types.Tool)
                for name, tool in cache.items()
            ):
                raise _failure()
            if not all(
                _async_callable(handlers.get(kind), None)
                for kind in (types.CallToolRequest, types.ListToolsRequest)
            ):
                raise _failure()
            if not isinstance(self.mcp.tools, list) or not all(
                isinstance(tool, types.Tool) for tool in self.mcp.tools
            ):
                raise _failure()
            if not _async_callable(self.mcp._request, None, None, None, None, None, None):
                raise _failure()
            inspect.signature(self.mcp.mount_http).bind()
        except Exception:
            raise _failure() from None

    def snapshot_tools(self) -> tuple[types.Tool, ...]:
        return tuple(tool.model_copy(deep=True) for tool in self.mcp.tools)

    def seed_tool_cache(self) -> None:
        """Publish the full repaired deployment superset before handler wrapping."""
        tools = self.snapshot_tools()
        cache = self.mcp.server._tool_cache
        cache.clear()
        cache.update({tool.name: tool for tool in tools})

    def call_tool_handler(self) -> CallToolHandler:
        return cast(CallToolHandler, self.mcp.server.request_handlers[types.CallToolRequest])

    def list_tools_handler(self) -> ListToolsHandler:
        return cast(ListToolsHandler, self.mcp.server.request_handlers[types.ListToolsRequest])

    def install_call_tool_handler(self, handler: CallToolHandler) -> None:
        if not _async_callable(handler, None):
            raise _failure()
        self.mcp.server.request_handlers[types.CallToolRequest] = handler

    def install_list_tools_handler(self, handler: ListToolsHandler) -> None:
        if not _async_callable(handler, None):
            raise _failure()
        self.mcp.server.request_handlers[types.ListToolsRequest] = handler

    def original_request(self) -> Request | None:
        """Return the SDK's original HTTP request, never a synthetic auth context."""
        try:
            request = self.mcp.server.request_context.request
        except (LookupError, AttributeError):
            return None
        return request if isinstance(request, Request) else None

    def install_membership_delete_body(self) -> None:
        original = cast(RestRequestHook, self.mcp._request)

        async def request(
            client: httpx.AsyncClient,
            method: str,
            path: str,
            query: dict[str, Any],
            headers: dict[str, str],
            body: Any | None,
        ) -> Any:
            if method.lower() == "delete" and path == "/api/v1/projects/memberships/batch":
                return await client.request(
                    "DELETE", path, params=query, headers=headers, json=body
                )
            return await original(client, method, path, query, headers, body)

        self.mcp._request = request

    def mount_transport(self) -> None:
        try:
            self.mcp.mount_http()
            self.validate_transport()
        except Exception:
            raise _failure() from None

    def validate_transport(self) -> FastApiHttpSessionManager:
        """Check mounted transport and lifecycle shapes without starting resources."""
        try:
            transport = self.mcp._http_transport
            if not isinstance(transport, FastApiHttpSessionManager):
                raise _failure()
            if transport.mcp_server is not self.mcp.server:
                raise _failure()
            if (
                type(transport.json_response) is not bool
                or type(transport._manager_started) is not bool
            ):
                raise _failure()
            if transport.event_store is not None and not isinstance(
                transport.event_store, EventStore
            ):
                raise _failure()
            if transport.security_settings is not None and not isinstance(
                transport.security_settings, TransportSecuritySettings
            ):
                raise _failure()
            if not isinstance(transport._startup_lock, asyncio.Lock):
                raise _failure()
            if transport._manager_task is not None and not isinstance(
                transport._manager_task, asyncio.Task
            ):
                raise _failure()
            if transport._session_manager is not None and not isinstance(
                transport._session_manager, StreamableHTTPSessionManager
            ):
                raise _failure()
            if not _async_callable(transport.shutdown):
                raise _failure()
            inspect.signature(StreamableHTTPSessionManager).bind(**self._manager_options(transport))
            inspect.signature(StreamableHTTPSessionManager.run).bind(None)
            if not inspect.isasyncgenfunction(inspect.unwrap(StreamableHTTPSessionManager.run)):
                raise _failure()
            if not _async_callable(
                StreamableHTTPSessionManager.handle_request, None, None, None, None
            ):
                raise _failure()
            return transport
        except Exception:
            raise _failure() from None

    async def start(self) -> None:
        transport = self.validate_transport()
        if transport._manager_started or transport._manager_task is not None:
            raise _failure()
        try:
            manager = StreamableHTTPSessionManager(**self._manager_options(transport))
        except Exception:
            raise _failure() from None
        transport._session_manager = manager
        ready: asyncio.Future[None] = asyncio.get_running_loop().create_future()

        async def run_manager() -> None:
            try:
                async with manager.run():
                    if not ready.done():
                        ready.set_result(None)
                    await asyncio.Event().wait()
            except BaseException as exc:
                if not ready.done():
                    ready.set_exception(_failure())
                if not isinstance(exc, Exception):
                    raise
                raise _failure() from None

        task = asyncio.create_task(run_manager())
        transport._manager_task = task

        def finish_startup(_task: asyncio.Task[None]) -> None:
            # Cancellation before the coroutine's first step cannot run its exception handler.
            if not ready.done():
                ready.set_exception(_failure())

        task.add_done_callback(finish_startup)
        try:
            await ready
            if task.done():
                raise _failure()
        except BaseException:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            raise
        # FastAPI-MCP must not advertise readiness before the SDK run context yields.
        transport._manager_started = True

    async def shutdown(self) -> None:
        if self.mcp._http_transport is None:
            return
        transport = self.validate_transport()
        try:
            task = transport._manager_task
            if task is not None:
                if not task.done():
                    task.cancel()
                # Consume owned task failures without logging vendor exception contents.
                # External cancellation still propagates instead of being swallowed.
                await asyncio.gather(task, return_exceptions=True)
        finally:
            transport._manager_started = False
