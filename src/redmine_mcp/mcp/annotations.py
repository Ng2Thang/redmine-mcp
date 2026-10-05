from mcp.types import Tool, ToolAnnotations

from redmine_mcp.auth import WRITE_OPERATIONS


def annotate_read_tools(tools: list[Tool]) -> None:
    """Publish client hints; authorization is still enforced by the REST route."""
    for tool in tools:
        tool.annotations = ToolAnnotations(
            readOnlyHint=tool.name != "download_attachment" and tool.name not in WRITE_OPERATIONS,
            destructiveHint=tool.name == "delete_attachment",
            idempotentHint=tool.name != "download_attachment" and tool.name not in WRITE_OPERATIONS,
            openWorldHint=True,
        )
