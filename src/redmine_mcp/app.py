import httpx
from fastapi import FastAPI

from redmine_mcp.api import (
    RequestContextMiddleware,
    application_error,
    health_router,
    unexpected_error,
)
from redmine_mcp.common import ApplicationError
from redmine_mcp.config import Settings
from redmine_mcp.features.attachments.router import router as attachments_router
from redmine_mcp.features.attachments.write_router import metadata_router
from redmine_mcp.features.attachments.write_router import router as uploads_router
from redmine_mcp.features.issues.relation_write_router import router as relation_writes_router
from redmine_mcp.features.issues.router import router as issues_router
from redmine_mcp.features.issues.write_router import router as issue_writes_router
from redmine_mcp.features.projects.router import router as projects_router
from redmine_mcp.features.projects.write_router import router as project_writes_router
from redmine_mcp.features.reference_data.router import router as reference_data_router
from redmine_mcp.features.time_entries.router import router as time_entries_router
from redmine_mcp.features.users.router import router as users_router
from redmine_mcp.lifecycle import RuntimeLifecycle
from redmine_mcp.mcp import register_mcp
from redmine_mcp.observability import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = Settings() if settings is None else settings
    configure_logging(settings.log_level)

    app = FastAPI(title="Redmine MCP", version="0.1.0")
    app.state.settings = settings
    app.state.upstream = None
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(ApplicationError, application_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_error)
    app.include_router(health_router)
    app.include_router(projects_router)
    app.include_router(project_writes_router)
    app.include_router(attachments_router)
    app.include_router(uploads_router)
    app.include_router(metadata_router)
    app.include_router(issues_router)
    app.include_router(issue_writes_router)
    app.include_router(relation_writes_router)
    app.include_router(time_entries_router)
    app.include_router(reference_data_router)
    app.include_router(users_router)
    internal = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://apiserver",
        timeout=settings.redmine_timeout_seconds + 5,
    )
    app.state.mcp = register_mcp(app, internal, settings)
    runtime = RuntimeLifecycle(settings, internal, app.state.mcp)
    app.router.lifespan_context = runtime.lifespan
    return app
