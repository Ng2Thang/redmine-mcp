"""Shared, credential-free HTTP transport configuration."""

import httpx

from redmine_mcp.config import Settings


def create_upstream_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=str(settings.redmine_url).rstrip("/") + "/",
        timeout=httpx.Timeout(
            settings.redmine_timeout_seconds,
            connect=settings.redmine_connect_timeout_seconds,
            pool=settings.redmine_pool_timeout_seconds,
        ),
        limits=httpx.Limits(
            max_connections=settings.redmine_max_connections,
            max_keepalive_connections=settings.redmine_max_keepalive_connections,
        ),
        follow_redirects=False,
    )
