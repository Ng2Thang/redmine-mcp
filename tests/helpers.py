"""Synthetic data and in-process MCP sessions shared by offline tests."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

PROJECT = {"id": 7, "identifier": "demo", "name": "Demo", "status": 1}
ISSUE = {
    "id": 42,
    "subject": "Offline example",
    "project": {"id": 7, "name": "Demo"},
    "tracker": {"id": 1, "name": "Bug"},
    "status": {"id": 1, "name": "New"},
    "priority": {"id": 2, "name": "Normal"},
    "author": {"id": 3, "name": "Example"},
    "created_on": "2026-09-30T00:00:00Z",
    "updated_on": "2026-09-30T00:00:00Z",
}


@asynccontextmanager
async def mcp_session(
    app: FastAPI, token: str | None = "offline-redmine-key"
) -> AsyncGenerator[ClientSession]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-Redmine-API-Key": token} if token is not None else {},
    ) as client:
        async with streamable_http_client("http://testserver/mcp", http_client=client) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                yield session
