# tool-035-list-time-entries: Read general spent-time logs

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-035-list-time-entries |
| Capability | Read caller-visible time logs across projects, users and dates for client overview totals |
| Type / access / destructive effects | Add read-only `list_time_entries` / read / none |
| Status | complete - implementation and authorized acceptance passed |
| Dependencies | Existing tool-012 time-entry feature, prep-015 bounded reader and tool-031 capability discovery; prep-002/016/017 infrastructure for later testing |
| Related tasks | [tool-034](tool-034-list-issue-estimates.md), independent; [dashboard](../index.md) |
| Target Redmine | Owned pinned 7.0.2-bookworm; native/REST/SDK acceptance passed |
| Last updated | 2026-10-06, Codex |
| Assignment | User requested implementation and separately authorized testing on 2026-10-06 |
| Next action | None for this assignment; repeat commands are recorded below |

## 2. Discovery and evidence

Clients need to answer questions such as "How much time was logged in September, grouped by
project and user?" without first discovering every issue. Existing `list_issue_time_entries`
requires an issue ID and issue-read preflight; its result model cannot represent project-only
logs. Retain that tool and add one general paginated reader, not a server aggregate endpoint.

| Source | Checked | Version / finding |
|---|---|---|
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-06 | Redmine 7.0.2 `timelog_controller.rb` exposes paginated JSON index |
| Release `time_entry_query.rb` and `query.rb` | 2026-10-06 | Project/user/issue filters, inclusive `from`/`to` date shortcuts, native `me` substitution, explicit subproject operators and entry-ID tie breaker |
| Release `time_entry.rb` and `timelog/index.api.rsb` | 2026-10-06 | Project-only entries allowed; API project, issue, user, activity, hours, comments and spent_on fields; native `view_time_entries` and own/all role visibility |
| `deploy/compose.test.yaml` | 2026-10-06 | Pins 7.0.2; the observed shared deployment is not automatically target-version evidence |

Use router -> service -> Protocol -> gateway, personal API-key identity, lifespan-managed
async clients, existing sanitized errors and bounded reads. Preserve pre-existing membership,
writer configuration, documentation and test edits. No subagents, tests, fixtures, startup,
Inspector or live writes are included in this coding assignment.

Resolved decisions: retain both capabilities; general results are logs, not server totals;
omitted dates impose no bound; exact-project is the default; issue references can be unavailable
without proving the entry is unattached; group client totals using returned stable references.

## 3. Requirements

| ID | Required outcome |
|---|---|
| REQ-001 | Read time entries across caller-visible projects, including project-only logs |
| REQ-002 | Filter by project/descendants, credited user or me, direct issue and inclusive log dates |
| REQ-003 | Return typed reference/hour/date fields and existing bounded page evidence |
| REQ-004 | Register REST/MCP and conditional project capabilities under native time-entry visibility |
| REQ-005 | Document accurate client totals/groupings without claiming incomplete or all-user totals |

Out of scope: writes, report UI, exports, server totals, author/assignee attribution, activity
filtering, global user discovery, database access and changing the existing issue-entry contract.

## 4. Public contract and technical specification

MCP `list_time_entries`; REST `GET /api/v1/time-entries`; upstream `GET /time_entries.json`.
Reader annotations: read-only, nondestructive, idempotent and open-world. Personal-key access
uses the existing read gate; Redmine decides project/module access and own/all-log visibility.
Project capabilities use `view_time_entries`, without requiring `view_issues` or issue preflight.

| Input | Type / default / validation | Native mapping |
|---|---|---|
| project_id | Optional positive integer | project_id; omission spans visible projects |
| include_subprojects | Boolean, false; true requires project_id | With project: subproject_id `!*` for false, `*` for true; omitted for a global scope |
| user_id | Optional positive integer or literal `me` | user_id, credited user; native me substitution |
| issue_id | Optional positive integer | Exact issue_id; descendants excluded |
| spent_from / spent_to | Optional ISO dates; each bound inclusive; reject from > to | from / to; filter spent_on rather than issue dates |
| limit / offset | Integers; 25 / 0; limit 1..100, offset >= 0 | Existing bounded pagination parameters |

Request fixed `sort=spent_on:asc`; Redmine adds the entry-ID tie breaker. Service query validation
is strict, rejects invalid bounds/scope before calling the reader, and accepts parsed calendar
dates from the router. No per-entry or issue-preflight fetches are introduced.

Return `Page[TimeEntry]` with existing `items`, count `total`, `limit`, `offset`, `visibility`
and `pagination_policy`. Each item has strict positive `id`, required project (`id`, `name`),
credited user (`id`, `name`), finite nonnegative JSON `hours`, ISO `spent_on`, nullable positive
`issue_id`, nullable activity (`id`, `name`) and nullable comments. Missing/null optional values
map to null; malformed present references fail instead of disappearing. Do not infer why an
issue reference is absent. Required malformed fields and invalid page metadata use sanitized 502.

