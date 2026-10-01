"""Common text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

INVALID_QUERY_PARAMETERS: Final[str] = "Invalid query parameters"

POSITIVE_INTEGER_REQUIRED: Final[str] = "{name} must be a positive integer"

__all__ = [
    "INVALID_QUERY_PARAMETERS",
    "POSITIVE_INTEGER_REQUIRED",
]
