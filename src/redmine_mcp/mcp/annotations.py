from mcp.types import Tool, ToolAnnotations


def annotate_read_tools(tools: list[Tool]) -> None:
    """Publish client hints; authorization is still enforced by the REST route."""
    for tool in tools:
        tool.annotations = ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        )
