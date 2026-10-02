"""Public MCP catalog and registration interface."""

from redmine_mcp.mcp.annotations import annotate_read_tools
from redmine_mcp.mcp.catalog import OPERATIONS, validate_generated_tools, validate_operation_catalog
from redmine_mcp.mcp.registration import register_mcp, shutdown_mcp, start_mcp

__all__ = [
    "OPERATIONS",
    "annotate_read_tools",
    "register_mcp",
    "shutdown_mcp",
    "start_mcp",
    "validate_generated_tools",
    "validate_operation_catalog",
]
