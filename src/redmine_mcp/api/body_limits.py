"""Admit bounded REST/MCP request bytes before parsing or authentication."""

import re
from http import HTTPMethod

from fastapi import status as http_status
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from redmine_mcp.api.error_handlers import application_error
from redmine_mcp.common import ApplicationError


def _too_large() -> ApplicationError:
    return ApplicationError(
        "request_body_too_large",
        "Request body exceeds the configured limit",
        http_status.HTTP_413_CONTENT_TOO_LARGE,
    )


def _invalid_framing() -> ApplicationError:
    return ApplicationError(
        "invalid_request_body", "Invalid request body framing", http_status.HTTP_400_BAD_REQUEST
    )


class RequestBodyLimitsMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    def _declared_length(self, scope: Scope) -> int | None:
        declared: bytes | None = None
        for name, value in scope.get("headers", []):
            if name.lower() != b"content-length":
                continue
            # Identical repeated lengths may also be combined by an HTTP intermediary.
            for part in value.split(b","):
                part = part.strip(b" \t")
                if re.fullmatch(rb"[0-9]+", part) is None:
                    raise _invalid_framing()
                normalized = part.lstrip(b"0") or b"0"
                if declared is not None and normalized != declared:
                    raise _invalid_framing()
                declared = normalized
        if declared is None:
            return None
        # Compare decimal bytes before int conversion, including extremely long headers.
        maximum = str(self.max_body_bytes).encode("ascii")
        if len(declared) > len(maximum) or (len(declared) == len(maximum) and declared > maximum):
            raise _too_large()
        return int(declared)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope["path"]
        method = scope["method"]
        limited = (method == HTTPMethod.POST and (path == "/mcp" or path.startswith("/mcp/"))) or (
            method in {HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH, HTTPMethod.DELETE}
            and path.startswith("/api/v1/")
        )
        if not limited:
            await self.app(scope, receive, send)
            return

        body = bytearray()
        try:
            declared = self._declared_length(scope)
            for name, value in scope.get("headers", []):
                if name.lower() == b"content-encoding" and value.strip().lower() != b"identity":
                    raise ApplicationError(
                        "request_encoding_unsupported",
                        "Encoded request bodies are not supported",
                        http_status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    )
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    # Never dispatch a tool with a partial body from a disconnected caller.
                    return
                if message["type"] != "http.request":
                    raise _invalid_framing()
                chunk = message.get("body", b"")
                if len(body) + len(chunk) > self.max_body_bytes:
                    raise _too_large()
                body.extend(chunk)
                if not message.get("more_body", False):
                    break
            if declared is not None and declared != len(body):
                raise _invalid_framing()
        except ApplicationError as exc:
            body.clear()
            response = await application_error(Request(scope), exc)
            await response(scope, receive, send)
            return

        accepted: bytes | None = bytes(body)
        body.clear()

        async def replay() -> Message:
            nonlocal accepted
            if accepted is not None:
                message: Message = {"type": "http.request", "body": accepted, "more_body": False}
                accepted = None
                return message
            # Preserve the original channel for disconnect listeners and streaming responses.
            return await receive()

        await self.app(scope, replay, send)
