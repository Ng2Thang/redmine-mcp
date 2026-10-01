import asyncio
import json
import logging
from time import perf_counter
from typing import Any

import httpx
from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import logs as logs_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.integrations.redmine.policy import ReadPolicy

logger = logging.getLogger(__name__)


def raise_for_upstream_status(status: int) -> None:
    failures = {
        http_status.HTTP_401_UNAUTHORIZED: (
            codes_text.INVALID_CREDENTIALS,
            redmine_text.INVALID_API_KEY,
            http_status.HTTP_401_UNAUTHORIZED,
        ),
        http_status.HTTP_403_FORBIDDEN: (
            codes_text.ACCESS_DENIED,
            redmine_text.ACCESS_DENIED,
            http_status.HTTP_403_FORBIDDEN,
        ),
        http_status.HTTP_404_NOT_FOUND: (
            codes_text.RESOURCE_NOT_FOUND,
            redmine_text.RESOURCE_UNAVAILABLE,
            http_status.HTTP_404_NOT_FOUND,
        ),
        http_status.HTTP_429_TOO_MANY_REQUESTS: (
            codes_text.UPSTREAM_RATE_LIMITED,
            redmine_text.RATE_LIMIT_EXCEEDED,
            http_status.HTTP_502_BAD_GATEWAY,
        ),
        http_status.HTTP_503_SERVICE_UNAVAILABLE: (
            codes_text.UPSTREAM_UNAVAILABLE,
            redmine_text.UNAVAILABLE,
            http_status.HTTP_502_BAD_GATEWAY,
        ),
        http_status.HTTP_504_GATEWAY_TIMEOUT: (
            codes_text.UPSTREAM_TIMEOUT,
            redmine_text.TIMED_OUT,
            http_status.HTTP_504_GATEWAY_TIMEOUT,
        ),
    }
    if status in failures:
        raise ApplicationError(*failures[status])
    if not http_status.HTTP_200_OK <= status < http_status.HTTP_300_MULTIPLE_CHOICES:
        raise ApplicationError(
            codes_text.UPSTREAM_ERROR, redmine_text.REQUEST_FAILED, http_status.HTTP_502_BAD_GATEWAY
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
            raise ValueError(redmine_text.RELATIVE_PATH_REQUIRED)
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
                                codes_text.UPSTREAM_RESPONSE_TOO_LARGE,
                                redmine_text.RESPONSE_TOO_LARGE,
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
                    codes_text.UPSTREAM_RESPONSE,
                    redmine_text.INVALID_RESPONSE,
                    http_status.HTTP_502_BAD_GATEWAY,
                ) from None
        except httpx.PoolTimeout:
            raise ApplicationError(
                codes_text.UPSTREAM_BUSY,
                redmine_text.CONNECTION_POOL_BUSY,
                http_status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from None
        except (httpx.TimeoutException, TimeoutError):
            raise ApplicationError(
                codes_text.UPSTREAM_TIMEOUT,
                redmine_text.TIMED_OUT,
                http_status.HTTP_504_GATEWAY_TIMEOUT,
            ) from None
        except httpx.RequestError:
            raise ApplicationError(
                codes_text.UPSTREAM_UNAVAILABLE,
                redmine_text.UNREACHABLE,
                http_status.HTTP_502_BAD_GATEWAY,
            ) from None
        finally:
            logger.info(
                logs_text.UPSTREAM_COMPLETED,
                status,
                (perf_counter() - started) * 1000,
            )
