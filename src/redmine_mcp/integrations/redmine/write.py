"""Bounded, single-attempt Redmine mutations with explicit uncertainty."""

import asyncio
import json
import logging
from dataclasses import dataclass
from http import HTTPMethod
from time import perf_counter
from typing import Any, Literal

import httpx
from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import logs as logs_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.integrations.redmine.client import raise_for_upstream_status
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.observability import debug_exception, endpoint_template

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
        response_bytes = 0
        outcome = "failed"
        method_name = str(method) if method in HTTPMethod else "unknown"
        endpoint = endpoint_template(path) if logger.isEnabledFor(logging.DEBUG) else "unknown"

        def receipt(
            value: Literal["accepted", "uncertain"], payload: dict[str, Any] | None = None
        ) -> WriteReceipt:
            nonlocal outcome
            outcome = value
            return WriteReceipt(value, status, payload)

        try:
            logger.debug(
                logs_text.UPSTREAM_STARTED,
                method_name,
                endpoint,
                1,
                len(content) if content is not None else 0,
            )
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
                        return receipt("uncertain")
                    if status in (
                        http_status.HTTP_400_BAD_REQUEST,
                        http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                    ):
                        outcome = "rejected"
                        raise RedmineWriteRejected(status)
                    if (
                        status < http_status.HTTP_200_OK
                        or status >= http_status.HTTP_300_MULTIPLE_CHOICES
                    ):
                        outcome = "rejected"
                    raise_for_upstream_status(status)
                    if status not in accepted_statuses:
                        return receipt("uncertain")
                    if status == http_status.HTTP_204_NO_CONTENT:
                        return receipt("accepted")
                    data = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                        response_bytes += len(chunk)
                        if len(data) + len(chunk) > self.policy.max_response_bytes:
                            return receipt("uncertain")
                        data.extend(chunk)
                    try:
                        if allow_empty_success and not data:
                            return receipt("accepted")
                        payload = json.loads(data)
                    except (ValueError, RecursionError) as exc:
                        debug_exception(logger, exc)
                        return receipt("uncertain")
                    if not isinstance(payload, dict):
                        return receipt("uncertain")
                    return receipt("accepted", payload)
                finally:
                    try:
                        await response.aclose()
                    except BaseException:
                        outcome = "failed"
                        raise
        except httpx.PoolTimeout as exc:
            debug_exception(logger, exc)
            raise ApplicationError(
                codes_text.UPSTREAM_BUSY,
                redmine_text.CONNECTION_POOL_BUSY,
                http_status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from None
        except (httpx.TimeoutException, TimeoutError, httpx.RequestError) as exc:
            debug_exception(logger, exc)
            if request.extensions.get("redmine_dispatched", dispatched):
                return receipt("uncertain")
            raise ApplicationError(
                codes_text.UPSTREAM_UNAVAILABLE,
                redmine_text.UNREACHABLE,
                http_status.HTTP_502_BAD_GATEWAY,
            ) from None
        except BaseException as exc:
            if not isinstance(exc, Exception):
                outcome = "interrupted"
            debug_exception(logger, exc)
            raise
        finally:
            logger.debug(
                logs_text.UPSTREAM_ATTEMPT,
                method_name,
                endpoint,
                1,
                status,
                (perf_counter() - started) * 1000,
                response_bytes,
                request.extensions.get("redmine_dispatched", dispatched),
                outcome,
            )
            logger.info(
                logs_text.UPSTREAM_WRITE_COMPLETED,
                method,
                status,
                (perf_counter() - started) * 1000,
            )
