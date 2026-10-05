"""Bounded, single-attempt Redmine mutations with explicit uncertainty."""

import asyncio
import json
import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal

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


class RedmineWriter:
    def __init__(self, http: httpx.AsyncClient, api_key: str, policy: ReadPolicy) -> None:
        self.http = http
        self.api_key = api_key
        self.policy = policy

    async def write_json(
        self,
        method: Literal["POST", "PATCH", "DELETE"],
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        accepted_statuses: tuple[int, ...] = (201, 204),
        params: dict[str, str] | None = None,
    ) -> WriteReceipt:
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        if body is not None and len(body) > self.policy.max_response_bytes:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.REQUEST_TOO_LARGE,
                http_status.HTTP_413_CONTENT_TOO_LARGE,
            )
        return await self._write(
            method, path, body, "application/json", accepted_statuses, params=params
        )

    async def write_binary(self, path: str, content: bytes, *, filename: str) -> WriteReceipt:
        if len(content) > self.policy.max_binary_bytes:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.REQUEST_TOO_LARGE,
                http_status.HTTP_413_CONTENT_TOO_LARGE,
            )
        return await self._write(
            "POST", path, content, "application/octet-stream", (201,), params={"filename": filename}
        )

    async def _write(
        self,
        method: Literal["POST", "PATCH", "DELETE"],
        path: str,
        content: bytes | None,
        content_type: str,
        accepted_statuses: tuple[int, ...],
        params: dict[str, str] | None = None,
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
                    if status in (
                        http_status.HTTP_400_BAD_REQUEST,
                        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                    ):
                        raise ApplicationError(
                            codes_text.INVALID_PARAMETERS,
                            redmine_text.WRITE_REJECTED,
                            http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                        )
                    raise_for_upstream_status(status)
                    if status not in accepted_statuses:
                        return WriteReceipt("uncertain", status)
                    if status == 204:
                        return WriteReceipt("accepted", status)
                    data = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                        if len(data) + len(chunk) > self.policy.max_response_bytes:
                            return WriteReceipt("uncertain", status)
                        data.extend(chunk)
                    try:
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
            if dispatched:
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
