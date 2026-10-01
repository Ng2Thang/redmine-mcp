# Manual verification

This guide records operational smoke checks. It does not add an automated test suite or establish
production readiness. Full permission, restore, and failure-recovery verification remains in the
[testing roadmap](testing-roadmap.md).

## Preparation and startup

Use an existing synthetic environment or deliberately create one with `bash scripts/dev-up.sh`.
That command creates configuration, containers, and sample data; it is not a read-only check.
For an external instance, use only the read-only calls below with an appropriately restricted key.
Never seed, reset, or restore a real instance for verification.

Confirm startup finishes without errors, then check liveness:

```bash
curl --fail --silent --show-error http://localhost:8000/health
```

Expected body: `{"status":"ok"}`. This endpoint does not contact Redmine, so successful tool
calls are still needed to check upstream connectivity and credentials.

## MCP Inspector

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Open the printed Inspector URL with its session token. Select **Streamable HTTP**, set the server
URL to `http://localhost:8000/mcp`, and configure its authentication header privately:

```text
X-Redmine-API-Key: <your personal Redmine API key>
```

Inspector's session token is different from the Redmine API key. Do not capture either in
screenshots, reports, or logs.

1. Connect and list tools. Confirm `list_issue_time_entries` appears with the existing readers.
2. Call `list_projects` with `{"limit":25,"offset":0}`. Expect visible project objects and
   `total`, `limit`, and `offset` pagination values.
3. Call `list_issues` with `{"status_id":"*","limit":25,"offset":0}`. Expect visible issues;
   save an actual returned ID for the next call.
4. Call `get_issue` with `{"issue_id":<returned ID>}` after replacing the placeholder with an
   integer. Expect matching issue details and visible journals/attachment metadata where present.
5. Call `list_issues` with `{"limit":1,"offset":0}` and then `{"limit":1,"offset":1}`.
   On an unchanged dataset with at least two open issues, expect different issue IDs and matching
   pagination fields. Omitted status defaults to `open`.
6. If relevant to the change, exercise project, closed-status, and `assigned_to_id:"me"` filters
   using known visible data. `me` is the requesting Redmine user.
7. On a marked synthetic issue with time entries, call `list_issue_time_entries` with
   `{"issue_id":<returned ID>,"limit":25,"offset":0}` after replacing the placeholder.
   Compare credited user IDs, hours, dates, and the visible count with Redmine's time-entry
   page for that exact issue. Page through all entries before totaling. Record whether the
   reader can see all users' entries; an empty page alone does not establish that.

For the complete synthetic seed, the expected count using the `demo-mcp-reader` key with
`status_id:"*"` is 128.
After the optional history seed, the expected count is 391 before any manual changes.
Repeat a read with another synthetic user's personal key and compare visible projects and
issues. The server must use that user's Redmine visibility; exact counts depend on their role.
Compare against [synthetic data](test-data.md) and the private local manifest. Record mismatches;
do not treat one matching count as proof that every permission boundary is correct.

## Authentication and validation

Without the personal-key header, the following read-only REST request should return `401`
and `{"detail":"Missing or invalid Redmine API key"}`:

```bash
curl --silent --show-error --include http://localhost:8000/api/v1/projects
```

Repeat the Inspector connection using an omitted or deliberately invalid Redmine key and confirm
that protected tool access is rejected. Restore the valid key privately afterward.

In Swagger at `http://localhost:8000/docs`, use **Authorize** with your Redmine API key.
Request `GET /api/v1/issues` with `limit=0`; expect REST status `422` and validation details.
If a known absent or inaccessible issue ID is available, read it and check that the response does
not disclose its contents; Redmine may return forbidden or not-found behavior depending on access.
Do not guess sensitive IDs on a real instance. See the [tool reference](tool-reference.md) for
sanitized errors and the distinction between REST status and MCP tool-error envelopes.

## Quality checks and recording results

```bash
bash scripts/check.sh
uv run --frozen pre-commit validate-config
```

Record results in the change or review description, using this template:

```text
Revision / working-tree changes:
Environment: synthetic / external (no secrets or private host details)
Python and tool versions:
Startup and health: pass / fail / not run, with reason
Tool discovery and each tool call: pass / fail / not run, with reason
Authentication, validation, and pagination: pass / fail / not run, with reason
Quality checks: pass / fail / not run, with reason
Known limitations and deferred checks:
```

Record only redacted summaries, not complete issue bodies or credentials. Do not perform reset,
backup, or restore merely to validate documentation. Successful smoke checks do not replace the
deferred automated and recovery tests.
