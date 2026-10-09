"""Logs text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

LOG_FORMAT: Final[str] = (
    "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s call_id=%(call_id)s %(message)s"
)
LOGGING_CONFIGURED: Final[str] = "logging_configured level=%s"
VENDOR_DIAGNOSTIC: Final[str] = "vendor_diagnostic details_omitted=true"
REQUEST_STARTED: Final[str] = "request_started method=%s"
REQUEST_OPERATION: Final[str] = "request_operation operation=%s"
CALL_STARTED: Final[str] = "mcp_call_started operation=%s"
CALL_COMPLETED: Final[str] = "mcp_call_completed operation=%s outcome=%s duration_ms=%.1f"
AUTHENTICATION: Final[str] = "authentication outcome=%s reason=%s"
AUTHORIZATION: Final[str] = "authorization operation=%s outcome=%s reason=%s"
CAPABILITY: Final[str] = "capability_evaluated state=%s"
ERROR_STACK: Final[str] = "error_stack frames=%s truncated=%s"
BUDGET_STARTED: Final[str] = "read_budget_started max_requests=%s max_bytes=%s deadline_seconds=%s"
BUDGET_COMPLETED: Final[str] = (
    "read_budget_completed requests=%s response_bytes=%s duration_ms=%.1f"
)
BUDGET_EXHAUSTED: Final[str] = "read_budget_exhausted reason=%s requests=%s response_bytes=%s"
PAGINATION: Final[str] = "pagination_checked limit=%s offset=%s max_pages=%s outcome=%s"
UPSTREAM_STARTED: Final[str] = (
    "upstream_attempt_started method=%s endpoint=%s attempt=%s request_bytes=%s"
)
UPSTREAM_ATTEMPT: Final[str] = (
    "upstream_attempt_completed method=%s endpoint=%s attempt=%s status=%s "
    "duration_ms=%.1f response_bytes=%s dispatched=%s outcome=%s"
)
UPSTREAM_ADMISSION: Final[str] = "upstream_admission outcome=%s wait_ms=%.1f dispatched=%s"
RETRY_DECISION: Final[str] = "upstream_retry_decision attempt=%s decision=%s reason=%s"
UPSTREAM_WRITE_COMPLETED: Final[str] = (
    "upstream_write_completed method=%s status=%s duration_ms=%.1f"
)

REQUEST_FAILED: Final[str] = "request_failed code=%s status=%s"

UNEXPECTED_ERROR: Final[str] = "request_failed code=internal_error exception_type=%s"

REQUEST_COMPLETED: Final[str] = "request_completed operation=%s status=%s duration_ms=%.1f"

UPSTREAM_COMPLETED: Final[str] = "upstream_completed method=GET status=%s duration_ms=%.1f"

UPSTREAM_READ_RETRY: Final[str] = (
    "upstream_read_retry attempt=%s next_attempt=%s delay_seconds=%.3f status=%s reason=%s"
)

__all__ = [
    "LOGGING_CONFIGURED",
    "VENDOR_DIAGNOSTIC",
    "LOG_FORMAT",
    "REQUEST_STARTED",
    "REQUEST_OPERATION",
    "CALL_STARTED",
    "CALL_COMPLETED",
    "AUTHENTICATION",
    "AUTHORIZATION",
    "CAPABILITY",
    "ERROR_STACK",
    "BUDGET_STARTED",
    "BUDGET_COMPLETED",
    "BUDGET_EXHAUSTED",
    "PAGINATION",
    "UPSTREAM_STARTED",
    "UPSTREAM_ATTEMPT",
    "UPSTREAM_ADMISSION",
    "RETRY_DECISION",
    "UPSTREAM_WRITE_COMPLETED",
    "REQUEST_FAILED",
    "UNEXPECTED_ERROR",
    "REQUEST_COMPLETED",
    "UPSTREAM_COMPLETED",
    "UPSTREAM_READ_RETRY",
]
