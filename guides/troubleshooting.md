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
a valid personal API key, and native permissions. Ask the administrator to check those settings.
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

## Setup and testing

### The sample stack reports an occupied port

The 7.0.2 stack uses Redmine 8001, MCP 8000, and PostgreSQL 5433. The 6.0.1 stack uses
3001, 8002, and 5436. Startup identifies a conflicting container or service; stop that
identified service before retrying. Reruns reuse services owned by the selected project.
Old `redmine-mcp-test*` projects are retained and may still occupy these ports.
See [sample server setup](installation.md#docker-with-sample-data).

### Pytest exits with E2E preparation failed

No test case has run yet. Inspect the selected project's private preparation log first:

```bash
cat .local/e2e/redmine-mcp-dev-7-0-2/pytest-prepare.log
```

Use `redmine-mcp-dev-6-0-1` for 6.0.1. `compose-up.log` contains startup diagnostics;
`seed.log` contains native fixture diagnostics. Those files may not exist if the failure
happened earlier. Confirm Docker Desktop is running, the required ports are available,
and the selected profile matches the intended version. Keep private keys and logs out of
shared reports. See [Testing and evidence](testing.md) for automatic preparation and reruns.

### The selected env file is not marked as synthetic

Current built-in profiles use no env file and ignore root `.env`. This message indicates
a custom env-file profile or older setup code. Clear exported custom E2E settings using
[the testing instructions](testing.md#commands-for-an-authorized-assignment), then confirm
the checkout has the current launcher. A custom profile needs its own marked synthetic
configuration. Do not add a synthetic marker to an external-instance `.env` to bypass checks.

### Pytest shows PydanticDeprecatedSince211

The pinned FastAPI-MCP dependency has an annotation that calls an older Pydantic schema
hook. This warning is separate from a preparation failure or failed test assertion. Check
pytest's final result and exit message. Fixing the dependency requires a compatible change;
editing `.venv` directly would be lost when dependencies are installed again.

### I deleted local files but the E2E fixtures still exist

Database records and development seed state live in Docker volumes. Deleting Python caches
or helper scripts does not reset them. Deleting an E2E manifest removes its ownership record,
so preparation refuses to adopt colliding records just by name. Use the documented
[guarded reset](testing.md#reset-and-preparation-failures) only when the selected synthetic
data can be discarded. Development and E2E resets retain different state; inspect their
boundaries before switching between demo data and fresh test fixtures.

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
