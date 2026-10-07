# tool-011-expose-issue-schedule-and-spent-hours: Read issue dates and spent hours

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-011-expose-issue-schedule-and-spent-hours` |
| Assigned capability | Let a client identify Bugs whose start and due dates both fall in a chosen month, then calculate the sum of their visible direct spent hours. |
| Type | Extend existing `list_issues` and `get_issue` tools |
| Access | Read |
| Destructive effects | None |
| Status | blocked |
| Dependencies | [prep-002](prep-002-offline-tests.md) supplies offline verification; [tool-001](tool-001-list-issues-search.md) supplies project, tracker, status, and pagination; [tool-010](tool-010-list-issues-by-target-version.md) supplies `include_subprojects=false` for exact-project queries, with its acceptance still pending |
| Related tasks | [tool-005](tool-005-list-trackers.md) resolves the Bug tracker ID; [tool-002](tool-002-get-issue-context.md) owns existing detail expansions |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Implementation finished; static checks pass. Offline and synthetic acceptance remain pending under a separate testing assignment. |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

### Client outcome and repository baseline

The client asked for every Bug in **History Alpha Operations** whose start and end dates are in
September 2026, followed by the total spent time of those Bugs. In Redmine, this specification
interprets "end date" as the issue's `due_date`. The current `list_issues` can filter by project
and tracker, include closed issues with `status_id="*"`, exclude subprojects, and page through all
matches. `get_issue` can retrieve one issue. Their shared `Issue` model omits `start_date`,
`due_date`, `spent_hours`, and `total_spent_hours`; Pydantic therefore drops those upstream fields.
The earlier client query could enumerate 13 Bug candidates but could not verify their dates or
calculate hours. No current MCP tool lists time entries or computes a spent-time aggregate.

The existing route -> service -> `IssueReader` Protocol -> `RedmineIssues` gateway uses
`GET /issues.json` and `GET /issues/{id}.json`. `bootstrap.py` already wires that gateway and
`mcp/registration.py` already allowlists both stable operation IDs. This task requires no new
route, tool, upstream endpoint, dependency, or credential. Preserve existing working-tree edits
to the issue stack, task 010, the dashboard, tool reference, and changelog. The repository's
English Markdown and no automatic unit-test execution instructions apply.

### Upstream evidence

| Source URL or versioned source | Date verified | Version supported | Endpoint/behavior | Permission required | Evidence or limitation |
|---|---|---|---|---|---|
| Previously inspected Redmine issue detail API view (prior source inspection; current release review pending) | 2026-09-30 | prior sample | `GET /issues/{id}.json` emits `start_date`, `due_date`, `spent_hours`, and `total_spent_hours` | `spent_hours` fields only when `view_time_entries` is allowed on the project | Lines 13-22 show the dates and permission gate; detail is version-pinned evidence. |
| [Redmine Issues REST guide](https://www.redmine.org/projects/redmine/wiki/Rest_Issues) | 2026-09-30 | General reference; detail checked against prior sample source | `GET /issues.json`, paging, status/project/tracker filters, start and due date fields | Existing visible-issue access | The list example contains both dates; the guide does not prove a stable server-side date-range filter for both fields. |
| [Redmine issue-list spent-hours change](https://www.redmine.org/issues/34857) and Redmine change record | 2026-09-30 | Previously observed; target verification pending | Issue-list API adds `spent_hours` and `total_spent_hours` | Redmine's spent-time visibility rules | Historical release evidence; confirm the exact prior sample list payload in opt-in synthetic acceptance. |
| [Redmine roles reference](https://www.redmine.org/projects/redmine/wiki/RedmineRoles) | 2026-09-30 | General reference | View spent time and time-log visibility | `view_time_entries`; role can restrict visible entries to own | A visible issue does not prove that all project time entries are visible to the shared account. |
| `src/redmine_mcp/features/issues/models.py`, `integrations/redmine/issues.py`, and `mcp/registration.py` | 2026-09-30 | Current repository | Shared issue projection and existing MCP operations | Existing shared reader | Static code inspection only; no live Redmine response was used as acceptance evidence. |

The upstream issue fields already exist. The current public model drops them. `spent_hours`
means time recorded directly against an issue and visible to the shared Redmine account;
`total_spent_hours` includes descendant issue time and must not be summed across a set of issues
that may contain parents and children. The project-level total requested here uses only direct
`spent_hours` for each selected issue. This is an inference from the distinct upstream field
names and Redmine's [issue spent-time behavior](https://www.redmine.org/projects/redmine/wiki/RedmineIssues);
synthetic acceptance must confirm it on the pinned instance. A role limited to its own time logs
may receive a numeric visible-hours subtotal; non-null hours alone do not prove access to every
user's time logs.

### Requested outcome inventory

| Client outcome / tool | Existing coverage | Read/write | Version support | Task ID | Dependencies | In scope/deferred |
|---|---|---|---|---|---|---|
| Find all Bugs in one exact project | `list_issues` plus tracker lookup | Read | Current repository | Existing tools | tool-001, tool-005, tool-010 | Existing capability |
| Identify issues with both dates in September | Dates are dropped | Read | prior sample detail view and REST list example | tool-011 | prep-002 | In scope: expose dates and filter complete pages client-side |
| Sum spent time for those issues | Hours are dropped | Read | prior sample detail view; list field source review pending | tool-011 | prep-002 | In scope: expose direct hours and define client summation |
| Filter time entries by `spent_on`, or return an aggregate in one server call | No current tool | Read | Separate Time Entries API | Unassigned | New client outcome | Deferred |

### Questions and decisions

| ID | Question/assumption | Evidence or decision | Blocking? | Resolution date |
|---|---|---|---|---|
| DEC-001 | What does "end date" mean? | Use Redmine issue `due_date`; `closed_on` and time-entry `spent_on` describe different dates. | No | 2026-09-30 |
| DEC-002 | Add a new MCP operation or extend existing issue tools? | Extend `list_issues` and `get_issue`; both already return the shared `Issue` model. | No | 2026-09-30 |
| DEC-003 | Does September constrain when time was logged? | No. The condition is on issue `start_date` and `due_date`; sum all visible direct hours currently recorded for qualifying issues. | No | 2026-09-30 |
| DEC-004 | How is missing or restricted spent-time permission represented? | Map omitted upstream hour fields to `null`, never zero. Numeric fields reflect only entries visible to the shared account; a role restricted to its own time logs may return a numeric subtotal. | No | 2026-09-30 |
| DEC-005 | How are subtasks counted? | Sum only direct `spent_hours` once per qualifying issue ID. Do not add `total_spent_hours`, which can overlap descendants. | No | 2026-09-30 |
| DEC-006 | How are both date conditions applied? | The client reads every page of the existing issue query and retains issues with inclusive `2026-09-01 <= start_date, due_date <= 2026-09-30`. Missing dates do not match. No upstream date filter is specified. | No | 2026-09-30 |

## 3. Requirements

### Goal and boundaries

- Intended user and outcome: an MCP client can answer the September 2026 Bug question with an
  auditable issue list, both issue dates, individual hours, and a complete sum when authorized.
- In scope: expose nullable issue dates and two permission-gated hour fields on list and detail;
  document complete-page filtering and direct-hour summation.
- Out of scope: a new aggregate tool, server-side date filters, time-entry records or `spent_on`
  filtering, issue URLs, changing Redmine permissions, and writes.
- Future enhancements: a bounded aggregate or time-entry reader requires a separate client
  outcome and permission/response contract.
- Compatibility constraints: preserve both operation IDs, routes, inputs, defaults, page shape,
  issue identity fields, expansions, errors, and existing authentication.
- Permission/configuration prerequisites: the requesting Redmine user needs visible issues and
  `view_time_entries` with sufficient time-log visibility for a complete total.

| ID | User need and intended outcome | Required observable behavior | Prerequisites/constraints |
|---|---|---|---|
| REQ-001 | Determine whether each Bug starts and ends in the selected month. | `list_issues` and `get_issue` return ISO date or `null` for `start_date` and `due_date`. | Omitted upstream date maps to `null`; malformed present date fails safely. |
| REQ-002 | See time logged on each qualifying Bug. | Both tools return nonnegative numeric `spent_hours` and `total_spent_hours`, or `null` if Redmine omits them. | Permission-gated; `null` is unknown/unavailable, not zero. |
| REQ-003 | Calculate the visible direct-hours total for all qualifying Bugs. | Client can exhaust pages, filter both dates inclusively, deduplicate issue IDs, and sum direct `spent_hours` using decimal arithmetic. | Use `status_id="*"`; report unavailable if any selected issue has `spent_hours: null`; do not claim all users' hours unless reader visibility is verified. |
| REQ-004 | Keep existing clients working. | Existing operation names, request contracts, response wrapper, auth, and error mapping remain. | Additive issue fields only. |

Example client request: `list_issues({"project_id":8,"tracker_id":1,"status_id":"*",
"include_subprojects":false,"limit":100,"offset":0})`. IDs are illustrative. Suppose
one returned Bug has `start_date="2026-09-03"`, `due_date="2026-09-25"`, and
`spent_hours=1.5`: it qualifies. A Bug with `due_date=null` does not. If one qualifying issue
has `spent_hours=null`, the client lists it and states that the total is unavailable or partial.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| Existing or new tool | Extend `list_issues` and `get_issue`; no new MCP tool |
| Stable operation IDs | `list_issues`, `get_issue` |
| Purpose and tool description | Add that results include issue start/due dates and permission-gated direct and descendant-inclusive spent hours; guide callers to page all results before summing direct hours. |
| REST method and route | Existing `GET /api/v1/issues` and `GET /api/v1/issues/{issue_id}` |
| Authentication and authorization | Caller personal `X-Redmine-API-Key`; Redmine controls that user's issue and time visibility. |
| MCP exposure | Existing explicit allowlist entries; refreshed OpenAPI/MCP response schema only. |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty behavior | Upstream mapping |
|---|---|---|---|---|---|
| Existing `list_issues` query | Existing types/defaults | Unchanged | Existing validation | Unchanged | Existing `GET /issues.json` parameters |
| Existing `get_issue` path and include | Existing types/defaults | Unchanged | Existing validation | Unchanged | Existing `GET /issues/{id}.json` |

There is no new date or spent-time input. To include closed Bugs, callers set `status_id="*"`.
For the exact project, callers set `include_subprojects=false`; they increase `offset` until
the reported `total` is exhausted. Results are not a snapshot if Redmine changes during paging.

### Outputs and mapping

- Add `start_date: date | None = None` and `due_date: date | None = None` to the shared issue
  model. Serialize as `YYYY-MM-DD` or JSON `null`.
- Add `spent_hours: nonnegative finite number | None = None` and
  `total_spent_hours: nonnegative finite number | None = None`. Preserve upstream JSON numbers;
  reject booleans and numeric strings; map omitted fields to `null`. Do not synthesize zero,
  fetch time entries, or infer permission from the mere presence of an issue.
- A qualifying issue has both dates within the same requested inclusive calendar range.
  The requested September 2026 range is `2026-09-01` through `2026-09-30`.
- Sum `spent_hours` over unique qualifying issue IDs with decimal arithmetic. A complete total
  of account-visible hours requires non-null `spent_hours` for every qualifying issue.
  Confirm all-time-log visibility before describing it as the total across all Redmine users.
  `total_spent_hours` is displayed only as issue context and is not part of this sum.
- Example addition to one existing issue object:

```json
{
  "id": 154,
  "subject": "[HISTORY-004] Document work",
  "start_date": "2026-09-03",
  "due_date": "2026-09-25",
  "spent_hours": 1.5,
  "total_spent_hours": 2.0
}
```

The example is illustrative, not a claim about issue 154's actual dates or hours. All other
existing issue fields and the `items`/`total`/`limit`/`offset` page wrapper remain.

- Pagination, ordering, and expansions: unchanged. Date filtering occurs after every relevant
  upstream page has been read. `get_issue` retains its current default and selected expansions.
- Upstream calls: existing `GET /issues.json` for each requested list page and
  `GET /issues/{id}.json` for detail. Parse fields from each returned `issue` object.
- Upstream and public success: existing 200 response and MCP result behavior.
- Compatibility: additive response fields; no new inputs, calls, tools, or dependency changes.

### Errors

| Scenario | Detection layer | REST status and safe error | MCP result | Retry/reconciliation behavior |
|---|---|---|---|---|
| Invalid existing input | Router | Existing 422 validation response | Existing tool error envelope | Correct input. |
| Missing/invalid MCP authentication | Shared dependency | Existing 401 | Existing tool error envelope | Supply valid personal Redmine API key. |
| Redmine credential rejected | Shared client | Existing 502 `upstream_authentication` | Existing tool error envelope | Fix server credential. |
| Forbidden or invisible issue | Shared client | Existing 403 or 404 | Existing tool error envelope | Respect reader visibility. |
| Time permission absent but issue visible | Model mapping | 200 with nullable hour fields | Successful result containing `null` | Do not treat `null` as zero; obtain appropriate reader access outside this task. |
| Timeout or transport failure | Shared client | Existing 504 or 502 | Existing tool error envelope | Retry read; pages may change. |
| Malformed present date/hours or upstream JSON | Mapping/client | Existing sanitized 502 `upstream_response` | Existing tool error envelope | Inspect upstream configuration; never fabricate a value. |
| Other unsuccessful upstream status | Shared client | Existing 502 `upstream_error` | Existing tool error envelope | Follow existing handling. |

### Write semantics

N/A - read-only. Calls have no intended Redmine state changes.

Specification exit check: the public fields, permission/null semantics, filtering, aggregation,
and compatibility are resolved. Exact issue-list payload on the pinned instance remains an
acceptance check, not a public-contract decision.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Verification |
|---|---|---|---|---|
| 1 | Keep the existing reader and offline baseline; do not change credentials. | `docs/plans/tasks/prep-002-offline-tests.md`, configuration | prep-002 | Review baseline and auth contract. |
| 2 | Add nullable ISO dates and nonnegative finite nullable hour fields to shared `Issue` model. | `features/issues/models.py` | 1 | Model mapping scenarios. |
| 3 | Confirm list/detail gateway and mapper retain the fields without extra upstream calls. | `integrations/redmine/issues.py`, `mapping.py` | 2 | Exact upstream request and response scenarios. |
| 4 | Update caller-facing descriptions for existing tools; keep service/port signatures and bootstrap wiring. | `features/issues/router.py`, service/ports/bootstrap review | 2 | REST and MCP schema scenarios. |
| 5 | Document field semantics and a complete-page September aggregation recipe. | `docs/tool-reference.md`, `CHANGELOG.md` if release notes are required | 4 | Documentation review. |
| 6 | Add meaningful offline scenarios and separately perform authorized synthetic acceptance. | Existing offline test suite, `docs/manual-verification.md` if needed | 2-5 | Scenario IDs below. |

Dependency/configuration changes: N/A; existing Pydantic, FastAPI, HTTPX, and Redmine reader
are sufficient. The implementation phase must respect the user's separate test authorization.

## 6. Acceptance criteria and traceability

| Criterion ID | Given | When | Then |
|---|---|---|---|
| AC-001 | Upstream list/detail issue has both dates | Caller reads either tool | Both ISO dates appear unchanged. |
| AC-002 | Upstream omits one or both dates | Caller reads either tool | Missing dates are `null`, and those issues cannot satisfy a both-dates range. |
| AC-003 | Reader can view time entries | Caller reads list/detail issue | Direct and descendant-inclusive hour values appear as numbers; direct value 0 stays 0. |
| AC-004 | Reader cannot view some time entries | Upstream omits hour fields | Both hour fields are `null`; no false zero or complete total is reported. |
| AC-005 | A multi-page project Bug query mixes qualifying, nonqualifying, open, and closed issues | Client pages with `status_id="*"`, filters both dates, and sums direct hours | Each qualifying ID is counted once; sum excludes descendant-inclusive totals and reports incomplete when a selected hour value is null. |
| AC-006 | Existing clients call either issue operation | New fields are deployed | Names, inputs, defaults, page wrapper, expansions, auth, and errors remain compatible. |
| AC-007 | Upstream sends malformed present date/hours | Caller reads affected issue | Sanitized `upstream_response` error; no partial numeric answer. |

| Requirement | Acceptance criterion | Verification method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001, AC-002, AC-007 | DATE-001, DATE-002, DATE-003 | Pending | Pending |
| REQ-002 | AC-003, AC-004, AC-007 | HOURS-001, HOURS-002, HOURS-003 | Pending | Pending |
| REQ-003 | AC-005 | AGG-001, AGG-002, LIVE-001 | Pending | Pending |
| REQ-004 | AC-006 | COMPAT-001, MCP-001 | Pending | Pending |

## 7. Test plan and execution record

### Scenario plan

Plan tests only. Repository instructions prohibit automatic unit-test execution without user
acceptance or an explicit testing assignment. Default automated scenarios use fake settings,
HTTPX MockTransport, ASGI lifespan, and MCP SDK client checks; no real credentials.

| Scenario ID | Acceptance criteria | Layer/method | Setup and input | Expected result | Offline/live |
|---|---|---|---|---|---|
| DATE-001 | AC-001 | Mapper and REST | List/detail payloads with `2026-09-01` and `2026-09-30` | Dates retained as ISO strings. | Offline |
| DATE-002 | AC-002 | Mapper and REST | Omitted/null start or due date | Public null; issue excluded by sample client filter. | Offline |
| DATE-003 | AC-007 | Mapper and REST | Invalid present date | Sanitized 502. | Offline |
| HOURS-001 | AC-003 | Mapper and REST | Direct 1.5, descendant-inclusive 2.0; separately direct 0 | Numeric values retained, including zero. | Offline |
| HOURS-002 | AC-004 | Mapper and REST | Upstream omits hour fields due to permission | Public nulls; no complete aggregate. | Offline |
| HOURS-003 | AC-007 | Mapper and REST | Negative, infinite, or malformed present hours | Sanitized 502. | Offline |
| AGG-001 | AC-005 | Client workflow | Two pages; both date boundaries, missing date, out-of-range issue, duplicate parent/child references | Correct unique-ID direct-hour sum. | Offline |
| AGG-002 | AC-005 | Client workflow | One qualifying issue with null direct hours | Total marked incomplete, never 0. | Offline |
| COMPAT-001 | AC-006 | REST regression | Existing list/detail inputs, defaults, expansions, auth, and failure fixture | Existing contracts preserved. | Offline |
| MCP-001 | AC-006 | MCP SDK client | Discover and invoke `list_issues` and `get_issue` | Stable names and new response fields. | Offline |
| LIVE-001 | AC-003, AC-005 | Inspector on marked synthetic Previously inspected Redmine | Query exact History Alpha Operations Bug set; inspect list/detail, dates, hours, and reader permission | Pinned list payload and manually computed visible direct-hour total agree; do not seed/reset merely for this reader check. | Opt-in live |

- Defaults, filters, encoding, pagination, optional fields: DATE-001, DATE-002, AGG-001, COMPAT-001.
- Invalid inputs rejected before upstream access: COMPAT-001, existing issue tests.
- Exact upstream query and response mapping: DATE-001, HOURS-001, COMPAT-001.
- Successful, empty, malformed, and unsuccessful responses: DATE-001 through DATE-003,
  HOURS-001 through HOURS-003, COMPAT-001.
- Missing authentication and insufficient permissions: COMPAT-001, HOURS-002, LIVE-001.
- Existing tool names, contracts, and unrelated behavior: COMPAT-001, MCP-001.
- MCP discovery, invocation, annotations, and error envelopes: MCP-001, COMPAT-001.
- Write payloads, duplicate calls, unknown outcomes, and resulting state: N/A - read-only.

Execution record: static checks passed on 2026-09-30 from Git Bash:
`uv run --frozen --no-sync ruff check .` (all checks passed),
`uv run --frozen --no-sync ruff format --check .` (81 files formatted),
`uv run --frozen --no-sync mypy src` (38 source files, no issues), and
`git diff --check` (no whitespace errors). Unit tests, startup, Inspector, and live Redmine
verification were not run under this coding-only assignment. Record synthetic fixture IDs and
runtime results only after a separate authorized testing assignment.

## 8. Implementation and review record

- Changes made: shared `Issue` model now exposes nullable ISO `start_date`/`due_date` and
  nonnegative finite nullable `spent_hours`/`total_spent_hours`. Present dates must be
  `YYYY-MM-DD` strings; present hours must be JSON numbers, excluding booleans and strings.
  Existing mapper converts malformed present fields to sanitized `upstream_response` errors.
  List/detail routes describe the new fields; gateway, services, inputs, calls, and operation IDs
  remain unchanged.
- Plan deviations and reasons: none; the existing gateway and mapper already forward issue
  objects to the shared model without dropping recognized fields.
- Quality and automated test results: Ruff lint/format, mypy, and diff whitespace checks pass;
  automated tests were not written or run under this assignment.
- Startup and Inspector results: pending.
- Documentation updated: `docs/tool-reference.md`, `CHANGELOG.md`, this task, and dashboard.
- Final diff review: issue model and router additions preserve the in-progress tool-010 edits;
  no new credentials, upstream calls, or write behavior. Static diff whitespace check passes.
- Pre-existing failures versus introduced failures: no static failures observed.
- Remaining defects/blockers: offline scenario implementation/execution and marked synthetic
  Inspector acceptance require a separate authorized testing assignment. Tool-010 acceptance
  is also pending for the exact-project query prerequisite.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed.
- [x] Documentation reflects the final behavior.
- [x] No unresolved decision changes the specified behavior.
- [x] Final diff reviewed and task record synchronized.

Final status: blocked; implementation finished, testing pending.

Outcome: both existing issue tools expose schedule dates and permission-gated spent-hour fields;
the public guide explains how to filter and sum the qualifying Bugs.

Missing prerequisite or remaining work: implement and run DATE-001 through DATE-003, HOURS-001
through HOURS-003, AGG-001/002, COMPAT-001, MCP-001, and LIVE-001 after a separate testing
assignment; confirm tool-010 exact-project acceptance and reader time-entry visibility.

Next action: hand off to the separate testing stage, then update acceptance evidence and status.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

DATE, HOURS, AGG, COMPAT, and MCP offline cases pass. Thirteen Operations Bugs have matching list date/hour fields and sampled detail fields. No issue qualifies for September 2026, so LIVE-001's nonempty hours aggregate remains pending.

See [the dated verification ledger](../../testing/evidence/prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_issues/get_issue date and direct hours` functional evidence is mapped in the
[32-operation ledger](../../testing/evidence/current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H1 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
