# tool-012-list-issue-time-entries: Attribute spent hours on an issue

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-012-list-issue-time-entries` |
| Assigned capability | Let an MCP client identify the Redmine users whose time entries account for visible hours on selected issues. |
| Type | Add read-only `list_issue_time_entries` tool |
| Access | Read |
| Destructive effects | None |
| Status | blocked |
| Dependencies | [prep-002](prep-002-offline-tests.md) provides offline verification; [tool-011](tool-011-expose-issue-schedule-and-spent-hours.md) provides the issue selection and direct-hours context. Tool-011 acceptance is pending. |
| Related tasks | [tool-001](tool-001-list-issues-search.md) selects issues; [tool-010](tool-010-list-issues-by-target-version.md) supplies exact-project scoping. |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Historical field mapping recorded; 7.0.2 source review and synthetic acceptance pending. |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

### Client outcome and repository baseline

The client selected six Bugs in **History Beta Web** with both issue `start_date` and `due_date`
in August 2026, found that their visible direct time totals 27 hours, and asked who logged those
hours. `list_issues` and `get_issue` expose `spent_hours` but no time-entry records or user
attribution. Issue `author` and `assigned_to` do not identify whose hours a time entry records.
The client can reuse the existing issue tools to select Bugs, then invoke this tool for each
qualifying issue and group returned entries by `user.id`.

At discovery, the path was issue router -> `IssueService` -> `IssueReader` Protocol ->
`RedmineIssues` gateway, wired by `bootstrap.py`; `mcp/registration.py` explicitly allowlisted
tool operations. There was no time-entry route, model, service, port, gateway, or MCP operation.
The implementation reuses the
lifespan-managed `RedmineClient`, bearer authentication, `Page`, and visibility shape. Preserve
the staged edits to tool-010, tool-011, runtime code, docs, and changelog. The repository requires
English Markdown and prohibits automatic unit-test execution without user acceptance.

### Upstream evidence

| Source URL or versioned source | Date verified | Version supported | Endpoint/behavior | Permission required | Evidence or limitation |
|---|---|---|---|---|---|
| Previously inspected Redmine timelog controller (prior source inspection; current release review pending) | 2026-09-30 | prior sample | `GET /time_entries.json` has API auth, `total_count`, `offset`, and `limit`; it loads visible entries and their users. | Query visibility applies. | Lines 27-28, 39-56, 279-285; a single issue's visibility still needs a separate issue read. |
| Previously inspected Redmine time-entry query (prior source inspection; current release review pending) and base query (prior source inspection; current release review pending) | 2026-09-30 | prior sample | `issue_id` is an available exact-match filter; a simple `issue_id=<positive ID>` becomes `=` and the query orders ties by entry ID. | `view_time_entries`; `TimeEntry.visible` limits rows. | `issue_id` supports other operators upstream, but this tool sends only a positive numeric exact match. |
| [Redmine Time Entries REST guide](https://www.redmine.org/projects/redmine/wiki/Rest_TimeEntries) and [REST pagination guide](https://www.redmine.org/projects/redmine/wiki/REST_Api) | 2026-09-30 | General guide, checked against prior sample controller/query and API view | Time-entry listing and offset/limit page metadata. | Redmine account access. | The pinned API view establishes the required prior sample JSON fields. |
| [Redmine roles reference](https://www.redmine.org/projects/redmine/wiki/RedmineRoles) | 2026-09-30 | General guide | View spent time and role-level time-log visibility. | `view_time_entries`; a role may see all or only its own entries. | An empty list or numeric issue `spent_hours` does not prove access to all users' logs. |
| Previously inspected Redmine time-entry API view (prior source inspection; current release review pending) | 2026-09-30 | prior sample | Emits `time_entries`, page metadata, `issue.id`, credited `user.id/name`, rounded numeric `hours`, and `spent_on`. | Same visible-entry scope. | `issue` and `user` are conditionally emitted, so missing required fields cause a sanitized 502. |

The upstream `TimeEntry` model distinguishes the user credited for time from the entry author.
This tool returns the **credited user** from the time-entry API. It must not claim that this user
personally submitted the log, because logging on behalf of someone else is possible and the
proposed API response does not establish the entry author.

### Requested outcome inventory

| Client outcome / tool | Existing coverage | Read/write | Version support | Task ID | Dependencies | In scope/deferred |
|---|---|---|---|---|---|---|
| Select Bugs by project, tracker, and issue dates | Existing `list_issues` fields | Read | Current repository | tool-011 | tool-001, tool-010 | Existing capability |
| Read issue direct spent hours | Existing `get_issue` and `list_issues` fields | Read | Current repository | tool-011 | prep-002 | Existing capability |
| Identify credited users and hours behind one issue's visible time | No current tool | Read | prior sample timelog controller/query | tool-012 | prep-002, tool-011 | In scope |
| Identify who submitted an entry when different from its credited user | No established API field | Read | Not established for prior sample | Unassigned | Separate evidence/product need | Deferred |

### Questions and decisions

| ID | Question/assumption | Evidence or decision | Blocking? | Resolution date |
|---|---|---|---|---|
| DEC-001 | Extend `get_issue` or add a tool? | Add a paginated tool: time entries are a separate Redmine collection and can outgrow one issue response. Existing issue contracts stay stable. | No | 2026-09-30 |
| DEC-002 | What does “who logged the hours” mean? | Return the credited time-entry `user` with a clear label. Do not infer the submitter/author. | No | 2026-09-30 |
| DEC-003 | Are only August time entries included? | No. August selected the issue schedule. This tool returns all currently visible direct time entries on each chosen issue, regardless of `spent_on`. | No | 2026-09-30 |
| DEC-004 | Are child issue entries included? | No. Match `issue_id` exactly, consistent with tool-011's direct `spent_hours`. | No | 2026-09-30 |
| DEC-005 | Does zero returned entries mean zero time exists? | Only zero entries visible to the shared account. Do not assert project-wide completeness without permission verification. | No | 2026-09-30 |
| DEC-006 | Is the exact prior sample JSON field shape confirmed? | Pinned `app/views/timelog/index.api.rsb` emits the required fields and page metadata. | No | 2026-09-30 |

## 3. Requirements

### Goal and boundaries

- Intended user and outcome: an MCP client can name each credited user and the hours recorded
  directly on a selected visible issue, then aggregate across a known set of issue IDs.
- In scope: one issue per call, paginated visible entries, entry ID, exact issue ID, credited user,
  hours, `spent_on`, and visibility scope.
- Out of scope: author/submitter attribution, mutations, project-wide time reports, server-side
  aggregation, child issue entries, and filtering by when time was spent.
- Future enhancements: an author-aware capability only if a supported and authorized upstream
  source can expose the entry creator reliably.
- Compatibility: existing issue tools, schemas, names, defaults, and spent-hour meanings remain.
- Permission/configuration prerequisites: shared reader has issue visibility and Redmine
  `view_time_entries`; complete attribution across users requires all-time-log visibility.

| ID | User need and intended outcome | Required observable behavior | Prerequisites/constraints |
|---|---|---|---|
| REQ-001 | Identify whose hours contribute to a selected Bug. | Each returned entry has credited `user` ID/name and direct `hours`; entry and issue IDs allow audit and deduplication. | Only entries visible to the requesting Redmine user. |
| REQ-002 | Explain the total for several Bugs. | Complete pages per issue allow grouping by user ID and decimal summation of unique entry IDs. | Report a visible subtotal unless all-entry access is verified; do not sum issue `total_spent_hours`. |
| REQ-003 | Preserve issue and time-log access boundaries. | Invisible issue fails safely; visible issue with no visible entries returns an empty page and requesting-user visibility metadata. | No privilege escalation or database access. |
| REQ-004 | Keep existing clients working. | New route/tool is additive; existing `list_issues` and `get_issue` behavior is unchanged. | Explicit MCP allowlist entry. |

Illustrative client flow: read Bug IDs `181`, `229`, `277`, `325`, `373`, and `421` from the
August issue schedule, then page `list_issue_time_entries` for each. Group all returned entries
by `user.id`. The IDs identify the earlier synthetic case; no entry user or per-user hours are
claimed here. A zero-entry response for one issue means no entries visible to this reader.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| Existing or new tool | New `list_issue_time_entries`, because entries are a separately paginated collection. |
| Stable operation ID | `list_issue_time_entries` |
| Purpose and tool description | “List time entries visible to the requesting Redmine user that are logged directly on one issue. Each entry identifies the user credited with the hours; that user may differ from the person who submitted the entry. Page through all results before totaling hours.” |
| REST method and route | `GET /api/v1/issues/{issue_id}/time-entries` |
| Authentication and authorization | Caller personal `X-Redmine-API-Key`; Redmine enforces that user's issue and time-entry permissions. |
| MCP exposure | Add `list_issue_time_entries` to the explicit allowlist as read-only. |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty behavior | Upstream mapping |
|---|---|---|---|---|---|
| `issue_id` path | Integer | Required | Positive | Missing/invalid: 422 or route 404 under existing FastAPI behavior | `GET /issues/{id}.json` preflight; exact `issue_id` query on `/time_entries.json` |
| `limit` query | Integer | Optional, 25 | 1 through 100 | Omitted uses 25; null/empty invalid | `limit` |
| `offset` query | Integer | Optional, 0 | Nonnegative | Omitted uses 0; null/empty invalid | `offset` |

### Outputs and mapping

- Return `Page[IssueTimeEntry]`: `items`, `total`, requested `limit`, requested `offset`, and
  `visibility.scope="shared_redmine_account"`. `total` is the count of visible matches reported
  by Redmine. An empty `items` list is valid.
- Each item has positive `id`, positive `issue_id`, `user: {id: positive integer, name: string}`,
  nonnegative finite JSON-number `hours`, and ISO `spent_on` (`YYYY-MM-DD`). The public `user`
  label means **time credited to**. An omitted/malformed required value is a sanitized 502,
  never a guessed user, zero hours, or an entry without issue attribution.
- Example response (illustrative, not a claim about actual issue 181):

```json
{
  "items": [
    {"id": 9001, "issue_id": 181, "user": {"id": 26, "name": "Example User"},
     "hours": 1.5, "spent_on": "2026-08-18"}
  ],
  "total": 1,
  "limit": 25,
  "offset": 0,
  "visibility": {"scope": "shared_redmine_account", "observations": []}
}
```

- Gateway first reads `GET /issues/{issue_id}.json` with no expansions to establish issue
  visibility. It then reads `GET /time_entries.json?issue_id={issue_id}&limit={limit}&offset={offset}`.
  The exact positive numeric filter excludes descendants. Map Redmine `time_entries`,
  `total_count`, and each entry's `issue.id`, `user`, `hours`, and `spent_on` into the public page.
  Reject any returned entry whose `issue.id` differs from the requested ID.
- Upstream success is HTTP 200 with paged JSON; public REST success is HTTP 200 and MCP returns
  the normal tool-result envelope. Do not rely on undocumented `author` data.
- Ordering follows the pinned Redmine time-entry query default: `spent_on` descending, then
  entry ID as a tie-breaker. The public tool has no sort input. As with issue lists, pages are
  not a snapshot if Redmine changes during the query.
- For a six-issue answer, exhaust each page, deduplicate by entry ID, group by `user.id`, and
  sum `hours` with decimal arithmetic. Compare the visible entry sum with each issue's visible
  direct `spent_hours` as a diagnostic; differences do not identify a logger or prove a bug,
  because visibility and concurrent changes may differ.
- Compatibility: additive route and operation only. No dependency, configuration, or existing
  tool contract changes.

### Errors

| Scenario | Detection layer | REST status and safe error | MCP result | Retry/reconciliation behavior |
|---|---|---|---|---|
| Invalid caller input | Router | Existing 422 validation | Tool error envelope | Correct input; no resource request (identity verification may run). |
| Missing/invalid personal Redmine API key | Shared auth | Existing 401 | Tool error envelope | Supply a valid personal Redmine API key. |
| Redmine credential rejected | Shared client | Existing 502 `upstream_authentication` | Tool error envelope | Repair server credential. |
| Issue forbidden or invisible | Issue preflight/shared client | Existing 403 or 404 | Tool error envelope | Respect Redmine visibility. |
| No time entries visible | Gateway | 200 with `items=[]`, `total=0` | Successful empty page | Do not infer project-wide zero. |
| Upstream time-entry access denied | Shared client | Existing 403 `access_denied` | Tool error envelope | Obtain appropriate reader access. |
| Timeout or transport failure | Shared client | Existing 504/502 | Tool error envelope | Read retry is safe; paging may shift. |
| Malformed page, entry, or mismatched issue ID | Gateway/model mapping | Sanitized 502 `upstream_response` | Tool error envelope | Do not report partial attribution. |
| Other unsuccessful upstream status | Shared client | Existing 502 `upstream_error` | Tool error envelope | Investigate upstream safely. |

### Write semantics

N/A - read-only. The tool makes GET requests and has no intended Redmine state change.

Specification exit check: public purpose, input, visibility, pagination, errors, and pinned
entry field mapping are decided. The serializer rounds hours to two decimal places.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Verification |
|---|---|---|---|---|
| 1 | Inspect prior sample time-entry API view; revise mapping if needed. | Pinned Redmine source, this task | N/A | Record field evidence; permission confirmation remains for synthetic acceptance. |
| 2 | Add validated time-entry model and reader Protocol. | `features/time_entries/models.py`, `ports.py` | 1 | Mapping scenarios. |
| 3 | Add gateway with issue preflight, exact filter, pagination, and sanitized mapping. | `integrations/redmine/time_entries.py`, existing client/mapper as needed | 2 | Mocked upstream requests and failures. |
| 4 | Add service and REST route with validated path/page inputs and personal-key authentication dependency. | `features/time_entries/service.py`, `router.py`, `api/dependencies.py` | 3 | ASGI scenarios. |
| 5 | Wire service and register the stable MCP operation explicitly. | `bootstrap.py`, `app.py`, `mcp/registration.py` | 4 | MCP discovery/invocation. |
| 6 | Update public guide and manual verification instructions. | `docs/tool-reference.md`, `docs/manual-verification.md`, `CHANGELOG.md` | 5 | Documentation review. |
| 7 | Implement meaningful offline scenarios and separate opt-in synthetic acceptance. | Existing test suite and this task record | 1-6 | Scenario IDs below. |

Dependency/configuration changes: N/A. Use existing Python dependencies, reader key, and MCP
token. The testing stage requires the user's separate authorization under repository instructions.

## 6. Acceptance criteria and traceability

| Criterion ID | Given | When | Then |
|---|---|---|---|
| AC-001 | A visible issue has entries credited to two users | Client pages the new tool | Every visible entry has its own user, issue ID, date, and hours; per-user sums equal the visible entry total. |
| AC-002 | An issue has more than 100 visible entries | Client requests successive pages | All entries are discoverable once by stable ID, with reported total/offset. |
| AC-003 | An issue is invisible or the personal Redmine API key is invalid | Client calls the tool | Existing safe 403/404 or 401; no time-entry data leaks. |
| AC-004 | Reader sees only some or no time entries | Client reads a visible issue | Result is explicitly requesting-user scoped; an empty page is not labeled a global zero. |
| AC-005 | Redmine returns an invalid entry, page, or another issue's entry | Client calls the tool | Sanitized 502; no fabricated attribution or partial sum. |
| AC-006 | Existing issue tools are called after addition | Client uses old inputs | Names, defaults, page shapes, and behavior remain stable. |
| AC-007 | Pinned synthetic Redmine has issue entries | Inspector invokes tool after startup | Visible credited users and entry hours match the Redmine time-entry page for the same issue. |

| Requirement | Acceptance criterion | Verification method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001, AC-005 | ENTRY-001, ENTRY-004 | Pending | Pending |
| REQ-002 | AC-002, AC-007 | PAGE-001, AGG-001, LIVE-001 | Pending | Pending |
| REQ-003 | AC-003, AC-004 | AUTH-001, VIS-001, LIVE-001 | Pending | Pending |
| REQ-004 | AC-006 | COMPAT-001, MCP-001 | Pending | Pending |

## 7. Test plan and execution record

### Scenario plan

Plan only. Do not write or run unit tests until the user authorizes testing. When authorized,
use fake settings, HTTPX MockTransport, ASGI lifespan, and MCP SDK checks without real keys.

| Scenario ID | Acceptance criteria | Layer/method | Setup and input | Expected result | Offline/live |
|---|---|---|---|---|---|
| ENTRY-001 | AC-001 | Gateway/REST | One issue, entries for two users, distinct dates and decimal hours | Correct credited users and entry fields. | Offline |
| ENTRY-002 | AC-001 | Gateway/REST | Valid zero-hour entry and a user different from issue assignee/author | Zero preserved; attribution comes only from entry `user`. | Offline |
| ENTRY-003 | AC-004 | Gateway/REST | Visible issue, empty `time_entries` page | 200, `total=0`, requesting-user scope. | Offline |
| ENTRY-004 | AC-005 | Gateway/REST | Missing/malformed user, issue, hours, date, or cross-issue entry | Sanitized 502; no partial result. | Offline |
| PAGE-001 | AC-002 | Gateway/REST | More than 100 entries, two offsets | Exact filter/limit/offset; total and entries consistent. | Offline |
| AGG-001 | AC-001, AC-002 | Client workflow | Six issue pages with repeated credited users | Deduplicate entries by ID, group by user ID, sum with decimal arithmetic. | Offline |
| AUTH-001 | AC-003 | ASGI/gateway | Missing personal Redmine API key, rejected Redmine key, forbidden/invisible issue | Existing 401 and 403/404 semantics. | Offline |
| VIS-001 | AC-004 | ASGI/gateway | Time-entry query returns 403 or only reader-visible rows | Error or scoped subset; never claim all-user completeness. | Offline |
| COMPAT-001 | AC-006 | REST regression | Existing issue list/detail calls | Unchanged contracts and authentication. | Offline |
| MCP-001 | AC-006 | MCP SDK | Discover and invoke new and existing operations | New stable name present; old names unchanged; errors safe. | Offline |
| LIVE-001 | AC-007 | Inspector on marked Previously inspected Redmine | Read one synthetic issue and its time-entry page | Credited user IDs and hours match Redmine; record whether reader can see all entries. | Opt-in live |

- Defaults, filters, encoding, pagination, optional fields: PAGE-001, ENTRY-003.
- Invalid inputs rejected before upstream access: AUTH-001 plus positive-ID/page validation.
- Exact upstream query and response mapping: ENTRY-001, PAGE-001.
- Successful, empty, malformed, and unsuccessful responses: ENTRY-001/003/004, AUTH-001, VIS-001.
- Missing authentication and insufficient permissions: AUTH-001, VIS-001.
- Existing tool names and contracts: COMPAT-001, MCP-001.
- MCP discovery, invocation, and error envelopes: MCP-001.
- Write payloads, duplicate calls, and uncertain outcomes: N/A - read-only.
- Startup, live visibility, and cleanup: LIVE-001; no seed/reset/restore for this reader check.

### Execution evidence

| Evidence ID | Command/procedure and environment | Scenario/check | Expected | Actual redacted result | Status | Date |
|---|---|---|---|---|---|---|
| EVID-001 | `bash scripts/check.sh` in Git Bash after implementation | Static quality | Pass | Not run | Pending | N/A |
| EVID-002 | `uv run --frozen pytest` in Git Bash after separate test authorization | Offline scenarios | Pass | Not run | Pending | N/A |
| EVID-003 | Inspector on marked synthetic Previously inspected Redmine after separate authorization | LIVE-001 | Match visible time entries | Not run | Pending | N/A |
| EVID-004 | `uv run --frozen --no-sync ruff check .` in Git Bash | Static lint | Pass | All checks passed | Pass | 2026-09-30 |
| EVID-005 | `uv run --frozen --no-sync ruff format --check .` in Git Bash | Static format | Pass | 90 files already formatted | Pass | 2026-09-30 |
| EVID-006 | `uv run --frozen --no-sync mypy src` in Git Bash | Static types | Pass | Success: no issues found in 46 source files | Pass | 2026-09-30 |
| EVID-007 | `git diff --check` in Git Bash | Diff whitespace | Pass | No output; exit 0 | Pass | 2026-09-30 |
| EVID-008 | Authorized prep-004 read-only sample on previously marked synthetic fixture: app REST time-entry page and Redmine REST under the same restricted reader key | LIVE-001 partial | Match visible entries | History issue 151 returned three visible entries; IDs and count matched. Inspector separately discovered/invoked this tool, but credited users/hours/dates were not compared for issue 151. | Partial | 2026-10-01 |
| EVID-009 | `uv run --frozen pytest -q --tb=short` after prep-004 authorization | ENTRY-001 and ENTRY-004 partial | Mapping and wrong-issue rejection | One credited-user entry and exact upstream query passed; a cross-issue entry produced sanitized 502. Two-user, zero-hour, and malformed-field variants remain pending. | Partial | 2026-10-01 |

Verification limitations and missing prerequisites: prep-004 verification was authorized and
EVID-008 is a partial live sample. The planned offline cases and full LIVE-001 comparison remain
pending; all-user visibility is not established. The current runtime uses per-user
`X-Redmine-API-Key`; earlier bearer wording remains historical and needs contract reconciliation.

## 8. Implementation and review record

- Changes made: added validated time-entry model, reader port, service, Redmine gateway, bearer-
  protected REST route, bootstrap wiring, and explicit MCP registration. Gateway preflights issue
  visibility, filters exact issue ID, and rejects missing fields or mismatched issue attribution.
- Plan deviations and reasons: N/A; the pinned serializer matches the planned public fields.
- Quality and automated test results: EVID-004 through EVID-007 pass. The first Ruff run found
  three line-length and two formatting findings in new files; formatting those files resolved
  them. Automated tests were not run.
- Startup and Inspector results: not run under this coding-only assignment.
- Documentation updated: task, dashboard, tool reference, manual verification, and changelog.
- Final diff review: new route follows router -> service -> port -> gateway and uses only
  lifespan-managed HTTP. No secrets or logging were added. Unrelated edits were preserved.
- Pre-existing failures versus introduced failures: none in the final static checks.
- Remaining defects/blockers: tool-011 acceptance and separate test/synthetic verification remain
  pending for the full six-Bug workflow.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed.
- [x] Documentation reflects implemented behavior.
- [x] No unresolved contract decision changes the specified behavior.
- [x] Final implementation diff reviewed and task record synchronized.

Final status: blocked; implementation finished; testing pending.

Outcome: paginated, read-only issue time entries attribute visible hours to the credited
Redmine user.

Missing prerequisite or remaining work: implement and run planned offline scenarios; run
repository checks and marked synthetic Inspector acceptance; verify reader visibility.

Next action: authorize a separate testing stage for ENTRY-001 through ENTRY-004, PAGE-001,
AGG-001, AUTH-001, VIS-001, COMPAT-001, MCP-001, and LIVE-001.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

ENTRY, PAGE, AGG, AUTH, VIS, COMPAT, and MCP offline cases pass. Three live entries match Redmine by ID, issue, credited user, hours, date, and count. All-user completeness and the contrasting-role visibility matrix remain pending.

See [the dated verification ledger](../../testing/evidence/prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_issue_time_entries` functional evidence is mapped in the
[32-operation ledger](../../testing/evidence/current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H1 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
