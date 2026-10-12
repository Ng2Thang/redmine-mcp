# Supported tools and capabilities

See what you can do with Redmine MCP, which actions require writer access, and the limits
to expect. Follow [everyday workflows](workflows.md) for examples and copyable prompts.

## Tools by task

The registered catalog contains 18 reads and 18 writes. Your connection may expose fewer
actions. The default reader exposes reads; writes require a separate configured writer.

| Task | Tools to look up |
| --- | --- |
| Identify the caller and candidate actions | `get_current_user`, `list_my_project_capabilities` |
| Explore projects and memberships | `list_projects`, `get_project`, `list_project_members` |
| Find and read issues | `list_issues`, `get_issue` |
| Resolve status, tracker, and priority choices | `list_issue_statuses`, `list_trackers`, `list_issue_priorities` |
| Resolve project categories and versions | `list_project_issue_categories`, `list_project_versions` |
| Review time logs and activities | `list_time_entries`, `list_issue_time_entries`, `list_project_time_entry_activities` |
| Inspect files and attachment links | `list_project_files`, `get_attachment`, `get_issue` with attachments included |
| Create or update issues and notes | `create_issue`, `update_issue`, `update_issue_note` |
| Log or correct time | `create_time_entry`, `update_time_entry`, `delete_time_entry` |
| Manage versions and user memberships | `create_project_version`, `add_project_members`, `update_project_members`, `delete_project_members` |
| Manage relations and watchers | `create_issue_relation`, `delete_issue_relation`, `add_issue_watcher`, `remove_issue_watcher` |
| Upload or change attachments and project files | `upload_attachment`, `update_attachment`, `delete_attachment`, `add_project_file` |

This is a task-oriented selection, not an exhaustive schema listing. The
[full tool reference](../docs/tool-reference.md) explains every operation, scope, and receipt.
Your server's MCP schemas and REST OpenAPI at `/docs` supply exact accepted arguments.
Do not invent tool names or arguments from examples.

## Configuration and operations

| Question | Reference |
| --- | --- |
| Which server settings can I change? | [Runtime configuration](../docs/configuration.md) |
| How do I deploy a writer? | [Writer configuration](../docs/configuration.md#separate-writer-deployment) |
| How do I operate Docker or connect external Redmine? | [Operations](../docs/operations.md) |
| How do issue tags depend on plugins? | [RedmineUP tags](../docs/integrations/redmineup-tags.md) |
| How should credentials be handled? | [Security policy](../SECURITY.md) |

## Result boundaries

Lists are caller-visible and paginated; a preview is not a complete report. Missing values
are unavailable unless the contract says otherwise. Attachments provide metadata and links.
Writer acceptance and independent verification are distinct; see [write actions](write-actions.md).

The target is Redmine 7.0.2 and the implementation is an unreleased pilot. Activity discovery
testing was waived, and time-entry creation testing is pending. Existing evidence, gaps,
and later operation records remain in the [capability roadmap](../docs/plans/index.md).
Guide examples do not add runtime evidence.
