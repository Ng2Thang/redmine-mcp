from mcp.types import Tool, ToolAnnotations


def annotate_read_tools(tools: list[Tool]) -> None:
    """Publish client hints; authorization is still enforced by the REST route."""
    for tool in tools:
        tool.annotations = ToolAnnotations(
            readOnlyHint=tool.name != "download_attachment",
            destructiveHint=False,
            idempotentHint=tool.name != "download_attachment",
            openWorldHint=True,
        )
