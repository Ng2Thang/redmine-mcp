from collections.abc import AsyncIterator
from importlib import import_module
from typing import Any

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from pydantic import SecretStr

from redmine_mcp.config import Settings


@pytest.fixture
def fake_settings() -> Settings:
    return Settings(
        _env_file=None,
        redmine_url="http://redmine.invalid",
        redmine_api_key=SecretStr("offline-redmine-key"),
        mcp_api_token=SecretStr("offline-mcp-token"),
    )


@pytest.fixture
def upstream() -> dict[str, Any]:
    return {"requests": [], "status": 200, "body": {}}


@pytest_asyncio.fixture
async def app(
    monkeypatch: pytest.MonkeyPatch, fake_settings: Settings, upstream: dict[str, Any]
) -> AsyncIterator[FastAPI]:
    app_module = import_module("redmine_mcp.app")
    real_client = httpx.AsyncClient

    def respond(request: httpx.Request) -> httpx.Response:
        upstream["requests"].append(request)
        if upstream.get("exception") is not None:
            raise upstream["exception"]
        return httpx.Response(upstream["status"], json=upstream["body"])

    def client_factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        is_upstream = kwargs.get("base_url", "").startswith("http://redmine.invalid")
        if is_upstream:
            assert "transport" not in kwargs
            kwargs["transport"] = httpx.MockTransport(respond)
        else:
            assert isinstance(kwargs.get("transport"), httpx.ASGITransport)
        client = real_client(*args, **kwargs)
        upstream["upstream_client" if is_upstream else "internal_client"] = client
        return client

    monkeypatch.setattr(app_module, "Settings", lambda: fake_settings)
    monkeypatch.setattr(app_module.httpx, "AsyncClient", client_factory)
    instance = app_module.create_app()
    async with instance.router.lifespan_context(instance):
        yield instance
    assert upstream["upstream_client"].is_closed
    assert upstream["internal_client"].is_closed


@pytest_asyncio.fixture
async def rest_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Authorization": "Bearer offline-mcp-token"},
    ) as client:
        yield client
