"""Codes text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

INVALID_PARAMETERS: Final[str] = "invalid_parameters"

INVALID_CREDENTIALS: Final[str] = "invalid_credentials"

PERMISSION_DENIED: Final[str] = "permission_denied"

SERVICE_UNAVAILABLE: Final[str] = "service_unavailable"

INTERNAL_ERROR: Final[str] = "internal_error"

ACCESS_DENIED: Final[str] = "access_denied"

RESOURCE_NOT_FOUND: Final[str] = "resource_not_found"

UPSTREAM_RATE_LIMITED: Final[str] = "upstream_rate_limited"

UPSTREAM_UNAVAILABLE: Final[str] = "upstream_unavailable"

UPSTREAM_TIMEOUT: Final[str] = "upstream_timeout"

UPSTREAM_ERROR: Final[str] = "upstream_error"

UPSTREAM_RESPONSE_TOO_LARGE: Final[str] = "upstream_response_too_large"

UPSTREAM_RESPONSE: Final[str] = "upstream_response"

UPSTREAM_BUSY: Final[str] = "upstream_busy"

__all__ = [
    "INVALID_PARAMETERS",
    "INVALID_CREDENTIALS",
    "PERMISSION_DENIED",
    "SERVICE_UNAVAILABLE",
    "INTERNAL_ERROR",
    "ACCESS_DENIED",
    "RESOURCE_NOT_FOUND",
    "UPSTREAM_RATE_LIMITED",
    "UPSTREAM_UNAVAILABLE",
    "UPSTREAM_TIMEOUT",
    "UPSTREAM_ERROR",
    "UPSTREAM_RESPONSE_TOO_LARGE",
    "UPSTREAM_RESPONSE",
    "UPSTREAM_BUSY",
]
