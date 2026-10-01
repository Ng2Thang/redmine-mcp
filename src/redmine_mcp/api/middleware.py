import logging
from time import perf_counter
from uuid import uuid4

from fastapi import status as http_status
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from redmine_mcp.api.error_handlers import unexpected_error
from redmine_mcp.constants import api as api_text
from redmine_mcp.constants import logs as logs_text
from redmine_mcp.observability import request_id

logger = logging.getLogger("redmine_mcp.requests")


class RequestContextMiddleware:
    """Correlate REST/MCP and internal ASGI calls without logging request data."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        inherited = request_id.get()
        correlation = uuid4().hex if inherited == "-" else inherited
        token = request_id.set(correlation)
        scope.setdefault("state", {})["request_id"] = correlation
        started = perf_counter()
        status = http_status.HTTP_500_INTERNAL_SERVER_ERROR
        response_started = False

        async def send_response(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                message = {
                    **message,
                    "headers": [*headers, (b"x-request-id", correlation.encode("ascii"))],
                }
            await send(message)

        try:
            await self.app(scope, receive, send_response)
        except Exception as exc:
            response = await unexpected_error(Request(scope), exc)
            if response_started:
                # Preserve a failed stream without propagating sensitive exception text.
                raise RuntimeError(api_text.RESPONSE_STREAM_FAILED) from None
            await response(scope, receive, send_response)
        finally:
            route = scope.get("route")
            operation = getattr(route, "operation_id", None) or "transport"
            logger.info(
                logs_text.REQUEST_COMPLETED,
                operation,
                status,
                (perf_counter() - started) * 1000,
            )
            request_id.reset(token)
