# tool-010-list-issues-by-target-version: Find issues in a target version

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-010-list-issues-by-target-version` |
| Assigned capability | Let a client list all visible issues for a selected project, tracker, and target version, with an option to exclude subprojects. |
| Type | Extend existing `list_issues` tool |
| Access | Read |
| Destructive effects | None |
| Status | blocked; implementation finished, testing pending |
| Dependencies | [prep-002](prep-002-offline-tests.md); [tool-007](tool-007-list-project-versions.md) supplies target-version ID discovery, but its pending acceptance does not block this filter implementation |
| Related tasks | [tool-001](tool-001-list-issues-search.md) owns existing filters and defaults; [tool-007](tool-007-list-project-versions.md) owns version discovery |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Target-version filtering, exact-project scoping, target-version output, and public documentation are implemented. Static checks pass; acceptance verification is pending. |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

### Client outcome and repository baseline

The client needs every Bug in target version **History Sprint 02** for the exact **History
Alpha** project. `list_project_versions(project_id=5)` resolves that version to ID `2`, and
`list_issues` already accepts `project_id`, `tracker_id`, `status_id`, pagination, and ordering.
It cannot filter by target version, does not expose an issue's target version, and currently
includes issues from subprojects when Redmine applies a project filter. Filtering returned pages
locally cannot prove complete target-version membership and produces the wrong exact-project
scope.

Extend `list_issues`; do not add another MCP operation. The current flow is
`features/issues/router.py` -> `service.py` -> `ports.py` ->
`integrations/redmine/issues.py` -> `GET issues.json`. The shared `Issue` model serves both
`list_issues` and `get_issue`. `bootstrap.py` already wires `RedmineIssues`, and
`mcp/registration.py` already allowlists `list_issues`, so neither needs a new operation.

The shared bearer token authenticates the MCP/REST caller. The configured Redmine reader account
controls project, issue, private-issue, and version visibility. `prep-002` supplies the offline
test baseline. Repository instructions require English Markdown and prohibit automatic unit-test
execution without explicit user acceptance or mention. The working tree was clean when planned,
apart from a permission warning while Git inspected `.pytest_cache`; unrelated future changes
must be preserved.

### Upstream evidence

| Source URL or versioned source | Date verified | Version supported | Endpoint/behavior | Permission required | Evidence or limitation |
|---|---|---|---|---|---|
| [Redmine Issues REST guide](https://www.redmine.org/projects/redmine/wiki/Rest_Issues) | 2026-09-30 | General guide, checked against prior sample source below | `GET /issues.json`, pagination, project/subproject behavior | Issues visible to the API account | Documents that `project_id=XXX&subproject_id=!*` excludes subprojects; the guide does not enumerate `fixed_version_id` among its abbreviated list filters. |
| Previously inspected Redmine issue query (prior source inspection; current release review pending) | 2026-09-30 | prior sample | `fixed_version_id` issue filter | `view_issues`; query is based on visible issues | Registers `fixed_version_id` as a list filter and shows it is available independently of the project-only category filter. |
| Previously inspected Redmine issue API view (prior source inspection; current release review pending) | 2026-09-30 | prior sample | Issue list/detail serialization | Existing issue visibility | Emits `fixed_version` with ID and name when assigned and omits it when absent. |
| Previously inspected Redmine issues controller (prior source inspection; current release review pending) | 2026-09-30 | prior sample | API index count and rows | Existing issue query authorization | Count and paged items come from the same visible issue query. |
| `tools/seed/history.py` and `docs/test-data.md` | 2026-09-30 | Repository synthetic fixture | Shared sprint versions and issue assignments | Marked synthetic reader | History Alpha owns six versions shared with descendants, and every history issue has a `fixed_version_id`; IDs must be read from the manifest after resets. |

Current public differences: the issue route cannot send `fixed_version_id` or exact-project
scope; the Pydantic model drops Redmine's `fixed_version` reference. The upstream API calls the
field `fixed_version`, while Redmine UI terminology calls it **Target version**. The public input
uses `fixed_version_id` to stay aligned with Redmine and the existing `list_project_versions`
IDs; its description must mention Target version.

### Requested outcome inventory

| Client outcome / tool | Existing coverage | Read/write | Version support | Task ID | Dependencies | In scope/deferred |
|---|---|---|---|---|---|---|
| Resolve History Sprint 02 to an ID | `list_project_versions` | Read | General docs; pinned-runtime acceptance pending | tool-007 | prep-002 | Existing capability |
| Filter Bug issues by project and target version | Partial `list_issues` coverage for project/tracker | Read | Previously inspected Redmine source | tool-010 | prep-002, tool-007 discovery | In scope |
| Exclude History Alpha subprojects | No bounded public input | Read | REST guide plus pinned-runtime acceptance | tool-010 | prep-002 | In scope |
| Show target version on list/detail issues | Upstream field currently dropped | Read | Previously inspected Redmine source | tool-010 | prep-002 | In scope |

### Questions and decisions

| ID | Question/assumption | Evidence or decision | Blocking? | Resolution date |
|---|---|---|---|---|
| DEC-001 | Add a new tool or extend `list_issues`? | Extend `list_issues`; project, tracker, status, ordering, and pagination already belong to this search operation. | No | 2026-09-30 |
| DEC-002 | How should clients exclude subprojects? | Add `include_subprojects: bool = true`. When false, require `project_id` and forward `subproject_id=!*`; when true or omitted, forward no subproject filter and preserve current behavior. | No | 2026-09-30 |
| DEC-003 | Must `fixed_version_id` require `project_id`? | No. Previously inspected Redmine registers the version filter for global and project queries. Clients should normally combine it with `project_id` to avoid matching a shared version across descendants. | No | 2026-09-30 |
| DEC-004 | How is an issue without a target version represented? | Return `fixed_version: null`, matching the existing category mapping convention and Redmine's omitted field. | No | 2026-09-30 |
| DEC-005 | Does “all bugs” imply closed issues? | Preserve `status_id="open"`; callers must send `status_id="*"` and exhaust pagination to retrieve open and closed matches. | No | 2026-09-30 |
| DEC-006 | What if exact History Alpha has no matching Bug in Sprint 02? | Return a successful empty page with `total: 0`; empty is a valid, meaningful result. | No | 2026-09-30 |

## 3. Requirements

### Goal and boundaries

- Intended user and outcome: an MCP client can answer “Which Bugs belong to History Sprint 02
  in the exact History Alpha project?” from Redmine's authoritative issue query.
- In scope: positive target-version ID filtering; nullable target-version output on list and
  detail; bounded exact-project scoping; composition with existing tracker/status filters,
  pagination, and sorting.
- Out of scope: version-name matching, sprint inference from dates, issue writes, version writes,
  arbitrary Redmine filter operators, and a second issue-list operation.
- Future enhancements: other fixed-version operators such as no version, any version, multiple
  version IDs, version status, or due-date filtering require a separate client outcome.
- Compatibility constraints: preserve operation ID, REST route, page shape, auth, errors,
  existing inputs/defaults, and current inclusion of subprojects when the new boolean is omitted.
- Permission/configuration prerequisites: the requesting Redmine user must be able to view the
  selected project and issues; target-version discovery uses `list_project_versions`.

| ID | User need and intended outcome | Required observable behavior | Prerequisites/constraints |
|---|---|---|---|
| REQ-001 | Find issues assigned to History Sprint 02. | A positive `fixed_version_id` filters visible issues upstream and combines with existing filters. | Version ID comes from `list_project_versions`; no name filter. |
| REQ-002 | Limit results to History Alpha itself. | `include_subprojects=false` with `project_id` excludes descendant-project issues. | False without `project_id` is rejected before upstream access. |
| REQ-003 | Verify each result's target version. | List and detail issue responses expose nullable `{id, name}` `fixed_version`. | Missing upstream field maps to `null`; malformed non-null data fails safely. |
| REQ-004 | Retrieve every matching Bug, including closed issues when requested. | The filter composes with `tracker_id`, `status_id`, `limit`, and `offset`; filtered `total` drives paging. | Caller supplies `status_id="*"` and follows pages. |
| REQ-005 | Keep existing clients working. | Omitted new inputs preserve query parameters, subproject inclusion, response wrapper, auth, and errors. | No new MCP operation or dependency. |

Realistic synthetic request:

```json
{
  "project_id": 5,
  "include_subprojects": false,
  "fixed_version_id": 2,
  "tracker_id": 1,
  "status_id": "*",
  "limit": 100,
  "offset": 0
}
```

IDs are illustrative and must be resolved from the current project, tracker, and history
manifests. A valid exact-project query may return `{"items": [], "total": 0, ...}`. Repeating
the query with `include_subprojects=true` may include visible descendant-project issues assigned
to the shared sprint.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| Existing or new tool | Extend `list_issues`; it already owns issue filtering and paging. |
| Stable operation ID | `list_issues` |
| Purpose and tool description | Find visible issues, optionally by Target version ID, and optionally restrict a selected project to that project only. Use `status_id='*'` and pagination for all statuses. |
| REST method and route | `GET /api/v1/issues` |
| Authentication and authorization | Caller personal `X-Redmine-API-Key`; the requesting Redmine user determines issue visibility. |
| MCP exposure | Existing explicit `list_issues` allowlist entry and read-only behavior; generated schema gains the two inputs and output field. |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty behavior | Upstream mapping |
|---|---|---|---|---|---|
| `fixed_version_id` query | Integer | Optional, default omitted | `>=1` | Omitted/null sends no version filter; empty or invalid is 422 | `fixed_version_id` on `GET issues.json` |
| `include_subprojects` query | Boolean | Optional, default `true` | `false` requires `project_id` | Omitted/true sends no subproject filter; invalid is 422 | false -> `subproject_id=!*`; true -> omitted |
| `project_id` query | Existing optional positive integer | Unchanged | Existing `>=1`; required only when `include_subprojects=false` | Existing behavior when omitted | Existing `project_id` |
| Existing issue inputs | Existing types/defaults | Unchanged | Existing validation | Unchanged | Existing mappings |

### Outputs and mapping

Keep `Page[Issue]` with `items`, `total`, `limit`, and `offset`. Add
`fixed_version: Reference | None = None` to `Issue`, after `category`, so both list and detail
responses expose the Target version. Map Redmine's `fixed_version: {id, name}` directly. Missing
or null maps to `null`; malformed non-null data uses the existing sanitized
`upstream_response` 502 path. Do not fetch the version separately.

Forward supplied filters to the existing `GET issues.json` call. Forward
`subproject_id="!*"` only when `include_subprojects` is false. Filtering occurs upstream before
pagination, so `total` represents matching visible issues. Preserve `status_id=open`,
`sort=id:asc`, `limit=25`, `offset=0`, and the current limit range. No snapshot guarantee exists
across pages.

Public success is REST 200 and the existing MCP tool-result envelope. Adding nullable
`fixed_version` is an additive response change. Omission of both inputs produces the exact prior
upstream query, including Redmine's current descendant-project behavior.

### Errors

| Scenario | Detection layer | REST status and safe error | MCP result | Retry/reconciliation behavior |
|---|---|---|---|---|
| Non-positive/malformed Target version ID | Route validation | 422 validation detail | Existing MCP error envelope | Correct request |
| `include_subprojects=false` without project | Route validation | 422 concise dependency error; no resource request (identity verification may run) | Existing MCP error envelope | Supply `project_id` or use true |
| Missing/invalid MCP personal Redmine API key | Existing auth | Existing 401 | Existing MCP error envelope | Supply a valid personal Redmine API key |
| Hidden project/issue or insufficient Redmine permission | Gateway | Existing sanitized 403/404 | Existing MCP error envelope | Correct access; do not infer hidden data |
| Unknown version or version not applicable to selected scope | Upstream query | Successful empty page when Redmine returns no matches; otherwise existing safe upstream mapping | Normal result or existing error envelope | Verify IDs and sharing |
| Timeout or transport failure | Gateway | Existing sanitized 504/502 | Existing MCP error envelope | Read may be retried |
| Malformed page or `fixed_version` reference | Mapping | `upstream_response` 502 | Existing MCP error envelope | Investigate upstream response |
| Other unsuccessful upstream status | Gateway | Existing `upstream_error` 502 | Existing MCP error envelope | Retry only when appropriate |

### Write semantics

N/A - read-only. Calls query Redmine and do not alter issues, versions, projects, or local state.

Specification exit check: operation ownership, input validation/defaults, exact-project mapping,
output shape, compatibility, errors, and verification obligations are resolved. Pinned-runtime
behavior remains acceptance work rather than a contract blocker.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Verification |
|---|---|---|---|---|
| 1 | Add nullable `fixed_version` reference to the shared issue model. | `src/redmine_mcp/features/issues/models.py` | prep-002 | TARGETISSUE-002 |
| 2 | Add `fixed_version_id` and `include_subprojects` to the route; reject false without project before service access. | `src/redmine_mcp/features/issues/router.py` | Step 1 | TARGETISSUE-001, TARGETISSUE-003 |
| 3 | Thread both inputs through the service and `IssueReader` Protocol without importing framework or HTTP types. | `src/redmine_mcp/features/issues/service.py`, `ports.py` | Step 2 | Ruff/mypy static checks |
| 4 | Forward the version filter and bounded `subproject_id=!*` mapping in the gateway. | `src/redmine_mcp/integrations/redmine/issues.py` | Step 3 | Exact-query capture in TARGETISSUE-001 |
| 5 | Preserve the existing operation allowlist and bootstrap wiring; review generated OpenAPI/MCP schema for new inputs/output. | `src/redmine_mcp/mcp/registration.py`, `bootstrap.py` (review; edit only if required) | Steps 1-4 | TARGETISSUE-004 |
| 6 | Update public tool documentation and changelog, then synchronize this task and dashboard. | `docs/tool-reference.md`, `CHANGELOG.md`, this task, `docs/plans/index.md` | Steps 1-5 | Contract/diff review |
| 7 | In a separate authorized testing assignment, add offline scenarios without weakening existing coverage. | `tests/` | Implementation complete | TARGETISSUE-001 through TARGETISSUE-005 |
| 8 | Run marked synthetic Redmine and Inspector acceptance without seeding/resetting solely for verification. | Inspector and existing history fixture | Tests complete | TARGETISSUE-006 |

Dependency/configuration changes: none expected. Do not change packages, `uv.lock`, credentials,
write gates, Docker configuration, or the MCP operation allowlist entry.

## 6. Acceptance criteria and traceability

| Criterion ID | Given | When | Then |
|---|---|---|---|
| AC-001 | A visible target version, project, and tracker | `list_issues` is called with their IDs and `status_id="*"` | Only matching visible issues are returned and `total` counts the filtered query |
| AC-002 | A parent project with matching issues in descendants | The same query is made with false and true subproject inclusion | False returns only exact-project issues; true preserves parent-plus-visible-descendants behavior |
| AC-003 | Issues with and without a target version | They are listed or read individually | `fixed_version` is `{id, name}` or `null` respectively |
| AC-004 | Invalid new inputs | REST or MCP invokes the tool | Validation fails safely, and the project-dependency failure makes no Redmine call |
| AC-005 | Existing callers omit both new inputs | They invoke `list_issues` or `get_issue` | Existing names, defaults, query, paging, auth, errors, and related context remain compatible |
| AC-006 | A reader cannot see an issue or project | It queries by target version | Hidden issues do not appear in `items` or `total`, and hidden resources remain safely mapped |

| Requirement | Acceptance criterion | Verification method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001 | TARGETISSUE-001, TARGETISSUE-006 | Pending | Pending |
| REQ-002 | AC-002, AC-004 | TARGETISSUE-001, TARGETISSUE-003, TARGETISSUE-006 | Pending | Pending |
| REQ-003 | AC-003 | TARGETISSUE-002 | Pending | Pending |
| REQ-004 | AC-001, AC-006 | TARGETISSUE-004, TARGETISSUE-006 | Pending | Pending |
| REQ-005 | AC-005 | TARGETISSUE-005 | Pending | Pending |

## 7. Test plan and execution record

### Scenario plan

| Scenario ID | Acceptance criteria | Layer/method | Setup and input | Expected result | Offline/live |
|---|---|---|---|---|---|
| TARGETISSUE-001 | AC-001, AC-002 | Gateway/REST exact-query capture | Combine project, tracker, all statuses, version, pagination, and each boolean value | Version ID is forwarded; false adds `subproject_id=!*`; true/omitted does not | Offline, pending |
| TARGETISSUE-002 | AC-003 | Model/gateway list and detail mapping | Populated, omitted/null, and malformed `fixed_version` | Reference, `null`, and sanitized 502 respectively | Offline, pending |
| TARGETISSUE-003 | AC-004 | REST/MCP validation with upstream spy | Zero/malformed version; false without project; malformed boolean | 422 and no resource request (identity verification may run) where route validation applies | Offline, pending |
| TARGETISSUE-004 | AC-001, AC-006 | REST/MCP behavior | Empty page, multiple pages, auth, 403/404, timeout, malformed page | Stable page/error envelopes and filtered total | Offline, pending |
| TARGETISSUE-005 | AC-005 | Regression and MCP discovery | Omit new inputs; invoke list/detail and discover tools | Old upstream query/defaults remain; one `list_issues` operation exposes additive schema | Offline, pending |
| TARGETISSUE-006 | AC-001, AC-002, AC-006 | Inspector against marked Previously inspected Redmine | Resolve current History Alpha, Sprint 02, and Bug IDs; compare exact and descendant-inclusive queries | Membership, empty-result behavior if applicable, count, target-version field, and visibility are observed | Opt-in live, pending |

Coverage selection:

- Defaults, filters, encoding, pagination, optional fields: TARGETISSUE-001, 002, 004, 005.
- Invalid inputs before upstream access: TARGETISSUE-003.
- Exact upstream query and response mapping: TARGETISSUE-001, 002.
- Successful, empty, malformed, and unsuccessful responses: TARGETISSUE-002, 004.
- Missing authentication and insufficient permissions: TARGETISSUE-004, 006.
- Existing tool names, contracts, and unrelated behavior: TARGETISSUE-005.
- MCP discovery, invocation, annotations, and error envelopes: TARGETISSUE-003 through 005.
- Write behavior: N/A - read-only.
- Startup and live permission verification: TARGETISSUE-006 using the existing marked fixture.

### Execution evidence

| Evidence ID | Command/procedure and environment | Scenario/check | Expected | Actual redacted result | Status | Date |
|---|---|---|---|---|---|---|
| EVID-001 | `uv run --frozen --no-sync ruff check .`, `uv run --frozen --no-sync ruff format --check .`, and `uv run --frozen --no-sync mypy src` from Git Bash | Static checks | Ruff and mypy pass | All passed; Ruff reported 80 files already formatted and mypy found no issues in 38 source files | Pass | 2026-09-30 |
| EVID-002 | `uv run --frozen pytest` after explicit test authorization | TARGETISSUE-001 through 005 | Offline suite passes | Not run during planning | Pending | 2026-09-30 |
| EVID-003 | Inspector 2.8.0 against the marked synthetic environment | TARGETISSUE-006 | Pinned-runtime behavior matches contract | Not run during planning | Pending | 2026-09-30 |

Verification limitations and missing prerequisites: static checks passed in the coding-only
assignment. TARGETISSUE-001 through TARGETISSUE-006, automated tests, startup, Inspector, and
live Redmine queries remain unrun. Runtime IDs can change after reset and must be resolved rather
than hard-coded. Unit tests require a separate authorized testing assignment.

## 8. Implementation and review record

- Changes made: Added nullable `Issue.fixed_version`; threaded optional `fixed_version_id` and
  `include_subprojects` through the issue route, service, reader Protocol, and Redmine gateway.
  The gateway forwards `fixed_version_id` and sends `subproject_id=!*` only when exact-project
  scoping is requested. The route rejects `include_subprojects=false` without `project_id`.
- Plan deviations and reasons: None.
- Quality and automated test results: EVID-001 passed. Automated tests were not written or run
  in this coding-only assignment.
- Startup and Inspector results: pending; no startup, Inspector, or live Redmine query was run.
- Documentation updated: tool reference, changelog, this task, and dashboard.
- Final diff review: Changes preserve the `list_issues` operation ID, default query, paging,
  authentication, and allowlist. Unrelated working-tree changes were preserved.
- Pre-existing failures versus introduced failures: The first Ruff lint run found an introduced
  overlong route line; it was corrected before EVID-001. No remaining static failures exist.
- Remaining defects/blockers: TARGETISSUE-001 through TARGETISSUE-006 need offline and synthetic
  acceptance evidence, including query mapping, malformed mapping, validation, compatibility,
  pagination, and visibility.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed.
- [x] Public documentation reflects the final behavior.
- [x] No unresolved decision changes the specified behavior.
- [x] Final diff reviewed and task record synchronized.

Final status: blocked; implementation finished, testing pending.

Outcome: `list_issues` accepts a Target version ID and optional exact-project scope, and both
issue operations expose nullable Target version references while preserving existing defaults.

Missing prerequisite or remaining work: a separate testing assignment must add and run
TARGETISSUE-001 through TARGETISSUE-005, then verify TARGETISSUE-006 through Inspector against
the marked synthetic Previously inspected Redmine environment.

Next action: authorize a separate testing assignment for TARGETISSUE-001 through
TARGETISSUE-006; do not treat static-check success as acceptance evidence.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

TARGETISSUE-001 through TARGETISSUE-005 pass offline. Inspector and same-key Redmine return zero exact-project and seven descendant-inclusive History Alpha/Sprint 02 Bug matches with matching IDs/count/version membership. Full visibility acceptance and clean live rerun remain pending.

See [the dated verification ledger](../prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_issues Target version filter` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H1 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
