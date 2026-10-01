"""Logs text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

REQUEST_FAILED: Final[str] = "request_failed code=%s status=%s"

UNEXPECTED_ERROR: Final[str] = "request_failed code=internal_error exception_type=%s"

REQUEST_COMPLETED: Final[str] = "request_completed operation=%s status=%s duration_ms=%.1f"

UPSTREAM_COMPLETED: Final[str] = "upstream_completed method=GET status=%s duration_ms=%.1f"

__all__ = [
    "REQUEST_FAILED",
    "UNEXPECTED_ERROR",
    "REQUEST_COMPLETED",
    "UPSTREAM_COMPLETED",
]
