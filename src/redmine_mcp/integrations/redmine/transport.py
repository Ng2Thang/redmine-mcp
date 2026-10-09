"""Shared, credential-free HTTP transport configuration."""

import asyncio
import logging
from collections.abc import AsyncIterator
from time import perf_counter

import httpx
from fastapi import status as http_status
from httpx._utils import get_environment_proxies

from redmine_mcp.common import ApplicationError
from redmine_mcp.common.read_budget import charge_request, check_read_deadline
from redmine_mcp.config import Settings
from redmine_mcp.constants import logs as logs_text

logger = logging.getLogger(__name__)


class AdmittedStream(httpx.AsyncByteStream):
    def __init__(self, stream: httpx.AsyncByteStream, semaphore: asyncio.Semaphore) -> None:
        self.stream = stream
        self.semaphore = semaphore
        self.close_task: asyncio.Task[None] | None = None

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self.stream:
            yield chunk

    async def aclose(self) -> None:
        if self.close_task is None:
            self.close_task = asyncio.create_task(self._close())
            self.close_task.add_done_callback(self._observe_close)
        # Cancellation of a caller must not cancel socket cleanup or release the
        # permit while the underlying response is still being closed.
        await asyncio.shield(self.close_task)

    @staticmethod
    def _observe_close(task: asyncio.Task[None]) -> None:
        if not task.cancelled():
            task.exception()

    async def _close(self) -> None:
        try:
            await self.stream.aclose()
        finally:
            self.semaphore.release()


class AdmittedTransport(httpx.AsyncBaseTransport):
    """One permit per physical request, held until its response stream closes."""

    def __init__(
        self,
        inner: httpx.AsyncBaseTransport,
        semaphore: asyncio.Semaphore,
        admission_seconds: float,
    ) -> None:
        self.inner = inner
        self.semaphore = semaphore
        self.admission_seconds = admission_seconds

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        request.extensions["redmine_dispatched"] = False
        charge_request()
        started = perf_counter()
        try:
            async with asyncio.timeout(self.admission_seconds):
                await self.semaphore.acquire()
        except TimeoutError:
            logger.debug(
                logs_text.UPSTREAM_ADMISSION, "timeout", (perf_counter() - started) * 1000, False
            )
            raise ApplicationError(
                "upstream_busy",
                "Redmine request capacity is busy; retry later",
                http_status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from None
        except BaseException:
            logger.debug(
                logs_text.UPSTREAM_ADMISSION,
                "interrupted",
                (perf_counter() - started) * 1000,
                False,
            )
            raise
        try:
            # Admission waiting may have consumed the remaining operation deadline.
            # Fail before dispatch; the exception path releases the acquired permit.
            check_read_deadline()
            request.extensions["redmine_dispatched"] = True
            logger.debug(
                logs_text.UPSTREAM_ADMISSION, "admitted", (perf_counter() - started) * 1000, True
            )
            response = await self.inner.handle_async_request(request)
            if not isinstance(response.stream, httpx.AsyncByteStream):
                raise RuntimeError("Unexpected upstream stream")
            response.stream = AdmittedStream(response.stream, self.semaphore)
            return response
        except BaseException:
            self.semaphore.release()
            if not request.extensions["redmine_dispatched"]:
                logger.debug(
                    logs_text.UPSTREAM_ADMISSION, "denied", (perf_counter() - started) * 1000, False
                )
            raise

    async def aclose(self) -> None:
        await self.inner.aclose()


def create_upstream_client(settings: Settings) -> httpx.AsyncClient:
    semaphore = asyncio.Semaphore(settings.redmine_max_concurrent_requests)
    limits = httpx.Limits(
        max_connections=settings.redmine_max_connections,
        max_keepalive_connections=settings.redmine_max_keepalive_connections,
    )

    def admitted_transport(proxy: str | None = None) -> AdmittedTransport:
        return AdmittedTransport(
            httpx.AsyncHTTPTransport(limits=limits, retries=0, proxy=proxy),
            semaphore,
            settings.redmine_admission_timeout_seconds,
        )

    # A custom transport disables HTTPX's automatic environment proxy mounts.
    # Reuse its parser to retain platform proxy and NO_PROXY matching semantics.
    # Every proxy pool shares the direct transport's admission semaphore.
    mounts: dict[str, httpx.AsyncBaseTransport | None] = {
        pattern: None if proxy is None else admitted_transport(proxy)
        for pattern, proxy in get_environment_proxies().items()
    }
    return httpx.AsyncClient(
        base_url=str(settings.redmine_url).rstrip("/") + "/",
        timeout=httpx.Timeout(
            settings.redmine_timeout_seconds,
            connect=settings.redmine_connect_timeout_seconds,
            pool=settings.redmine_pool_timeout_seconds,
        ),
        transport=admitted_transport(),
        mounts=mounts,
        follow_redirects=False,
    )
