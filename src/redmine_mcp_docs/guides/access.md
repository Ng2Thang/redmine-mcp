# Reader and writer access

Your personal Redmine API key determines which account is used. You can only read or
change what that account is allowed to access in Redmine. Connecting an AI client does
not grant extra Redmine permissions.

## Choose reader or writer

| Your task | Connection | Example |
| --- | --- | --- |
| Read projects, issues, or time logs | Reader | Show my open issues. |
| Create an issue or add a note | Enabled writer | Add this progress note to issue #123. |
| Log or correct time | Enabled writer | Log 1.5 hours on issue #123 for the specified date. |

The local reader normally uses port `8000`; the separate writer normally uses `8001`.
Use the actual URL supplied by your administrator. The writer also offers reads, but
available write actions depend on deployment configuration and caller discovery.

Connect using [MCP client installation](get-started.md), then follow
[Make and review changes](write-actions.md) to check your account's candidate actions,
select a target, and interpret the result. If an action is missing, check the connection
and ask your administrator whether the action is enabled on the writer and your Redmine
permissions allow it for the target. A visible tool is a candidate, not a guarantee of
permission on every target.

## Administrator setup

Keep the default reader read-only. Deploy the writer separately using
[writer configuration](../docs/configuration.md#separate-writer-deployment) and
[writer operations](../docs/operations.md#separate-writer).

Writer setup requires all of the following:

- `REDMINE_WRITE_ENABLED=true` in the writer runtime.
- A nonempty `REDMINE_WRITER_OPERATIONS` list containing the intended actions.
- A valid personal Redmine API key supplied by each caller.
- Native Redmine permissions for the actual target.

Each caller authenticates separately. The server does not check a writer key hash or user ID
admission list. Follow the linked configuration for exact values and commands.

An explicit operation list limits scope. Standalone `allowed_all` permits every registered
write, including new registrations after an upgrade. Restart or recreate the writer as
documented after changing configuration.
