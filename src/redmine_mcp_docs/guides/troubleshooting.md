# Troubleshooting and FAQ

Start with the symptom below. When asking an administrator for help, include the action,
time, sanitized error code, and `X-Request-ID` when available. Keep keys and private content
out of shared logs and screenshots.

## Connection and access

### The client cannot connect

Check that the server is running and the URL ends in `/mcp`. Use **Streamable HTTP** and
ensure the client sends `X-Redmine-API-Key`. `/docs` is a REST reference, not an MCP endpoint.

If the client runs on another machine, `localhost` points there, not to the MCP server.
Ask for a reachable URL. A Docker-hosted server also needs a Redmine URL reachable from
its container; Windows-hosted Redmine commonly uses `host.docker.internal`. See
[MCP server installation](installation.md) and [connection details](first-calls.md).

### Authentication fails with 401

Use your personal Redmine API key, not a password, Inspector session token, or retired
shared MCP token. Check REST API access and the intended active account. Configure the
header once; repeated key headers are rejected. Reconnect after changing credentials.

### An action is missing or returns 403

Check whether you connected to the reader. Writes need a separate writer, enabled operation,
admitted caller, and native permissions. Ask the administrator to check those settings.
Seeing a candidate does not guarantee target access. See [access setup](access.md) and
[write actions](write-actions.md).

### An issue returns 404

Confirm its ID and your account. It may be absent or hidden by project/private-issue
permissions; 404 does not distinguish those cases. Check Redmine using the same account
before assuming the record was deleted.

## Inputs and results

### Results are empty or incomplete

Confirm project, assignee, status, and date filters. Issue lists default to open issues;
use `status_id: "*"` to include closed issues. Issue dates and time-entry dates answer
different questions. Check whether subprojects are included.

Check `pagination_policy`. `requires_narrowing=true` marks a preview; narrow supported
filters before continuing. `scope_required` and `scan_budget_exceeded` mean the original
collection did not finish. Report partial or unavailable results explicitly. Complete
pagination still covers only records visible to your account.

### Input is rejected with 422

Review the error and input schema. Use returned positive IDs, explicit dates, and correct
types. For example, issue-list `assigned_to_id` uses a string like `"42"`, while
`create_issue.project_id` is numeric. Categories require a project filter. Native required
fields or workflow rules can also reject input. Consult the [reference guide](reference.md).

### A read is slow or returns 502, 503, or 504

Reduce page size or optional expansions where useful and narrow broad filters. If it
persists, ask the operator to check Redmine availability, safe error codes, capacity, and
deadlines. `upstream_response` can indicate an unexpected Redmine payload; smaller requests
will not necessarily fix it. Do not automatically repeat a write.

### A write timed out or its result is uncertain

The change may already exist. Check Redmine and any receipt ID before another attempt.
Repeating a creation, note, or time-entry request can create duplicates. Failed read-back
does not undo an accepted write. See [outcomes](write-actions.md#read-the-outcome).

## Frequently asked questions

### Why do I see less than a colleague?

Each key has its own Redmine permissions. Private issues, notes, and logs can differ
between users. Missing numeric values are unavailable, not automatically zero.

### Can the client read attachment contents?

Tools provide metadata and authenticated browser links. Direct MCP downloads are disabled.
Open the link in Redmine; browser login and permissions still apply.

### Can I delete an issue or search all issue text?

There is no general issue-deletion or full-text search tool. Use supported issue filters.
Some other records, such as time entries, have dedicated writer deletion actions.

### Does a time report show all work done?

It shows visible recorded time, not unlogged effort. `total` counts entries, not hours.
See [time reports](time-report.md).

### Is the pilot ready for every production workflow?

This is an unreleased pilot targeting Redmine 7.0.2. Operation-specific acceptance and gaps
are recorded in the [reference](reference.md) and roadmap. Historical results do not verify
your deployment, another version, or current working-tree edits.

For runtime settings, security policy, and server operations, use
[Operate and maintain the server](contributors.md#operate-and-maintain-the-server).
