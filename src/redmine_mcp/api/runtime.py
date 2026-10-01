import httpx
from fastapi import Request
from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.config import Settings


def get_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if not isinstance(settings, Settings):
        raise ApplicationError(
            "service_unavailable",
            "Server runtime is unavailable",
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return settings


def get_upstream(request: Request) -> httpx.AsyncClient:
    client = getattr(request.app.state, "upstream", None)
    if not isinstance(client, httpx.AsyncClient) or client.is_closed:
        raise ApplicationError(
            "service_unavailable",
            "Server runtime is unavailable",
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return client
