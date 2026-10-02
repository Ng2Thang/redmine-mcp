"""Mcp text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

CATALOG_MISMATCH: Final[str] = "Generated MCP tools do not match the explicit catalog"

DUPLICATE_OPERATION_IDS: Final[str] = "Duplicate MCP operation IDs in catalog: {operations}"

MISSING_READ_PERMISSIONS: Final[str] = "MCP operations lack explicit read permissions: {operations}"

UNIQUE_ROUTE_REQUIRED: Final[str] = "MCP operation {operation!r} must match exactly one REST route"

GET_ROUTE_REQUIRED: Final[str] = "MCP operation {operation!r} must use a GET route under /api/v1/"

RESPONSE_SCHEMA_REQUIRED: Final[str] = "MCP operation {operation!r} must publish a response schema"

READ_AUTHORIZATION_REQUIRED: Final[str] = (
    "MCP operation {operation!r} must enforce read authorization"
)
WRITE_AUTHORIZATION_REQUIRED: Final[str] = (
    "MCP operation {operation!r} must enforce write authorization"
)
WRITE_ROUTE_REQUIRED: Final[str] = (
    "MCP operation {operation!r} must use a write route under /api/v1/"
)
UNKNOWN_WRITE_OPERATIONS: Final[str] = "Unknown writer operation IDs: {operations}"

__all__ = [
    "CATALOG_MISMATCH",
    "DUPLICATE_OPERATION_IDS",
    "MISSING_READ_PERMISSIONS",
    "UNIQUE_ROUTE_REQUIRED",
    "GET_ROUTE_REQUIRED",
    "RESPONSE_SCHEMA_REQUIRED",
    "READ_AUTHORIZATION_REQUIRED",
    "WRITE_AUTHORIZATION_REQUIRED",
    "WRITE_ROUTE_REQUIRED",
    "UNKNOWN_WRITE_OPERATIONS",
]
