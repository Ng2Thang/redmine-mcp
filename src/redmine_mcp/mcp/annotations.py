from mcp.types import Tool, ToolAnnotations

from redmine_mcp.auth import WRITE_OPERATIONS


def annotate_read_tools(tools: list[Tool]) -> None:
    """Publish client hints; authorization is still enforced by the REST route."""
    for tool in tools:
        tool.annotations = ToolAnnotations(
            readOnlyHint=tool.name != "download_attachment" and tool.name not in WRITE_OPERATIONS,
            destructiveHint=tool.name
            in (
                "delete_attachment",
                "update_time_entry",
                "delete_time_entry",
                "update_issue_note",
                "delete_issue_relation",
                "remove_issue_watcher",
                "update_project_members",
                "delete_project_members",
            ),
            idempotentHint=tool.name != "download_attachment" and tool.name not in WRITE_OPERATIONS,
            openWorldHint=True,
        )
