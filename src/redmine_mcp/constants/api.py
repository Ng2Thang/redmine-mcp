"""Api text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

RUNTIME_UNAVAILABLE: Final[str] = "Server runtime is unavailable"

INTERNAL_SERVER_ERROR: Final[str] = "Internal server error"

RESPONSE_STREAM_FAILED: Final[str] = "Response streaming failed"

__all__ = [
    "RUNTIME_UNAVAILABLE",
    "INTERNAL_SERVER_ERROR",
    "RESPONSE_STREAM_FAILED",
]
