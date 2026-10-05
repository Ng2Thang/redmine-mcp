"""Runtime text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

MODULE_ATTRIBUTE_NOT_FOUND: Final[str] = "module {module!r} has no attribute {attribute!r}"

LIFESPAN_ALREADY_STARTED: Final[str] = "Create a new application instance for each runtime lifespan"

MCP_START_FAILED: Final[str] = "MCP session manager startup failed"

INVALID_KEEPALIVE_LIMIT: Final[str] = "Keepalive connections cannot exceed maximum connections"

URL_CONTAINS_CREDENTIALS: Final[str] = "Redmine URL must not contain credentials"

URL_CONTAINS_QUERY_OR_FRAGMENT: Final[str] = "Redmine URL must not contain a query or fragment"
WRITER_USER_IDS_REQUIRED: Final[str] = "Writer deployment requires positive user IDs"
WRITER_OPERATIONS_REQUIRED: Final[str] = "Writer operation IDs must be comma-separated names"
WRITER_KEY_HASH_REQUIRED: Final[str] = "Writer deployment requires a SHA-256 key hash"
PERSONAL_WRITER_HASH_FORBIDDEN: Final[str] = "Personal-key mode requires an empty writer key hash"

__all__ = [
    "MODULE_ATTRIBUTE_NOT_FOUND",
    "LIFESPAN_ALREADY_STARTED",
    "MCP_START_FAILED",
    "INVALID_KEEPALIVE_LIMIT",
    "URL_CONTAINS_CREDENTIALS",
    "URL_CONTAINS_QUERY_OR_FRAGMENT",
    "WRITER_USER_IDS_REQUIRED",
    "WRITER_OPERATIONS_REQUIRED",
    "WRITER_KEY_HASH_REQUIRED",
    "PERSONAL_WRITER_HASH_FORBIDDEN",
]
