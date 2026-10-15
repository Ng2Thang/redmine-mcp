# Manual verification

## Scope and authorization

This guide describes procedures; it does not authorize their execution. Run automated tests,
startup, Inspector or live calls only in an explicitly assigned verification stage. Documentation
review uses manual source/prose/example/link inspection without executing the examples.
Reader smoke checks do not authorize mutations, fixture creation or permission changes.

The [2026-10-07 acceptance ledger](testing/evidence/current-catalog-acceptance.md) supersedes older pending
summaries for its dated 17-read/15-write catalog: 1,086 offline and 21 owned Redmine 7.0.2 live cases
passed. It includes version and membership acceptance, `allowed_all`, and Inspector discovery
plus three read calls; Inspector performed no mutations in PREP-020. H1..H6 preserve wider
historical limitations. Repeated checks are new work, not evidence already produced by this guide.
Later preparation and time-entry acceptance, waivers and remaining gaps are recorded in the
[current roadmap summary](plans/index.md#catalog-status-2026-10-09) and the sections below.

## Project time-entry activities (testing waived)

[TOOL-040](plans/tasks/tool-040-list-project-time-entry-activities.md) implements
`list_project_time_entry_activities` at
`GET /api/v1/projects/{project_id}/time-entry-activities`. The user waived testing on 2026-10-08;
runtime acceptance remains unverified. The procedures below are retained for future assignments;
the earlier catalog ledger does not cover this operation. Execute TOOL-040-001..005 only in a
separately authorized verification stage.

- Add offline input, adapter, REST/MCP and capability cases for strict project/activity IDs,
  names, exact project detail/include mapping, upstream errors and read-only annotations.
  Update existing all-reader argument maps and project reader fakes for the new operation.
- Distinguish a present empty activity expansion from an omitted one: only the latter adds
  `/items` with `state=not_returned`. Reject null/nonarray expansions, malformed or duplicate
  activity IDs, invalid names and wrong project identities.
- On an owned marked Redmine 7.0.2 environment, compare populated/empty project activity lists
  with the native expansion under permitted and no-view accounts. Include inactive activities,
  project overrides and forbidden projects. Record the actual runtime version.
- In Inspector, discover the reader and invoke it with the same project. Check ID/name output,
  visibility observations and conditional `view_time_entries` capability evidence. Do not infer
  a caller default or permission to log time from catalog membership.
- If synthetic setup is separately authorized, track and restore only task-owned fixtures.
  This reader does not log time or administer activities. The shared localhost:3000 6.0.5
  instance is not a substitute for pinned 7.0.2 acceptance.

## Own-time entry creation (testing pending)

[TOOL-041](plans/tasks/tool-041-create-time-entry.md) adds writer-only `create_time_entry` at
`POST /api/v1/issues/{issue_id}/time-entries`. Its coding stage runs static checks only.
Implement/execute TOOL-041-001..009 in a separately authorized testing assignment:

- Add request/service/gateway coverage for numeric/date validation, supplied nulls, unsupported
  user/project/custom/batch fields, strict IDs, comments, exact POST body and resolved project
  query parameter, caller attribution and native default selection.
- Cover caller authentication, disabled writer, operation gates, explicit CSV/allowed_all,
  issue-derived `log_time`, conditional/unknown evidence, native denied targets, and callers who
  can log own time but cannot view time entries.
- Cover accepted/mismatching/unavailable independent GETs, native minute/two-decimal rounding,
  invalid/empty 201 identity/body, 5xx, dispatched timeout and pre-dispatch failure. Assert one
  POST and preserved acceptance/uncertainty, including when a later GET matches.
- Extend catalog argument/payload maps and writer-only synthetic mocks for the new operation.
  Verify REST/MCP schemas, discovery, annotations, allowed_all, capabilities and old-reader/writer
  compatibility. Existing tests remain untouched until that testing assignment.
- On an owned marked Redmine 7.0.2 writer, create two task-owned eight-hour logs on an explicit
  date and compare exact native entries, IDs and caller/date/activity fields. Exercise native
  role/project defaults, no-default rejection, invalid activities, required comments, daily-hour
  partial success, closed/future policies and permission boundaries in authorized owned fixtures.
- Use owned response-loss/500 injection and reconciliation for ambiguous commits, then delete
  only exact task-created IDs using the authorized cleanup mechanism. Track failure/ambiguity;
  deleting an entry cannot undo delivered webhook effects. Inspector creation calls are live
  writes and need this explicit verification authorization. Do not use the shared 6.0.5 instance
  as pinned 7.0.2 acceptance or reset it for this feature.

## Time-entry update acceptance

[TOOL-042](plans/tasks/tool-042-update-time-entry.md) implements `update_time_entry` at
`PUT /api/v1/issues/{issue_id}/time-entries/{time_entry_id}`. The user subsequently authorized
testing on 2026-10-08. [Recorded evidence](testing/evidence/tool-042-testing.md) covers 61 unit/99
dedicated integration cases, 10 owned native/Inspector cases, exact cleanup and scoped checks.
The full offline run had 1,755 passes and one old catalog argument failure corrected in a passing
targeted rerun; seven late cases pass separately. No clean final full-suite rerun is claimed.
Future authorized rechecks retain the following coverage:

- Cover strict partial-update inputs, supplied null/empty/unknown body rejection, comments
  clearing and date/hour/activity rules. Verify exact issue/entry/project/user preflight;
  malformed/wrong-target responses must send no PUT. Omitted fields must not enter the payload.
- Cover credited user versus submitting author, own/all/no-edit/log-only callers, caller authentication, deployment
  modes, writer gates, discovery, capability reports, explicit CSV and allowed_all. Role evidence
  remains conditional/unknown; native visibility/editability is final.
- Cover no-body 204, native hour rounding, matched/mismatch/unavailable observations, GET failure,
  5xx and dispatched timeout with one PUT and preserved acceptance/uncertainty. Extend catalog
  fixtures/operation maps without weakening existing reader or creation coverage.
- In the owned marked 7.0.2 environment, use disposable exact-ID entries. Check native field
  changes, stable identity, omitted fields, unrelated controls, role/settings rejection and
  authorized concurrency/fault observations. Inspector update calls are live mutations and
  require this separate assignment. Record resulting state and exact owned cleanup.

Do not use reported entries #919–#924 as fixtures or modify the shared server merely to test.
The operation is implemented and accepted within the documented owned environment and current
native policy settings. No production deployment or exhaustive policy/plugin/race coverage is claimed.

## Time-entry deletion acceptance

[TOOL-043](plans/tasks/tool-043-delete-time-entry.md) implements `delete_time_entry` at
`DELETE /api/v1/issues/{issue_id}/time-entries/{time_entry_id}`. The user separately assigned
testing on 2026-10-08. [Evidence](testing/evidence/tool-043-testing.md) records 32 unit/82 dedicated
integration cases, 1889 clean full offline passes and 12 owned native/Inspector cases, plus
scoped checks and exact cleanup. Future authorized rechecks retain TOOL-043-001..009 coverage:

- Add unit/service and gateway tests for positive IDs, exact entry/issue/project/credited-user
  preflight, missing/project-only/malformed targets and zero DELETE on rejection. Verify exactly
  one native DELETE with no body/query and no retries.
- Add permission and REST/MCP tests for own credited user versus author, all/no-edit/no-view,
  caller authentication and deployment gates, explicit CSV/allowed_all, conditional capability reports and
  destructive/non-idempotent hints. Update shared catalog operation maps and synthetic transport
  fixtures to support this new operation while preserving reader/update/creation cases.
- Cover native 204, dispatched timeout/5xx/unexpected 2xx, validation rejection and known
  pre-dispatch failure. Verify independent not_found/still_present/unavailable observations,
  unchanged receipt outcomes and duplicate preflight404 without a second mutation.
- Use the owned marked pinned 7.0.2 environment for isolated writer startup and Inspector.
  Delete only recorded disposable entry IDs; verify actual absence through authorized native
  fixture evidence, spent-time totals and preservation of unrelated control entries. Caller 404
  alone is insufficient. Cover own/all/denied roles, fault/visibility/race observations and
  independent multi-call receipts. Reconcile uncertain outcomes and clean up remaining owned
  resources, recording exact cleanup and limitations.

Do not use reported entries #919–#924 or change shared/global settings merely to test this tool.
Acceptance is scoped to the recorded owned environment and controlled faults/race; broader
plugin/policy/infrastructure variants remain disclosed in the evidence record.

## Bounded Redmine GET retries

[PREP-027](plans/tasks/prep-027-redmine-read-retries.md) implements shared GET retry.
The separately assigned [verification record](testing/evidence/prep-027-testing.md) documents
103 focused offline cases, 2 owned live reader cases and startup/Inspector discovery plus three
read calls. Full regressions and passing targeted corrections complete acceptance as recorded
there. For future authorized rechecks,
use the following coverage; do not exercise failure scenarios against a real or shared instance.

- Cover each eligible exception/status followed by success and exhaustion; assert the final
  existing REST/MCP result, unchanged parameters and exact physical-attempt count.
- Cover Retry-After seconds/dates, malformed/repeated values, delay caps, jitter and disabled
  retries with controlled clocks/sleep; close responses and release capacity before waits.
- Cover partial streams, cancellation, per-GET and parent deadlines, aggregate request/byte
  accounting, and cooperative membership batch time after an already accepted mutation.
- Cover invalid JSON/model/attachment metadata, permissions, HTTP 500 and local saturation
  with a single attempt; preserve per-user keys and sanitized logs.
- Confirm one internal REST dispatch and one mutation per operation. Failed GET read-back
  retains the original write receipt; no whole-tool, batch, session or mutation replay occurs.

## MCP compatibility boundary

[PREP-026](plans/tasks/prep-026-mcp-sdk-compatibility-boundary.md) isolates pinned vendor hooks;
SDK-026-001..006 were assigned for verification on 2026-10-07; current execution results are
in [Preparation regression testing](testing/evidence/prep-022-026-testing.md). For future authorized
rechecks, inspect that identified private accesses only
remain in `mcp/compatibility.py`. Inject incorrect package metadata and absent/wrong request,
handler/cache/context and transport/lifecycle hooks; expect the safe startup failure before ready.
Use the actual pinned pair rather than installing alternate versions. Lifecycle fixtures should
patch the compatibility module and provide a valid server/transport with the required shapes.

Verify repaired nullable/union schemas with two callers, immutable invocation cache, caller-specific
discovery and cross-caller session rejection. Check exact membership DELETE JSON, fresh read/list
budgets, sanitized REST/tool errors and accepted/uncertain writer receipts with one mutation at
most. Exercise manager failure before readiness, cancellation before its first coroutine step,
cancellation after entry, repeated lifecycle entry and shutdown/cleanup errors. Assert readiness
is only published after `run()` yields, startup cannot hang, the owned task settles and both HTTP
clients close in the existing order. Authorized Inspector/native parity uses owned Redmine 7.0.2
fixtures and cleanup only of task-owned resources. The earlier coding dependency waiver and
coding-only handoff are historical; use the shared verification record for current acceptance.

## Declared upstream fields

[PREP-025](plans/tasks/prep-025-strict-upstream-fields.md) hardens known resource fields.
FIELD-025-001..006 are covered by the assigned [preparation verification](testing/evidence/prep-022-026-testing.md).
For future authorized rechecks, parameterize root, nested, list,
parent, custom-field and receipt IDs with bool/string/float/zero/negative values. Check strict
flags, nonnegative counts/sizes, 0/100 progress boundaries, unrestricted positive project status,
and signed/null relation delays. Confirm safe upstream errors without raw Pydantic input.

Retain native-style required fields in journal, watcher and attachment preflight/read-back
fixtures; sparse identity-only fixtures must be expanded where those resource models now validate
the observation. Check valid dates, finite nonnegative numeric hours, defaults, omitted/null
optional fields, empty collections, parent dictionary shape and existing unknown-field policy.
Compare rejected preflight with accepted mutations followed by malformed observations: assert
zero versus one native mutation, original receipt preservation and unavailable verification.
Include update and copy issue preflight with malformed progress, flags and nested references;
both must return a sanitized upstream error before their PUT/POST, with zero mutation calls.
Use native-shaped issue fixtures and retain omitted/null optional-field compatibility.
Authorized Inspector/live parity uses the owned pinned 7.0.2 environment with ordinary
restricted writer credentials; verify resulting state and remove only task-owned resources.
The coding-only handoff has been superseded by the separately authorized testing assignment.

## Request-body admission

[PREP-024](plans/tasks/prep-024-bounded-request-bodies.md) implements admission before REST/MCP
parsing; BODY-024-001..006 are covered by the assigned
[preparation verification](testing/evidence/prep-022-026-testing.md). For future authorized rechecks,
use raw ASGI fixtures for exact cap/cap+1,
missing/chunked/understated lengths, identical/conflicting duplicates, negative/malformed lengths,
completed mismatches and non-identity encoding. Assert sanitized 400/413/415 errors, correlation
headers and zero downstream parser/authentication/native dispatch on rejection. Include huge
decimal lengths, empty chunks, accepted byte replay, disconnect and cancellation.

Check compact uploads at decoded N-1/N/N+1 against default and custom body/binary caps. Verify
that invalid base64 and existing writer gates retain their service/authorization behavior.
Exercise MCP POST admission, GET/SSE, session DELETE and internal REST error conversion without
double dispatch or interrupted accepted responses. Authorized startup/Inspector/live checks use
the owned pinned Redmine 7.0.2 writer environment and task-owned tool-020 upload fixtures;
verify resulting temporary attachment state and clean up only those owned attachments.
Do not reset shared data. The SDK manager uses the same effective body cap as the outer
middleware. Attach uploaded artifacts to a disposable issue before deleting that issue;
native attachment deletion cannot remove an unattached upload. The shared verification record
documents cleanup of interrupted owned artifacts.

## Issue estimates and general spent-time logs

The user authorized the testing stage for [tool-034](plans/tasks/tool-034-list-issue-estimates.md)
and [tool-035](plans/tasks/tool-035-list-time-entries.md) on 2026-10-06. Dedicated offline,
owned Redmine 7.0.2 live and Inspector checks passed; see the tasks for execution evidence.
Within a separately authorized verification assignment, repeat the focused checks in Git Bash
against the owned environment:

```bash
uv run --frozen --no-sync pytest tests/unit/test_time_entry_search.py tests/integration/test_issue_estimates.py tests/integration/test_time_entries_overview.py -q
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e/test_reporting_acceptance.py --run-e2e -q
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/prepare-e2e.py
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/verify-reporting-inspector.py
```

The preparation helper adds only owned fixtures; live tests delete their disposable issues and
logs. Inspector creates a temporary reader-only server and stops it afterward. Keep its private
header configuration and evidence in ignored `.local/e2e/redmine-mcp-dev-7-0-2/`.
Pytest prepares automatically; the explicit preparation command above is for the standalone
Inspector script. Use `REDMINE_E2E_VERSION=6.0.1` consistently and its corresponding project
directory to inspect 6.0.1. Do not reset a shared deployment for a read check.

- Compare `list_issues` and `get_issue` estimates with same-key native Redmine responses.
  Verify numeric estimates, explicit null and missing-field evidence; sum eight 12-hour
  estimates to 96 hours only when the complete selected scope actually contains those values.
- In Inspector, discover `list_time_entries` and call it across projects with inclusive
  `spent_from`/`spent_to` dates, then with project, credited user (`"me"` and an ID) and issue
  filters. Compare IDs, references, hours, dates and counts with native `time_entries.json`.
- Compare exact-project and descendant-inclusive scopes independent of the native default
  subproject setting. Include an owned project-only entry and check nullable `issue_id`.
- Compare own-log and all-log reader roles, inaccessible projects and module-disabled scopes.
  Complete pagination must still be labeled caller-visible.
- Exercise permitted pagination and broad-query narrowing; deduplicate entry IDs and sum
  `hours` with decimal arithmetic. Check safe malformed-response/budget cases offline and
  ensure partial collections never produce an asserted complete total.


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

The [prep-015 task](plans/tasks/prep-015-bounded-redmine-reads.md) owns the original bounded-read
criteria. Selected budget/proxy/attachment-link evidence has passed; consult the current ledger
and coverage matrix for the exact scope and remaining broader variants.
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

The historical coding handoff deferred download-tool tests and old paging expectations.
Subsequent testing records are linked in the current ledger; preserve the original record rather
than treating that earlier deferral as the current result. These procedures remain available for
an authorized regression assignment.

For separately authorized multi-user verification on the marked synthetic writer, use distinct
ordinary personal keys privately. Verify both users can read/connect and attempt configured
writes according to their native permissions without a writer key or user admission list.
Reusing a session ID with a different
user or rotated key must return 404 before dispatch, including GET and DELETE; the original
caller must retain its session. The detailed fixture/state matrix is in
[prep-014](plans/tasks/prep-014-multi-user-writer-acceptance.md). Do not execute those writes merely
to perform a reader smoke check.

For writer discovery, compare two users with contrasting complete project memberships.
Their write candidates should differ while reader names, schemas and annotations remain stable.
Call a hidden or previously cached tool directly: its current permissions must still be checked.
Repeat discovery after changing only an owned synthetic role; no other user's catalog may change.
Public non-member or incomplete permission data is intentionally shown as a candidate rather
than treated as definitive denial. Inspect target behavior separately from list visibility.

This guide records operational smoke checks. It does not add an automated test suite or establish
production readiness. Full permission, restore, and failure-recovery verification remains in the
[testing roadmap](testing-roadmap.md).

## Target version creation (separate authorization required)

[tool-032](plans/tasks/tool-032-create-project-version.md) owns its acceptance scenarios.
PREP-020 completed selected offline/native 7.0.2 state, duplicate and permission checks, plus
Inspector schema/read compatibility. The steps below are a regression procedure, not pending
current acceptance or authorization to repeat mutations. Use the isolated marked
7.0.2 environment, its restricted writer, and task-owned versions; preserve the shared 6.0.5
environment. Read credentials privately and record only redacted evidence.

1. Configure only the authorized writer operation and an ordinary caller with `manage_versions`.
   Inspect discovery, capability reporting, annotations, and the generated REST/MCP schemas.
2. Create a uniquely named version with description and due date. Compare the returned ID and
   resulting Redmine state: owning project, exact name, optional fields, open status, no sharing.
3. Repeat the name with different metadata. Expect existing ID/data and the explicit
   `version_already_exists` error. Confirm version count and existing metadata remain unchanged.
4. Compare denied project permission, excluded caller, excluded operation, and the reader
   deployment; no denied call may mutate state. A caller with `manage_versions` but no
   `view_issues` can create, while verification is unavailable and unreadable duplicates retain
   the validation error.
5. Use offline transports for timeout, malformed responses, shared/ambiguous duplicate matches,
   and read-back failure. Confirm one mutation attempt and correct acceptance/uncertainty.
6. Clean up only recorded task-owned version IDs with the separately authorized fixture
   procedure. Never delete a pre-existing version returned as a duplicate.

## Project membership management (live authorization required)

Offline unit/service/gateway and REST/MCP tests cover tool-033, including lifespan startup and
DELETE JSON body forwarding. PREP-020 passed TOOL-033-011 with owned native **7.0.2** state,
managed/protected roles, inheritance, assignment effects and disposable cleanup. Inspector
verified catalog/schema and membership reads; it performed no mutations. The
[combined task](plans/tasks/tool-033-project-members-management.md) and current ledger retain
exact evidence and historical handoffs. These steps are future regression scenarios, requiring
explicit live authorization; the shared **6.0.5** container is not target evidence. Preserve
shared users, projects and memberships.

1. Run the authorized offline regression command recorded in the combined task and review
   scenario coverage. Offline protected/inherited-role assertions use a synthetic upstream;
   record the actual native behavior separately during target-version acceptance.
2. Prepare owned ordinary users with manager access in one project and denied access in
   another, plus visible groups, direct/inherited memberships, protected roles and a parent/child
   project. Record initial membership roles and category/project default assignees.
3. Verify the reader exposes list only. In Inspector list one/two projects, paginate each,
   inspect users/groups/inherited flags and public `view_members` access. Exercise page/read
   budget errors and distinguish unavailable projects from empty membership pages.
   Include repeated role IDs from two groups or parent inheritance, and mixed direct/inherited
   rows. Expect one role per ID with inheritance true if any source is inherited. Confirm
   conflicting names/malformed role flags remain errors and duplicate requested role IDs fail.
   On a continued-page batch, make one project exceed its page scope while another fits;
   require the scoped rejection and the other project's readable page in the same result.
4. Configure only authorized membership writer operations. Check disabled gates, missing
   operations, caller authentication, native permissions, scoped capability reports and
   caller-specific discovery. An administrator must still pass MCP gates.
5. Submit invalid IDs/arrays/extra fields, duplicates, mismatched membership/project IDs,
   group writes and inherited deletes. A mixed batch with one known failure must perform
   zero mutations. Confirm malformed upstream data and incomplete inventories fail safely.
6. Add owned users; confirm exact native payload, one attempt and resulting memberships.
   Repeat add and simulate a concurrent duplicate; require explicit existing membership
   outcomes with no update fallback. Update roles and inspect inherited/protected retention,
   including accepted updates with mismatch verification and valid 200/204 empty responses.
7. Delete an eligible owned user membership; verify visible absence using the complete bounded
   project inventory. A 404 or access loss alone must yield unavailable verification. Inspect
   descendant propagation and category/project default-assignee effects separately.
8. Exercise mid-batch 403/422 versus shared authentication/outage/budget failures, server errors,
   timeouts, cancellation and failed read-back. Preserve accepted peers, stop later dispatches
   when required, and confirm no retry or rollback. Revoke the caller's management role in an
   earlier item and confirm fresh evidence before later writes.
   Hold admission capacity until the remaining batch deadline expires, then release it.
   Require no queued mutation dispatch, a released permit, retained earlier receipts and
   not-executed later items. Cover direct/proxy admission and reader compatibility as well.
9. Reconcile attempted project/user pairs or membership IDs after every uncertain/interrupted
   outcome before a new request. Restore only task-owned memberships, roles and assignments;
   record actual tool outputs, native state, cleanup and limitations. A future change needs
   its own evidence; do not infer acceptance from the existing suite count alone.

## Preparation and startup

For the automated E2E fixture environment, follow
[versioned stack preparation](testing-roadmap.md#selecting-a-redmine-release).
PREP-029 reuses the 6.0.1 stack on localhost:3001 and 7.0.2 on localhost:3002.
The built-in projects are `redmine-mcp-dev-6-0-1` and `redmine-mcp-dev-7-0-2`. They use
self-contained Compose files and ignore root `.env`. Their demo seed manifests live in
Docker's `seed_state` volumes; E2E manifests and logs live in `.local/e2e/<project>/`.
Standalone Inspector/browser scripts require preparation first; native fixture scripts
use `/e2e-state`. Pytest invokes preparation automatically with `tests/e2e --run-e2e`.
Preserve earlier dated evidence; it does not verify subsequent setup refactors.

Use an existing synthetic environment or deliberately create one with `bash scripts/dev-up.sh`.
That command starts containers and creates sample data in named Docker volumes; it does not
create a host env file or run tests. E2E can also start PostgreSQL/Redmine directly without
the development seed or Docker MCP service. Both startup paths mutate synthetic data.
For an external instance, use only the read-only calls below with an appropriately restricted key.
Never seed, reset, or restore a real instance for verification.

Confirm startup finishes without errors, then check liveness:

```bash
curl --fail --silent --show-error http://localhost:8002/health
```

Expected body: `{"status":"ok"}`. This endpoint does not contact Redmine, so successful tool
calls are still needed to check upstream connectivity and credentials.
The examples use the 7.0.2 sample reader on port 8002. Substitute port 8001 for the 6.0.1
sample reader, port 8000 for local Python, or the actual port for an external deployment.

## MCP Inspector

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Open the printed Inspector URL with its session token. Select **Streamable HTTP**, set the server
URL to `http://localhost:8002/mcp`, and configure its authentication header privately:

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
curl --silent --show-error --include http://localhost:8002/api/v1/projects
```

Repeat the Inspector connection using an omitted or deliberately invalid Redmine key and confirm
that protected tool access is rejected. Restore the valid key privately afterward.

In Swagger at `http://localhost:8002/docs`, use **Authorize** with your Redmine API key.
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
automated scenario assertions or outstanding recovery acceptance.
