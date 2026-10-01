"""Own runtime resources and their startup/shutdown ordering."""

from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

from redmine_mcp.config import Settings
from redmine_mcp.integrations.redmine import create_upstream_client
from redmine_mcp.mcp import shutdown_mcp


class RuntimeLifecycle:
    def __init__(self, settings: Settings, internal: httpx.AsyncClient, mcp: FastApiMCP) -> None:
        self.settings = settings
        self.internal = internal
        self.mcp = mcp
        self.started = False

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None]:
        if self.started:
            raise RuntimeError("Create a new application instance for each runtime lifespan")
        self.started = True
        async with AsyncExitStack() as resources:
            # Register cleanup before any later resource acquisition can fail.
            resources.push_async_callback(self.internal.aclose)
            upstream = await resources.enter_async_context(create_upstream_client(self.settings))
            resources.push_async_callback(shutdown_mcp, self.mcp)
            app.state.upstream = upstream
            try:
                yield
            finally:
                app.state.upstream = None
