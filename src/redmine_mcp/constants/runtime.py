"""Runtime text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

MODULE_ATTRIBUTE_NOT_FOUND: Final[str] = "module {module!r} has no attribute {attribute!r}"

LIFESPAN_ALREADY_STARTED: Final[str] = "Create a new application instance for each runtime lifespan"

INVALID_KEEPALIVE_LIMIT: Final[str] = "Keepalive connections cannot exceed maximum connections"

URL_CONTAINS_CREDENTIALS: Final[str] = "Redmine URL must not contain credentials"

URL_CONTAINS_QUERY_OR_FRAGMENT: Final[str] = "Redmine URL must not contain a query or fragment"

__all__ = [
    "MODULE_ATTRIBUTE_NOT_FOUND",
    "LIFESPAN_ALREADY_STARTED",
    "INVALID_KEEPALIVE_LIMIT",
    "URL_CONTAINS_CREDENTIALS",
    "URL_CONTAINS_QUERY_OR_FRAGMENT",
]