Native time-entry pages require count/limit/offset metadata. Reuse the shared preview,
same-filter continuation probe, page ceiling and read budget behavior. No fabricated hour-total
field is added; `total` is an entry count. Narrowing guidance names supported filters.

Errors: local invalid inputs 422; missing/rejected identity 401; native forbidden/not-found
403/404; malformed/upstream/transport failures retain sanitized 502/504-family envelopes;
scope/budget errors retain their codes. No implicit retry or credential logging is added.

Client reporting deduplicates IDs after complete permitted paging and sums `hours` using
decimal arithmetic, optionally grouping by project/user/activity/day. Missing activities form
an explicit unavailable group. Totals are caller-visible; own-log restrictions may remain.
Incomplete collection means partial/unavailable totals. Do not add overlapping issue spent-hour
aggregates. Logs can change between pages; this is not snapshot reporting.

Write semantics: N/A - read-only; no Redmine state changes or new external side effects.

## 5. Implementation plan

| Step | Change | Dependency |
|---|---|---|
| 1 | Add general entry model and strict scoped/date query model | Existing hour/date validators |
| 2 | Extend reader Protocol and service; add general gateway mapping | Step 1; shared bounded client |
| 3 | Add overview REST router and register it before MCP creation | Step 2; existing container reused |
| 4 | Register read operation, MCP allowlist and conditional project rule | Step 3 |
| 5 | Update reference, changelog, manual scenarios, coverage and task/dashboard records | Steps 1-4 |
| 6 | Run static checks and review additive compatibility | Steps 1-5 |
| 7 | Add/execute offline and owned live scenarios in a separately authorized testing stage | User testing authorization |

No new dependency, lockfile, runtime configuration or writer operation is needed. Existing
bootstrap TimeEntryService/RedmineTimeEntries wiring serves both tools.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Verification |
|---|---|---|---|
| AC-001 | REQ-001,003 | General/project-only rows preserve required and nullable fields | TOOL-035-001,007 passed |
| AC-002 | REQ-002 | Correct combined filters, boundaries, exact/descendant scopes and early invalid-input rejection | TOOL-035-002,003,007 passed |
| AC-003 | REQ-003,005 | Bounded pages and client totals preserve count/completeness/visibility semantics | TOOL-035-004,005 passed |
| AC-004 | REQ-004 | REST/MCP registration, schema, annotations and native time-entry permission evidence | TOOL-035-006,007 passed |

## 7. Test plan and execution record

| Scenario | Planned setup / layer | Expected result |
|---|---|---|
| TOOL-035-001 | Offline gateway/REST: populated, project-only, empty and malformed rows; optional refs/comments | Typed mapping, nullable issue ID and sanitized required/present-ref errors |
| TOOL-035-002 | Service/REST strict IDs, user me, pages, ISO dates, reversed dates and descendants without project | Invalid input fails before time-entry access; valid date objects reach the port |
| TOOL-035-003 | MockTransport native requests with combined filters, each date bound alone, exact/descendant scopes, me and issue | Correct method/query/date encoding/order; no issue or per-entry fetch |
| TOOL-035-004 | Offline multiple pages, same-filter probe, missing/mismatched metadata, broad preview/deep offsets and read budgets | Existing safe limits and actionable narrowing; no asserted complete aggregate |
| TOOL-035-005 | Client reporting fixtures: decimals, duplicate IDs, projects/users/activities/days, own-only visibility, dates different from issue schedule | Correct visible totals and explicit incomplete/unavailable groups |
| TOOL-035-006 | Offline REST/MCP discovery/invocation/auth errors, schemas/annotations/capability rules, old issue-entry preflight; invoke positive numeric user_id and `me`, reject invalid user IDs | New reader exposed consistently; full user_id union survives conversion and SDK caching; view_time_entries evidence; preserved old behavior |
| TOOL-035-007 | Opt-in owned pinned 7.0.2 native/REST/MCP comparison with project-only entry, descendant project and contrasting roles | Actual IDs/counts/hours/date scope and own/all-log visibility match |

Later testing must extend all catalog expectations/counts, stateful reader fixtures and
TimeEntryReader fakes. Add meaningful gateway/service/REST/MCP scenarios; preserve old
preflight coverage. Use fake settings offline; use isolated marked 7.0.2 fixtures for live
acceptance without resetting the shared deployment.

| Evidence | Procedure | Actual | Status |
|---|---|---|---|
| EVID-001 | Git Bash prerequisite doctor | Required prerequisites ready | Passed 2026-10-06 |
| EVID-002 | `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .`; `uv run --frozen --no-sync mypy src`; `git diff --check` | Lint passed; 239 files already formatted; mypy passed for 120 source files; no whitespace errors | Passed 2026-10-06 |
| EVID-003 | TOOL-035-001..007 testing, startup and Inspector | Not run; excluded from coding assignment | Pending separate authorization |

## 8. Implementation and review record

