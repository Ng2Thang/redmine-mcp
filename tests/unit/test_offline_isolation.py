"""The default suite must not reach configured external Redmine endpoints."""

import httpx
import pytest


@pytest.mark.asyncio
async def test_unmocked_httpx_request_is_rejected() -> None:
    async with httpx.AsyncClient(trust_env=False) as client:
        with pytest.raises(AssertionError, match="Offline tests attempted"):
            await client.get("http://redmine.invalid/")
