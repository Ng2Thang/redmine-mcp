import asyncio
import json
import logging
from time import perf_counter
from typing import Any

import httpx
from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.integrations.redmine.policy import ReadPolicy

logger = logging.getLogger(__name__)


def raise_for_upstream_status(status: int) -> None:
    failures = {
        http_status.HTTP_401_UNAUTHORIZED: (
            "invalid_credentials",
            "Invalid Redmine API key",
            http_status.HTTP_401_UNAUTHORIZED,
        ),
        http_status.HTTP_403_FORBIDDEN: (
            "access_denied",
            "Redmine access denied",
            http_status.HTTP_403_FORBIDDEN,
        ),
        http_status.HTTP_404_NOT_FOUND: (
            "resource_not_found",
            "Resource unavailable or not visible",
            http_status.HTTP_404_NOT_FOUND,
        ),
        http_status.HTTP_429_TOO_MANY_REQUESTS: (
            "upstream_rate_limited",
            "Redmine rate limit exceeded",
            http_status.HTTP_502_BAD_GATEWAY,
        ),
        http_status.HTTP_503_SERVICE_UNAVAILABLE: (
            "upstream_unavailable",
            "Redmine is unavailable",
            http_status.HTTP_502_BAD_GATEWAY,
        ),
        http_status.HTTP_504_GATEWAY_TIMEOUT: (
            "upstream_timeout",
            "Redmine timed out",
            http_status.HTTP_504_GATEWAY_TIMEOUT,
        ),
    }
    if status in failures:
        raise ApplicationError(*failures[status])
    if not http_status.HTTP_200_OK <= status < http_status.HTTP_300_MULTIPLE_CHOICES:
        raise ApplicationError(
            "upstream_error", "Redmine request failed", http_status.HTTP_502_BAD_GATEWAY
        )


class RedmineClient:
    def __init__(
        self, http: httpx.AsyncClient, api_key: str, policy: ReadPolicy | None = None
    ) -> None:
        self.http = http
        self.api_key = api_key
        self.policy = ReadPolicy() if policy is None else policy

    async def get(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        if (
            not path
            or path.startswith("/")
            or any(character in path for character in (":", "?", "#", "\\"))
            or any(part in (".", "..") for part in path.split("/"))
        ):
            raise ValueError("Redmine requests require a relative resource path")
        started = perf_counter()
        status: int | None = None
        try:
            request = self.http.build_request(
                "GET", path, params=params, headers={"X-Redmine-API-Key": self.api_key}
            )
            # The pool is shared, but authentication and cookies must be per request.
            request.headers.pop("cookie", None)
            request.headers.pop("authorization", None)
            async with asyncio.timeout(self.policy.deadline_seconds):
                response = await self.http.send(
                    request, auth=None, follow_redirects=False, stream=True
                )
                status = response.status_code
                try:
                    # Map failures before reading an upstream error body.
                    raise_for_upstream_status(status)
                    content = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                        if len(content) + len(chunk) > self.policy.max_response_bytes:
                            raise ApplicationError(
                                "upstream_response_too_large",
                                "Redmine response exceeds limit",
                                http_status.HTTP_502_BAD_GATEWAY,
                            )
                        content.extend(chunk)
                finally:
                    await response.aclose()
            try:
                result = json.loads(content)
                if not isinstance(result, dict):
                    raise ValueError
                return result
            except (ValueError, RecursionError):
                raise ApplicationError(
                    "upstream_response",
                    "Invalid Redmine response",
                    http_status.HTTP_502_BAD_GATEWAY,
                ) from None
        except httpx.PoolTimeout:
            raise ApplicationError(
                "upstream_busy",
                "Redmine connection pool is busy",
                http_status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from None
        except (httpx.TimeoutException, TimeoutError):
            raise ApplicationError(
                "upstream_timeout", "Redmine timed out", http_status.HTTP_504_GATEWAY_TIMEOUT
            ) from None
        except httpx.RequestError:
            raise ApplicationError(
                "upstream_unavailable", "Cannot reach Redmine", http_status.HTTP_502_BAD_GATEWAY
            ) from None
        finally:
            logger.info(
                "upstream_completed method=GET status=%s duration_ms=%.1f",
                status,
                (perf_counter() - started) * 1000,
            )