Testing follow-up (2026-10-06): the user explicitly requested the testing phase for tasks 034
and 035. Added strict service tests in `tests/unit/test_time_entry_search.py` and general log
REST/gateway/SDK coverage in `tests/integration/test_time_entries_overview.py`. Extended the
stateful reader fixture with credited-user/date/issue filters, project-only entries, ordering,
pagination and own-log visibility. Existing catalog invocations now use meaningful general
time-entry filters; the shared reader error matrix includes the new REST route.

Coverage includes nullable references, malformed rows and metadata, inclusive date mapping,
combined filters, exact/descendant scope, same-filter probes, deep/broad scope rejection and
scope growth after probing. Client examples deduplicate IDs and group decimal sums by project,
user, activity and day. Both REST and SDK budget errors retain `scan_budget_exceeded` and
stop before the continuation page; the budget fixture counts the identity request as well.
SDK calls preserve positive numeric IDs and `me`, reject invalid alternatives, and retain the
old issue-read preflight. Capability evidence needs only `view_time_entries` for the new reader.

The live fixture adds an owned reporting project and a dedicated own-log role without
`view_issues`, preserving existing roles. Live tests create disposable project-only and
issue-linked logs, compare native/REST/SDK behavior, exact and descendant scopes, boundary
dates, same-day ID ordering, credited users, own/all visibility and inaccessible projects.
All disposable logs are deleted in `finally` blocks. No runtime change was needed.

| Evidence | Procedure | Actual | Status |
|---|---|---|---|
| EVID-005 | `uv run --frozen --no-sync pytest tests/e2e/test_reporting_acceptance.py --run-e2e -q` | Both reporting acceptance tests passed against owned pinned 7.0.2; native/REST/SDK behavior and cleanup matched | Passed 2026-10-06 |
| EVID-006 | `uv run --frozen --no-sync python scripts/verify-reporting-inspector.py` | Inspector 2.8.0 discovery plus six reader calls passed, including numeric/me and combined filters; temporary reader-only server stopped | Passed 2026-10-06 |
| EVID-007 | `uv run --frozen --no-sync pytest -q` | 883 offline cases passed, including all 139 new dedicated reporting cases and extended reader errors/catalog checks; one existing Pydantic deprecation warning | Passed 2026-10-06 |
| EVID-008 | Ruff lint, Ruff format check, `mypy src`, `git diff --check` | Lint passed; 244 Python files formatted; mypy passed for 120 source files; no whitespace errors | Passed 2026-10-06 |

The initial coding restrictions and pending evidence above are historical. This explicitly
authorized testing assignment supersedes them for the selected scenarios.

- Added typed general logs/query/service/port/gateway and an independently registered router.
- Registered the reader operation and native project capability evidence; retained old wiring.
- Documented date scope, credited users, project-only entries, count versus hours and safe totals.
- Preserved unrelated edits and test files. No dependencies or configuration changes.
- Static checks: EVID-002 passed. Final diff review confirmed model/query validation, native
  date/user/project mapping, existing bounded-client reuse, no issue preflight, additive reader
  authorization and capability rules, and unchanged old issue-entry behavior.
  No tests, startup, Inspector or live calls executed.
- Plan deviations: none; service date fields accept parsed dates under strict query validation.

Review follow-up (2026-10-06): static inspection found that FastAPI-MCP 0.4 copies the query
`anyOf` and then adds one scalar `type` selected from a set. For `user_id`, this excluded either
positive integers or `me` during MCP SDK validation, depending on the selected type. The
user authorized the fix. Registration now removes only the conflicting top-level type from
this property's schema before `install_read_limits` caches tool definitions; the existing
union, numeric bound, literal constraint and query metadata are preserved. REST handling is
unchanged. TOOL-035-006 explicitly retains both SDK invocation regressions and invalid-ID
cases for the separate testing assignment. Follow-up static-check results are recorded below;
no tests, schema-exercising scripts, startup, Inspector or live calls were run.

| Evidence | Procedure | Actual | Status |
|---|---|---|---|
| EVID-004 | `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .`; `uv run --frozen --no-sync mypy src`; `git diff --check` | Lint passed; 239 files formatted; mypy passed for 120 source files; no whitespace errors. Diff confirms the union fix precedes SDK caching | Passed 2026-10-06 |

## 9. Completion and handoff

- [x] Required code and read registration implemented.
- [x] Public documentation updated.
- [x] Exact target-version source and native permission evidence reviewed.
- [x] Static checks and final diff review recorded.
- [x] TOOL-035-001..007 have passing acceptance evidence.
- [x] Task/dashboard final status synchronized.

Final status: complete. Offline, owned live and Inspector acceptance passed, with static
checks and task/dashboard/coverage records synchronized. Existing staged implementation
changes were preserved; no runtime or dependency change was needed. The reporting fixtures
remain owned and reusable; disposable logs/issues were removed and the temporary server stopped.
Only the focused reporting live module ran; unrelated live writer scenarios were not rerun.
