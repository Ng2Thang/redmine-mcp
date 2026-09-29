from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from redmine_mcp.api.error_handlers import application_error
from redmine_mcp.api.health import router as health_router
from redmine_mcp.bootstrap import build_container
from redmine_mcp.common.errors import ApplicationError
from redmine_mcp.config import Settings
from redmine_mcp.features.issues.router import router as issues_router
from redmine_mcp.features.projects.router import router as projects_router
from redmine_mcp.mcp.registration import register_mcp, shutdown_mcp
from redmine_mcp.observability import configure_logging


def create_app() -> FastAPI:
    settings = Settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(
            base_url=str(settings.redmine_url).rstrip("/") + "/",
            headers={"X-Redmine-API-Key": settings.redmine_api_key.get_secret_value()},
            timeout=settings.redmine_timeout_seconds,
            follow_redirects=False,
        ) as upstream:
            app.state.container = build_container(upstream)
            try:
                yield
            finally:
                try:
                    await shutdown_mcp(app.state.mcp)
                finally:
                    await internal.aclose()

    app = FastAPI(title="Redmine MCP", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_exception_handler(ApplicationError, application_error)  # type: ignore[arg-type]
    app.include_router(health_router)
    app.include_router(projects_router)
    app.include_router(issues_router)
    internal = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://apiserver",
        timeout=settings.redmine_timeout_seconds + 5,
    )
    app.state.mcp = register_mcp(app, internal)
    return app
