# tool-009-list-issues-by-category: Find issues in a project category

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-009-list-issues-by-category` |
| Assigned capability | Let a client list all visible issues in a project category, including closed issues when requested. |
| Type / access / destructive effects | Extend `list_issues` / read / none |
| Status | blocked; implementation finished, testing pending |
| Dependencies | [prep-002](prep-002-offline-tests.md); [tool-008](tool-008-list-project-issue-categories.md) supplies category ID discovery, but its pending acceptance does not block this read filter's implementation |
| Related tasks | [tool-001](tool-001-list-issues-search.md) owns existing filters and defaults; [tool-008](tool-008-list-project-issue-categories.md) owns category discovery |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Filter, category output, and public documentation implemented. Ruff and mypy static checks pass; acceptance verification is pending. |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

### Client outcome and repository baseline

The client asked for every issue in category **BE** of **Demo API**. Category discovery returned
project ID `2` and category ID `1`. `list_issues(project_id=2, status_id="*")` returned a page of
20 visible issues, but the current tool has no `category_id` input and the `Issue` model omits
Redmine's `category` field. The result cannot establish which issues belong to BE. A client must
be able to use `list_project_issue_categories` to resolve the ID, then page through filtered
issues until the returned `total` is exhausted. Category names are project scoped, so filtering
uses the numeric ID rather than a name.

The current route is `GET /api/v1/issues`, operation ID `list_issues`, returning `Page[Issue]`.
The flow is `features/issues/router.py` → `service.py` → `ports.py` →
`integrations/redmine/issues.py` → `GET issues.json`; `bootstrap.py` wires the gateway and
`mcp/registration.py` already allowlists `list_issues`. The shared bearer token and Redmine
account determine visibility. Preserve the extensive unrelated staged and unstaged work visible
in the working tree. The offline baseline is complete in `prep-002`; repository instructions
prohibit automatic unit test execution without user acceptance or mention.

### Upstream evidence

| Source URL or versioned source | Date verified | Version supported | Endpoint/behavior | Permission evidence | Finding |
|---|---|---|---|---|---|
| [Redmine Issues REST guide](https://www.redmine.org/projects/redmine/wiki/Rest_Issues) | 2026-09-30 | General documentation; checked against source below | `GET /issues.json` | API returns issues visible to caller | Lists pagination and default open status; category is present in example issue output. |
| Previously inspected Redmine issue query (prior source inspection; current release review pending) | 2026-09-30 | prior sample | `category_id` filter | Available only when a project query is selected | Adds `category_id` as a project-scoped list filter. |
| Previously inspected Redmine issues controller (prior source inspection; current release review pending) | 2026-09-30 | prior sample | `index` API query | Uses existing issue query visibility | API count and rows come from the same query; no separate category lookup is needed per issue. |
| Previously inspected Redmine issue API view (prior source inspection; current release review pending) | 2026-09-30 | prior sample | Issue serialization | Existing issue visibility | Emits `category` with ID and name when assigned; omits it otherwise. |

Current public differences: the gateway drops Redmine's `category` reference during model
validation, and the route cannot forward `category_id`. The category filter should require a
project because Previously inspected Redmine only exposes it for a project query. No database access or new
MCP operation is needed. Synthetic acceptance must confirm actual `GET issues.json` behavior
because source inspection alone is not runtime verification.

### Questions and decisions

| ID | Question or assumption | Decision | Blocking? | Date |
|---|---|---|---|---|
| DEC-001 | Should `category_id` work without a project? | Require `project_id` when `category_id` is supplied; reject the ambiguous request before Redmine. | No | 2026-09-30 |
| DEC-002 | How are uncategorized issues represented? | Expose `category: null`; Redmine omits `category` for those issues. | No | 2026-09-30 |
| DEC-003 | Does “all issues” include closed statuses automatically? | Preserve the existing `status_id="open"` default; callers use `status_id="*"` and pagination for all statuses. | No | 2026-09-30 |

## 3. Requirements

### Goal and boundaries

Extend the existing read tool so a client can ask for the issues in a known project category and
see the category on each returned issue. Preserve all existing filters, defaults, pagination,
sorting, auth, and visibility. The task does not add category creation, issue writes, category
name search, or unscoped cross-project category filtering. The requesting Redmine user must have
permission to view the target project and issues.

| ID | User need and intended outcome | Required observable behavior | Prerequisites/constraints |
|---|---|---|---|
| REQ-001 | Find BE issues in Demo API. | Positive `category_id` filters the selected project's visible issues and combines with status and existing filters. | `project_id` is required with `category_id`; use ID `1` for BE in project `2` in the current synthetic data. |
| REQ-002 | Recognize and verify each issue's category. | Both list and detail issue responses expose a nullable `{id, name}` `category` reference. | Missing upstream category maps to `null`; malformed category fails safely. |
| REQ-003 | Retrieve every matching issue. | Filtered `Page[Issue]` has the matching total and existing limit/offset behavior. | Caller follows pages; `status_id="*"` includes closed issues. |
| REQ-004 | Keep current clients working. | Omitted `category_id` preserves current query, defaults, output wrapper, name, auth, and errors. | Existing route and MCP registration remain stable. |

Example: `list_issues(project_id=2, category_id=1, status_id="*", limit=100, offset=0)`
returns only visible Demo API issues whose category is BE. An empty matching set returns
`items: []` and `total: 0`. A request with `category_id=1` but no `project_id` returns 422.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| Existing or new tool | Extend `list_issues`; its purpose is already to find visible issues. |
| Stable operation ID | `list_issues` |
| Caller-facing description | List visible issues; optionally filter by category ID within a project. Use `status_id='*'` and pages for all statuses. |
| REST method and route | `GET /api/v1/issues` |
| Authentication and authorization | Caller personal `X-Redmine-API-Key`; the requesting Redmine user controls issue visibility. |
| MCP exposure | Existing explicit `list_issues` allowlist entry; preserve read-only behavior. |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty behavior | Upstream mapping |
|---|---|---|---|---|---|
| `category_id` query | Positive integer | Optional, default omitted | `>=1`; requires `project_id` | Omitted sends no category filter; empty or invalid input is 422 | `category_id` on `GET issues.json` |
| `project_id` query | Positive integer | Existing optional input | Existing validation; required when `category_id` supplied | Unchanged when category omitted | Existing `project_id` |
| All prior inputs | Existing types | Existing defaults | Existing validation | Unchanged | Existing mappings |

### Outputs and mapping

Keep `Page[Issue]` and its `items`, `total`, `limit`, and `offset`. Add
`category: Reference | None = None` to the shared `Issue` model, so both `list_issues` and
`get_issue` expose the category. For categorized issues, map Redmine's `category: {id, name}`;
for omitted or null category, return `null`. Reject malformed non-null category data through
the existing sanitized `upstream_response` 502 mapping. Do not fetch category names separately.
Preserve all other issue fields and related-context behavior.

Forward `project_id`, `category_id`, `status_id`, and other supplied filters to the existing
`GET issues.json` call, with HTTPX encoding once. Filtering is upstream before pagination;
`total` reflects matching visible issues. Preserve default `status_id=open`, `sort=id:asc`,
`limit=25`, and `offset=0`; preserve the `limit` bound of 1–100. The public success response is
HTTP 200 and the MCP adapter's normal tool result. No write semantics or external side effects.

### Errors

| Scenario | Detection layer | REST status and safe error | MCP result | Retry behavior |
|---|---|---|---|---|
| Invalid category ID or missing project | Route validation | 422 with a concise validation error | Existing MCP error envelope | Correct request |
| Missing or invalid personal Redmine API key | Existing auth | Existing 401 behavior | Existing MCP error envelope | Supply a valid personal Redmine API key |
| Hidden project or issue / insufficient Redmine permission | Gateway | Existing sanitized 403/404 behavior | Existing MCP error envelope | Correct access; do not infer hidden data |
| Upstream timeout or transport failure | Gateway | Existing sanitized 504/502 behavior | Existing MCP error envelope | Retry read when available |
| Malformed upstream page or category | Mapping | `upstream_response` 502 | Existing MCP error envelope | Investigate upstream response |

Specification exit check: public inputs, dependency rule, output mapping, defaults, and error
behavior are decided. Synthetic verification of the pinned runtime remains pending.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Verification |
|---|---|---|---|---|
| 1 | Add nullable category reference to the shared issue model. | `features/issues/models.py` | prep-002 | Offline list and detail mapping scenarios |
| 2 | Add optional category ID to route, service, Protocol, and gateway; validate its project dependency before the upstream call. | `features/issues/{router,service,ports}.py`, `integrations/redmine/issues.py` | Step 1 | Exact upstream query and 422 scenarios |
| 3 | Update caller documentation and task record; keep operation ID and allowlist unchanged. | `docs/tool-reference.md`, `CHANGELOG.md`, this task, dashboard | Steps 1–2 | Contract review |
| 4 | Hand off meaningful offline and opt-in synthetic acceptance checks. | Test assignment and Inspector | Steps 1–3 | CATISSUE-001 through CATISSUE-005 |

Dependency or configuration changes: none expected. No new package, write gate, or Redmine key.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given project 2 and BE category ID 1, when listing with `status_id="*"`, then every returned issue belongs to that category and the total counts matching visible issues. | REQ-001, REQ-003 | Pending |
| AC-002 | Given categorized and uncategorized upstream issues, when listing or getting details, then category ID/name or `null` is returned correctly. | REQ-002 | Pending |
| AC-003 | Given `category_id` without `project_id`, zero, or malformed input, when invoked, then 422 occurs without an upstream request. | REQ-001 | Pending |
| AC-004 | Given old inputs or no category filter, when invoked, then existing defaults, result wrapper, filters, auth, and error mappings remain. | REQ-004 | Pending |
| AC-005 | Given a restricted reader, when filtering, then hidden issues do not appear in items or total. | REQ-001, REQ-003 | Pending |

## 7. Test plan and execution record

| Scenario | Acceptance | Layer and setup | Expected result | Mode |
|---|---|---|---|---|
| CATISSUE-001 | AC-001, AC-004 | Offline gateway/REST with exact query capture for combined category, status, and prior filters | `category_id` and `project_id` forwarded; omission preserves old query | Offline, pending |
| CATISSUE-002 | AC-002 | Offline list and detail mapping with populated, missing, and malformed category | Reference, `null`, and sanitized 502 respectively | Offline, pending |
| CATISSUE-003 | AC-003 | REST/MCP invalid inputs with upstream spy | 422 and no resource request (identity verification may run) | Offline, pending |
| CATISSUE-004 | AC-001, AC-003, AC-004 | REST/MCP pagination, empty page, auth, 403/404, timeout, and discovery | Stable operation and envelopes; filtered total and page bounds | Offline, pending |
| CATISSUE-005 | AC-001, AC-005 | Inspector on marked synthetic Previously inspected Redmine with a category that has issues and restricted visibility fixture | Category membership, all-status page count, and permission boundary verified | Opt-in live, pending |

Execution evidence: `uv run --frozen --no-sync ruff check .` passed; `uv run --frozen --no-sync
ruff format --check .` passed (78 files); `uv run --frozen --no-sync mypy src` passed (38 source
files). These are static checks only. Repository instructions require the user's acceptance or
mention before unit tests are run. CATISSUE-001 through CATISSUE-005, startup, Inspector, and
synthetic Redmine acceptance remain pending. Later verification should record exact Git Bash
commands, results, and the synthetic environment marker.

## 8. Implementation and review record

- Changes made: Added nullable `Issue.category`, optional `category_id` through the issue route,
  service, reader Protocol, and Redmine gateway, and a 422 guard requiring `project_id` with the
  category filter. Existing `list_issues` operation ID, defaults, pagination, and registration
  remain unchanged.
- Plan deviations and reasons: None.
- Quality results: Ruff lint and formatting and mypy passed using the commands above. Automated
  tests, startup, Inspector, and live calls were not run in this coding-only stage.
- Documentation updated: Tool reference, changelog, this task, and dashboard.
- Final diff review: Scoped changes preserve existing issue filters and shared response shape;
  unrelated working-tree changes and the retired issue backlog were preserved.
- Remaining blocker: CATISSUE-001 through CATISSUE-005 need offline and synthetic acceptance
  evidence, including category membership, malformed mapping, pagination, and visibility.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] AC-001 through AC-005 have passing acceptance evidence.
- [ ] Relevant checks and authorized tests pass.
- [ ] Synthetic Redmine and Inspector verification completed.
- [x] Tool reference reflects final behavior.
- [x] Final diff reviewed and task/dashboard synchronized.

Final status: blocked; implementation finished, testing pending. Outcome: `list_issues` accepts a
project category ID and both issue operations expose nullable category references. Next action:
authorize a separate testing assignment to implement and run CATISSUE-001 through CATISSUE-005,
then complete marked synthetic Redmine and Inspector acceptance.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

CATISSUE-001 through CATISSUE-004 pass offline. CATISSUE-005 remains blocked: the fixture records no categories and the reader lacks category-list permission.

See [the dated verification ledger](../prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_issues category filter` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H1 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
