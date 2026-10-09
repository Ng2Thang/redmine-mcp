"""Bounded, single-attempt Redmine mutations with explicit uncertainty."""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Literal
from http import HTTPMethod
from time import perf_counter
from typing import Any

import httpx
from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.integrations.redmine.client import raise_for_upstream_status
from redmine_mcp.integrations.redmine.policy import ReadPolicy

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WriteReceipt:
    outcome: Literal["accepted", "uncertain"]
    status: int | None = None
    payload: dict[str, Any] | None = None


class RedmineWriteRejected(ApplicationError):
    """Keep the original validation status without exposing the upstream response body."""

    def __init__(self, upstream_status: int) -> None:
        super().__init__(
            codes_text.INVALID_PARAMETERS,
            redmine_text.WRITE_REJECTED,
            http_status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
        self.upstream_status = upstream_status


class RedmineWriter:
    def __init__(self, http: httpx.AsyncClient, api_key: str, policy: ReadPolicy) -> None:
        self.http = http
        self.api_key = api_key
        self.policy = policy

    async def write_json(
        self,
        method: HTTPMethod,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        accepted_statuses: tuple[int, ...] = (
            http_status.HTTP_201_CREATED,
            http_status.HTTP_204_NO_CONTENT,
        ),
        params: dict[str, str] | None = None,
        allow_empty_success: bool = False,
    ) -> WriteReceipt:
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        if body is not None and len(body) > self.policy.max_response_bytes:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.REQUEST_TOO_LARGE,
                http_status.HTTP_413_CONTENT_TOO_LARGE,
            )
        return await self._write(
            method,
            path,
            body,
            "application/json",
            accepted_statuses,
            params=params,
            allow_empty_success=allow_empty_success,
        )

    async def write_binary(self, path: str, content: bytes, *, filename: str) -> WriteReceipt:
        if len(content) > self.policy.max_binary_bytes:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.REQUEST_TOO_LARGE,
                http_status.HTTP_413_CONTENT_TOO_LARGE,
            )
        return await self._write(
            HTTPMethod.POST,
            path,
            content,
            "application/octet-stream",
            (http_status.HTTP_201_CREATED,),
            params={"filename": filename},
        )

    async def _write(
        self,
        method: HTTPMethod,
        path: str,
        content: bytes | None,
        content_type: str,
        accepted_statuses: tuple[int, ...],
        params: dict[str, str] | None = None,
        allow_empty_success: bool = False,
    ) -> WriteReceipt:
        if (
            not path
            or path.startswith("/")
            or any(character in path for character in (":", "?", "#", "\\"))
            or any(part in (".", "..") for part in path.split("/"))
        ):
            raise ValueError(redmine_text.RELATIVE_PATH_REQUIRED)
        request = self.http.build_request(
            method,
            path,
            params=params,
            content=content,
            headers={"X-Redmine-API-Key": self.api_key, "Content-Type": content_type},
        )
        request.headers.pop("cookie", None)
        request.headers.pop("authorization", None)
        started = perf_counter()
        status: int | None = None
        dispatched = False
        try:
            async with asyncio.timeout(self.policy.deadline_seconds):
                dispatched = True
                response = await self.http.send(
                    request, auth=None, follow_redirects=False, stream=True
                )
                status = response.status_code
                try:
                    # A received server error cannot prove the mutation did not commit.
                    # Apply this policy to every JSON and binary write before error mapping.
                    if response.is_server_error:
                        return WriteReceipt("uncertain", status)
                    if status in (
                        http_status.HTTP_400_BAD_REQUEST,
                        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                    ):
                        raise RedmineWriteRejected(status)
                    raise_for_upstream_status(status)
                    if status not in accepted_statuses:
                        return WriteReceipt("uncertain", status)
                    if status == http_status.HTTP_204_NO_CONTENT:
                        return WriteReceipt("accepted", status)
                    data = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                        if len(data) + len(chunk) > self.policy.max_response_bytes:
                            return WriteReceipt("uncertain", status)
                        data.extend(chunk)
                    try:
                        if allow_empty_success and not data:
                            return WriteReceipt("accepted", status)
                        payload = json.loads(data)
                    except (ValueError, RecursionError):
                        return WriteReceipt("uncertain", status)
                    if not isinstance(payload, dict):
                        return WriteReceipt("uncertain", status)
                    return WriteReceipt("accepted", status, payload)
                finally:
                    await response.aclose()
        except httpx.PoolTimeout:
            raise ApplicationError(
                codes_text.UPSTREAM_BUSY,
                redmine_text.CONNECTION_POOL_BUSY,
                http_status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from None
        except (httpx.TimeoutException, TimeoutError, httpx.RequestError):
            if request.extensions.get("redmine_dispatched", dispatched):
                return WriteReceipt("uncertain", status)
            raise ApplicationError(
                codes_text.UPSTREAM_UNAVAILABLE,
                redmine_text.UNREACHABLE,
                http_status.HTTP_502_BAD_GATEWAY,
            ) from None
        finally:
            logger.info(
                "upstream_write_completed method=%s status=%s duration_ms=%.1f",
                method,
                status,
                (perf_counter() - started) * 1000,
            )
