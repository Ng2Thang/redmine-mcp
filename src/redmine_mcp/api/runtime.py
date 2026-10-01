import httpx
from fastapi import Request
from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.config import Settings
from redmine_mcp.constants import api as api_text
from redmine_mcp.constants import codes as codes_text


def get_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if not isinstance(settings, Settings):
        raise ApplicationError(
            codes_text.SERVICE_UNAVAILABLE,
            api_text.RUNTIME_UNAVAILABLE,
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return settings


def get_upstream(request: Request) -> httpx.AsyncClient:
    client = getattr(request.app.state, "upstream", None)
    if not isinstance(client, httpx.AsyncClient) or client.is_closed:
        raise ApplicationError(
            codes_text.SERVICE_UNAVAILABLE,
            api_text.RUNTIME_UNAVAILABLE,
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return client
