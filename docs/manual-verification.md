# Manual verification

## Current three-phase acceptance

The user authorized the testing implementation and its execution on 2026-10-05. Current selected
acceptance is recorded in [prep-016](plans/tasks/prep-016-unit-testing.md),
[prep-017](plans/tasks/prep-017-offline-integration-testing.md), and
[prep-018](plans/tasks/prep-018-live-e2e-testing.md), with a shared
[coverage matrix](plans/testing-coverage.md). The older assignment restrictions below remain
historical scope records; the new authorization applies to the selected scenarios.

Use the [testing roadmap](testing-roadmap.md) for the isolated 7.0.2 environment, automated E2E,
supplemental Inspector/browser commands and private credential handling. Do not upgrade or reset
the existing shared synthetic environment merely to run these checks.

## Bounded reads and attachment links (separately authorized)

The [prep-015 task](plans/tasks/prep-015-bounded-redmine-reads.md) owns pending acceptance.
Do not execute these scenarios without a separate verification assignment. Use offline fake
million-record totals rather than generating a million live synthetic issues.

- Compare a broad first-page preview with a continuation: the preview reports matching pages
  and `requires_narrowing`; continuation returns `scope_required` without fetching that page.
- Repeat with narrower existing filters and threshold/deep/nonaligned offsets. Observe the
  same-filter metadata probe and bounded capability inventory behavior.
- Inspect REST/MCP safe budget errors and semaphore permit release under concurrency,
  cancellation, transport failure and stream closure using offline transports.
  Attempt more than the configured concurrency limit (at least 51 for default 50) and verify
  active upstream responses never exceed that limit; include a smaller configured limit.
- Inspect generated time-entry tool descriptions and aggregation guidance: continuation must
  check pagination policy, stop on scope/budget errors, and label incomplete totals partial or
  unavailable. A large issue's time-entry breakdown must not imply unsupported date filters.
- Include synchronous response conversion that crosses the aggregate deadline before headers:
  REST must return `504 read_operation_timeout`, and MCP must retain the recognizable safe code.
- Cover process environment `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` and `NO_PROXY` routing,
  including wildcard bypass. Direct and proxy requests must share the configured semaphore;
  cancellation and response closure must release permits on both routes. Use fake proxy values
  and never record real proxy credentials.
- Verify `download_attachment` is absent from discovery; a cached call returns a tool error.
  The retired REST content route returns 403 without metadata or content acquisition.
- Read project/issue attachment metadata and open the returned public Redmine link in an
  authenticated browser. MCP must not fetch the link or return base64 content. Verify a public
  subpath mapping and malformed/off-origin metadata links separately.

Existing download-tool tests and old paging expectations need a later authorized update; this
coding assignment does not modify tests or execute the historical procedures below.

For separately authorized multi-user verification on the marked synthetic writer, use distinct
ordinary personal keys privately. In personal-key mode verify both users can read/connect and
an excluded write-admission user receives 403 for writes. Reusing a session ID with a different
user or rotated key must return 404 before dispatch, including GET and DELETE; the original
caller must retain its session. The detailed fixture/state matrix is in
[prep-014](plans/tasks/prep-014-multi-user-writer-acceptance.md). Do not execute those writes merely
to perform a reader smoke check.

For personal-key discovery, compare two users with contrasting complete project memberships.
Their write candidates should differ while reader names, schemas and annotations remain stable.
Call a hidden or previously cached tool directly: its current permissions must still be checked.
Repeat discovery after changing only an owned synthetic role; no other user's catalog may change.
Public non-member or incomplete permission data is intentionally shown as a candidate rather
than treated as definitive denial. Inspect target behavior separately from list visibility.

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

1. Connect and list tools. Confirm `get_current_user` and `list_issue_time_entries` appear with
   the existing readers.
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

For `get_current_user`, call with `{}` using an ordinary synthetic user's personal key.
Compare ID, login, names, returned email, visible project memberships, and roles against Redmine.
Repeat with another user's key to confirm caller identity changes. Where available, compare an
inherited role (`inherited=true`) and a non-inherited role (`inherited=false`). Check an account
with no visible memberships returns `memberships=[]`. Omitted email must be null with a `/mail`
`not_returned` observation. An empty membership list does not prove the user cannot access any
project. Confirm the result has no API key or additional account metadata and the catalog
publishes the existing read-only annotations. Keep credentials private.

Missing or rejected credentials must fail under the existing authentication contract.
Identity mismatch and malformed membership responses require separate offline adapter checks;
do not change live Redmine responses to simulate them. Detailed pending scenarios are in
[tool-013-get-current-user](plans/tasks/tool-013-get-current-user.md).

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
