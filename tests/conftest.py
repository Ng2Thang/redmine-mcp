import os
from collections.abc import AsyncIterator
from importlib import import_module
from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi import status as http_status
from pydantic import SecretStr

from redmine_mcp.config import Settings


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-e2e", action="store_true", help="Enable owned synthetic live tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    live = [item for item in items if "e2e" in Path(str(item.path)).parts]
    if live and not config.getoption("--run-e2e"):
        raise pytest.UsageError("Live tests require: pytest tests/e2e --run-e2e")
    for item in live:
        item.add_marker(pytest.mark.e2e)


@pytest.fixture(autouse=True)
def offline_isolation(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.get_closest_marker("e2e"):
        return
    for name in tuple(os.environ):
        if name.upper().startswith("REDMINE_"):
            monkeypatch.delenv(name, raising=False)

    def blocked(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Offline tests attempted an external network request")

    async def blocked_async(*args: Any, **kwargs: Any) -> None:
        blocked()

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked_async)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)


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
    return {"requests": [], "status": http_status.HTTP_200_OK, "body": {}}


@pytest_asyncio.fixture
async def app(
    monkeypatch: pytest.MonkeyPatch, fake_settings: Settings, upstream: dict[str, Any]
) -> AsyncIterator[FastAPI]:
    app_module = import_module("redmine_mcp.app")
    lifecycle_module = import_module("redmine_mcp.lifecycle")

    async def respond(request: httpx.Request) -> httpx.Response:
        upstream["requests"].append(request)
        if upstream.get("handler") is not None:
            return await upstream["handler"](request)
        if request.url.path == "/users/current.json":
            if upstream.get("identity_response") is not None and not request.url.params:
                status, body = upstream["identity_response"]
                return httpx.Response(status, json=body)
            if request.headers.get("X-Redmine-API-Key") != "offline-redmine-key":
                return httpx.Response(http_status.HTTP_401_UNAUTHORIZED, json={})
            if request.url.params.get("include") == "memberships":
                if upstream.get("profile_response") is not None:
                    status, body = upstream["profile_response"]
                    return httpx.Response(status, json=body)
                return httpx.Response(
                    http_status.HTTP_200_OK,
                    json={
                        "user": {
                            "id": 3,
                            "login": "offline-reader",
                            "firstname": "Offline",
                            "lastname": "Reader",
                            "memberships": [],
                            "api_key": "upstream-secret-must-not-leak",
                        }
                    },
                )
            return httpx.Response(
                http_status.HTTP_200_OK,
                json={"user": {"id": 3, "login": "offline-reader"}},
            )
        if upstream.get("exception") is not None:
            raise upstream["exception"]
        status, body = upstream.get("responses", {}).get(
            request.url.path, (upstream["status"], upstream["body"])
        )
        if (
            request.url.params.get("limit") == "1"
            and request.url.params.get("offset") == "0"
            and isinstance(body, dict)
        ):
            body = dict(body)
            for collection in ("projects", "issues", "time_entries"):
                if isinstance(body.get(collection), list):
                    body[collection] = body[collection][:1]
            if "limit" in body:
                body["limit"] = 1
            if "offset" in body:
                body["offset"] = 0
        return httpx.Response(status, json=body)

    def create_upstream_client(settings: Settings) -> httpx.AsyncClient:
        assert settings is fake_settings
        client = httpx.AsyncClient(
            base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
        )
        upstream["upstream_client"] = client
        return client

    monkeypatch.setattr(lifecycle_module, "create_upstream_client", create_upstream_client)
    instance = app_module.create_app(fake_settings)
    async with instance.router.lifespan_context(instance):
        yield instance
    assert upstream["upstream_client"].is_closed


@pytest_asyncio.fixture
async def rest_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": "offline-redmine-key"},
    ) as client:
        yield client
