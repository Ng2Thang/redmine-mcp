"""Keep FastAPI-MCP 0.4's DELETE-body compatibility at the adapter boundary."""

from fastapi_mcp import FastApiMCP

from redmine_mcp.mcp.compatibility import MCPCompatibility


def install_membership_transport(
    mcp: FastApiMCP, *, compatibility: MCPCompatibility | None = None
) -> None:
    boundary = MCPCompatibility(mcp) if compatibility is None else compatibility
    boundary.install_membership_delete_body()
