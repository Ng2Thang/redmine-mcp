import asyncio
import json
import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any, NoReturn
from urllib.parse import unquote

import httpx
from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.common.pagination import PaginationGuard
from redmine_mcp.common.read_budget import (
    charge_bytes,
    check_read_deadline,
    check_read_request_available,
    read_deadline,
)
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import logs as logs_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.responses import response_page
from redmine_mcp.integrations.redmine.retry import (
    RETRY_ERRORS,
    RETRY_STATUSES,
    RetryRuntime,
    retry_reason,
)

logger = logging.getLogger(__name__)


@dataclass
class _ReadAttempt:
    status: int | None = None
    retry_after: tuple[str, ...] = ()
    failure: httpx.RequestError | None = None


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
        self,
        http: httpx.AsyncClient,
        api_key: str,
        policy: ReadPolicy | None = None,
        *,
        retry_runtime: RetryRuntime | None = None,
    ) -> None:
        self.http = http
        self.api_key = api_key
        self.policy = ReadPolicy() if policy is None else policy
        self.pagination = PaginationGuard(self.policy.max_query_pages)
        self.retry_runtime = RetryRuntime() if retry_runtime is None else retry_runtime

    async def get_page(
        self,
        path: str,
        key: str,
        params: dict[str, str | int],
        guidance: str,
        *,
        require_metadata: bool = False,
    ) -> dict[str, Any]:
        limit, offset = params["limit"], params["offset"]
        if type(limit) is not int or type(offset) is not int:
            raise ValueError("Invalid pagination")
        self.pagination.check_depth(limit, offset, guidance)
        if offset:
            probe_params = {**params, "limit": 1, "offset": 0}
            probe = await self.get(path, probe_params)
            metadata = response_page(probe, key, 1, 0, require_metadata=require_metadata)
            self.pagination.require_scope(metadata.total, limit, guidance)
        data = await self.get(path, params)
        actual = response_page(data, key, limit, offset, require_metadata=require_metadata)
        if offset:
            self.pagination.require_scope(actual.total, limit, guidance)
        return data

    def attachment_link(self, content_url: str, attachment_id: int) -> str:
        url = self.attachment_url(content_url, attachment_id)
        if self.policy.public_url is None:
            return str(url)
        root = self.http.base_url.raw_path
        relative = url.raw_path[len(root) :].decode("ascii")
        return str(httpx.URL(self.policy.public_url.rstrip("/") + "/" + relative))

    def map_attachment_links(self, data: Any) -> None:
        """Map only actual attachment records; never synthesize missing content URLs."""
        if isinstance(data, dict):
            if data.get("content_url") is not None and "filesize" in data:
                attachment_id, url = data.get("id"), data["content_url"]
                if type(attachment_id) is not int or not isinstance(url, str):
                    raise ApplicationError(
                        "upstream_response", "Unexpected attachment metadata", 502
                    )
                data["content_url"] = self.attachment_link(url, attachment_id)
            for value in data.values():
                self.map_attachment_links(value)
        elif isinstance(data, list):
            for value in data:
                self.map_attachment_links(value)

    def attachment_url(self, content_url: str, attachment_id: int) -> httpx.URL:
        """Validate metadata links against the configured origin and download path."""
        try:
            url = httpx.URL(content_url)
            base = self.http.base_url
            root = base.raw_path.split(b"?", 1)[0]
            expected = root + b"attachments/download/" + str(attachment_id).encode("ascii")
            raw_path = url.raw_path.split(b"?", 1)[0]
            decoded_path = unquote(url.path)
            if (
                type(attachment_id) is not int
                or attachment_id < 1
                or url.scheme != base.scheme
                or url.host != base.host
                or url.port != base.port
                or url.username
                or url.password
                or url.query
                or url.fragment
                or not root.endswith(b"/")
                or not (raw_path == expected or raw_path.startswith(expected + b"/"))
                or "\\" in decoded_path
                or any(segment in (".", "..") for segment in decoded_path.split("/"))
            ):
                raise ValueError
            return url
        except (httpx.InvalidURL, ValueError, UnicodeError):
            raise ApplicationError(
                codes_text.UPSTREAM_RESPONSE,
                redmine_text.UNEXPECTED_DATA,
                http_status.HTTP_502_BAD_GATEWAY,
            ) from None

    async def get_attachment_bytes(self, content_url: str, attachment_id: int) -> bytes:
        """Retired binary interface: no attachment content is dispatched."""
        raise ApplicationError(
            "attachment_download_disabled", "Use attachment metadata and its Redmine link", 403
        )

    async def _get_attempt(
        self, path: str, params: dict[str, str | int], attempt: _ReadAttempt
    ) -> bytearray | None:
        request = self.http.build_request(
            "GET", path, params=params, headers={"X-Redmine-API-Key": self.api_key}
        )
        # Rebuild each request: the shared pool must never supply authentication or cookies.
        request.headers.pop("cookie", None)
        request.headers.pop("authorization", None)
        try:
            response = await self.http.send(request, auth=None, follow_redirects=False, stream=True)
        except RETRY_ERRORS as exc:
            attempt.failure = exc
            return None
        try:
            attempt.status = response.status_code
            if response.status_code in RETRY_STATUSES:
                attempt.retry_after = tuple(response.headers.get_list("retry-after"))
                return None
            # Do not acquire or inspect upstream error bodies.
            raise_for_upstream_status(response.status_code)
            content = bytearray()
            try:
                # Fixed-size chunking hides a buffered tail if the stream fails before EOF.
                # Charge each decoded chunk immediately, including failed attempts' tails.
                async for chunk in response.aiter_bytes():
                    charge_bytes(len(chunk))
                    if len(content) + len(chunk) > self.policy.max_response_bytes:
                        raise ApplicationError(
                            codes_text.UPSTREAM_RESPONSE_TOO_LARGE,
                            redmine_text.RESPONSE_TOO_LARGE,
                            http_status.HTTP_502_BAD_GATEWAY,
                        )
                    content.extend(chunk)
            except RETRY_ERRORS as exc:
                if response.is_closed:
                    # HTTPX closes at iterator EOF. A failure there is cleanup, not a
                    # broken read, and must not cause another dispatch.
                    raise
                attempt.failure = exc
                return None
            return content
        finally:
            # Cleanup failures propagate outside retry classification. The admitted stream
            # completes its shielded socket cleanup before releasing the physical permit.
            await response.aclose()

    @staticmethod
    def _raise_attempt_failure(attempt: _ReadAttempt) -> NoReturn:
        if attempt.failure is not None:
            raise attempt.failure
        if attempt.status is not None:
            raise_for_upstream_status(attempt.status)
        raise RuntimeError("GET attempt ended without content or failure")

    async def get(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        if (
            not path
            or path.startswith("/")
            or any(character in path for character in (":", "?", "#", "\\"))
            or any(part in (".", "..") for part in path.split("/"))
        ):
            raise ValueError(redmine_text.RELATIVE_PATH_REQUIRED)
        started = perf_counter()
        attempt = _ReadAttempt()
        try:
            runtime = self.retry_runtime
            deadline = runtime.monotonic() + self.policy.deadline_seconds
            budget_deadline = read_deadline()
            if budget_deadline is not None:
                deadline = min(deadline, budget_deadline)
            content: bytearray | None = None
            # One acquisition timer includes every attempt and wait. Clip cooperative batch
            # time here without introducing a cancellation timer around mutations/receipts.
            async with asyncio.timeout(max(0.0, deadline - runtime.monotonic())):
                for number in range(1, self.policy.retry_max_attempts + 1):
                    check_read_request_available()
                    if runtime.monotonic() >= deadline:
                        raise TimeoutError
                    attempt = _ReadAttempt()
                    content = await self._get_attempt(path, params, attempt)
                    if content is not None:
                        break
                    if number >= self.policy.retry_max_attempts:
                        self._raise_attempt_failure(attempt)
                    check_read_request_available()
                    delay = runtime.delay(self.policy, number, attempt.retry_after)
                    available = deadline - runtime.monotonic()
                    if available <= 0:
                        check_read_deadline()
                        raise TimeoutError
                    if delay is None or delay >= available:
                        self._raise_attempt_failure(attempt)
                    logger.info(
                        logs_text.UPSTREAM_READ_RETRY,
                        number,
                        number + 1,
                        delay,
                        attempt.status,
                        retry_reason(attempt.failure),
                    )
                    await runtime.sleep(delay)
            if content is None:
                raise RuntimeError("GET acquisition ended without content")
            try:
                result = json.loads(content)
                if not isinstance(result, dict):
                    raise ValueError
                self.map_attachment_links(result)
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
            # A cooperative batch timeout must not be flattened into a per-GET timeout.
            check_read_deadline()
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
                attempt.status,
                (perf_counter() - started) * 1000,
            )
