"""Redmine text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

INVALID_API_KEY: Final[str] = "Invalid Redmine API key"

ACCESS_DENIED: Final[str] = "Redmine access denied"

RESOURCE_UNAVAILABLE: Final[str] = "Resource unavailable or not visible"

RATE_LIMIT_EXCEEDED: Final[str] = "Redmine rate limit exceeded"

UNAVAILABLE: Final[str] = "Redmine is unavailable"

TIMED_OUT: Final[str] = "Redmine timed out"

REQUEST_FAILED: Final[str] = "Redmine request failed"

RELATIVE_PATH_REQUIRED: Final[str] = "Redmine requests require a relative resource path"

RESPONSE_TOO_LARGE: Final[str] = "Redmine response exceeds limit"
REQUEST_TOO_LARGE: Final[str] = "Redmine request exceeds limit"
INVALID_FILENAME: Final[str] = "Invalid attachment filename"
INVALID_BASE64: Final[str] = "Invalid base64 attachment content"
WRITE_REJECTED: Final[str] = "Redmine rejected the write request"

INVALID_RESPONSE: Final[str] = "Invalid Redmine response"

CONNECTION_POOL_BUSY: Final[str] = "Redmine connection pool is busy"

UNREACHABLE: Final[str] = "Cannot reach Redmine"

UNEXPECTED_DATA: Final[str] = "Unexpected Redmine data"

UNEXPECTED_PAGE: Final[str] = "Unexpected Redmine page"

UNKNOWN_OBSERVABLE_FIELDS: Final[str] = "Observable fields are not declared on {model}: {fields}"

VISIBILITY_FIELD_REQUIRED: Final[str] = "{model} has no visibility field"

__all__ = [
    "INVALID_API_KEY",
    "ACCESS_DENIED",
    "RESOURCE_UNAVAILABLE",
    "RATE_LIMIT_EXCEEDED",
    "UNAVAILABLE",
    "TIMED_OUT",
    "REQUEST_FAILED",
    "RELATIVE_PATH_REQUIRED",
    "RESPONSE_TOO_LARGE",
    "REQUEST_TOO_LARGE",
    "INVALID_FILENAME",
    "INVALID_BASE64",
    "WRITE_REJECTED",
    "INVALID_RESPONSE",
    "CONNECTION_POOL_BUSY",
    "UNREACHABLE",
    "UNEXPECTED_DATA",
    "UNEXPECTED_PAGE",
    "UNKNOWN_OBSERVABLE_FIELDS",
    "VISIBILITY_FIELD_REQUIRED",
]
