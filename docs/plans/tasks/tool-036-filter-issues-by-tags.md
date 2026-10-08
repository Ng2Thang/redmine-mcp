# tool-036-filter-issues-by-tags: Filter issues by any selected tag

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-036-filter-issues-by-tags |
| Assigned capability | Filter visible issues by ANY supplied known tag, combined with existing search filters |
| Type / access / effects | Extend existing `list_issues` / read-only / none |
| Status | blocked |
| Dependencies | Existing list reader, budgets/retries; PREP-028 filter evidence satisfied (detail acceptance is not a dependency) |
| Related tasks | [prep-028](prep-028-redmineup-tags-api-readiness.md), [dashboard](../index.md) |
| Target | Existing Redmine 7.0.2 + Tags 2.2.0 Light; no server modifications |
| Last updated | 2026-10-08, Codex |
| Progress summary | Implementation finished; 82 focused offline and 3 selected port-3000 live tests passed; Inspector passed; full target acceptance pending |
| Next action | Provide existing two-real-tag overlap/private fixtures and a supported Redmine 7.0.2 target; retain partial 6.0.5 evidence |

## 2. Discovery and evidence

The user needs issues tagged backend OR urgent together with existing project/status filters.
Before implementation, `IssueSearch`, reader Protocol and gateway had no tag input. Existing router/service/
port/gateway and MCP `list_issues` are reused; no new operation or generic query proxy is needed.

Apply `AGENTS.md`, the [workflow](../../workflows/redmine-tools.md) and
[template](../../templates/redmine-tool-task.md). The initial revision used review/planning
skills; the subsequent coding assignment uses `redmine-implement-task`. Preserve staged task
docs and existing PREP-028 changes. Tests/live calls were excluded from coding; the user later
assigned TOOL-036 testing and explicitly selected port 3000. Existing PREP-015/027
budgets/retries remain owners.

[TAGS-REST-001/002](../../integrations/redmineup-tags.md) record user-supplied positive
`notification` results (489/488, total 2) and a nonexistent-name control (empty, total 0).
These establish native single-name filtering on the demonstrated server. Core index/query source
and Tags `issue_query_patch.rb:29-52` establish structured params, ANY and filtering before native
count/paging. Multi-name overlap, scopes and MCP acceptance remain unverified.

| Decision | Resolution |
|---|---|
| DEC-001 | ANY names are AND-combined with other issue filters |
| DEC-002 | Use `issue_tags`, operator `=`, repeated structured values; bounded name subset below |
| DEC-003 | Native count/paging/order; no page-local filtering or union of independent tag pages |
| DEC-004 | User requires always-available tag filtering without an environment switch; use established native support without automatic probing |
| DEC-005 | No dependency on full-tag output, tag catalogue or write tools |

## 3. Requirements

| ID | Required behavior |
|---|---|
| REQ-001 | At least one selected tag matches; overlap issues appear once |
| REQ-002 | Preserve existing filters, defaults, include semantics and project scope |
| REQ-003 | Count/order/limit/offset apply to the fully filtered native result |
| REQ-004 | Invalid tag queries fail before dispatch; literal names never become wildcard patterns |
| REQ-005 | Same caller visibility, unchanged unfiltered path and truthful output without inferred tag arrays |

Synthetic expected set: A-only, B-only and A+B match ANY(A,B), C-only does not. This is a future
acceptance scenario, not evidence already supplied by the user.

## 4. Public contract and technical specification

Operation `list_issues`, `GET /api/v1/issues`, existing Page[Issue], reader key, allowlist and
read-only annotations. Add optional `tags_any: list[str] | None` (omitted by default).
REST repeats `tags_any=backend&tags_any=urgent`; MCP supplies an array. List output does not add
tags or claim that every requested name matched a returned issue.

### Input and deployment rules

When supplied, require 1..20 unique strict string names, 1..255 characters each. These are MCP
bounds, not claimed native limits. Reject explicit null, empty array, blank names, leading/
trailing whitespace, control characters, and `%`, `_` or backslash. Native gem matching uses
SQL LIKE, so those wildcard/escape characters are outside this initial literal-name contract.
Do not silently strip/case-fold names, split commas/pipes or accept arbitrary native operators.
Case behavior follows the existing native database; no portable case-insensitivity is promised.
General escaped-name support is a future extension requiring source/database evidence.
The generated MCP input schema must describe an optional array without a null alternative;
omission is represented internally by None. Preserve presence information at the boundary
so an explicitly supplied null fails validation rather than selecting the omitted path.

Tag filtering is always available, as requested by the user. No setting, bootstrap gate or
Compose/env passthrough is required. Supplied valid names use the demonstrated existing native
`issue_tags` support; omitted tags retain ordinary query behavior. No startup/API capability
probe, nonexistent-tag guess or per-request discovery is performed. Native support remains
a prerequisite: Redmine may silently ignore unknown filters if the plugin is removed.

Omitted tags retain the exact existing short-filter upstream path. All existing validation
remains, including category/project and subproject/project rules. Valid unknown names yield an
empty match set, consistent with the user control response.

### Complete structured native query

For supplied tags, use `GET issues.json` with `set_filter=1` and repeated arrays. The Redmine
client query type must support list values: a read-only `Mapping[str, str | int | list[str]]`
for `get`, `_get_attempt` and `get_page` (or an equivalent typed transport mapping). Scalar
existing callers remain compatible; page limit/offset validation and continuation probes stay
unchanged. HTTPX must encode each list value as repeated keys, not a comma/pipe-joined string.

Keep project_id (numeric, when supplied), sort, include, limit and offset top-level. Translate
every supplied core filter to the structured branch because native `fields[]` resets filters:

| Native field | Operator | Values |
|---|---|---|
| issue_tags | `=` | Selected names, one `values[issue_tags][]` entry per name |
| status_id=open (default) | `o` | Single empty string |
| status_id=closed | `c` | Single empty string |
| status_id=* | `*` | Single empty string |
| Numeric status_id | `=` | Status ID string |
| assigned_to_id | `=` | Numeric string or `me`, if supplied |
| tracker_id | `=` | ID string, if supplied |
| parent_id | `=` | ID string, if supplied |
| category_id | `=` | ID string, if supplied |
| fixed_version_id | `=` | ID string, if supplied |
| updated_on | `>=` | Same UTC timestamp currently used for updated_since |
| subproject_id when include_subprojects=false | `!*` | Single empty string |

For each row: append its name to `fields[]`, set `operators[field]`, and send
`values[field][]` as a list. Do not duplicate these as short filter params. Project scope is
still native project context; when include_subprojects=true, retain the existing native default
rather than inventing a new subproject rule. Stable sort remains the existing chosen ID/update
sort. The central page guard may make its existing offset probe; no tag-specific fanout.

### Results and errors

Native success: JSON issue page; public HTTP 200 Page[Issue] and existing MCP serialization.
Use native `total_count`, no local union/filtering. Existing read budgets and GET retries are
the only limits/retry owner. 422 invalid input, sanitized authentication 401,
access/resource 403/404, malformed envelope 502 `upstream_response`, and transport/deadline/
scope errors retain established mappings. Received native query validation errors use the
existing sanitized upstream failure mapping; no new error constants or tags_unavailable code
are introduced by this plan. Deployment support is a prerequisite, not inferred from HTTP 200.

Write semantics: N/A, read-only. No saved query or data mutation. Specification exit: ready
for the stated name subset and verified deployment precondition; runtime acceptance pending.

## 5. Implementation plan

| Step | Ownership |
|---|---|
| 1 | Use established native support directly; no feature flag or server modification |
| 2 | Add validated tags_any field and explicit route query array; preserve omitted/null distinction |
| 3 | Thread the field through service and existing IssueReader port |
| 4 | Widen typed Redmine query transport without changing scalar callers or retry/page logic |
| 5 | Build complete structured filters only when tags are supplied |
| 6 | Update descriptions, configuration/tool docs and changelog; no new MCP registration |
| 7 | Run assigned static checks; separately assign tests/Inspector/live acceptance |

Paths: `features/issues/{queries,service,ports,router}.py`,
`integrations/redmine/{issues,client}.py`, public docs.
No runtime configuration, dependency/lockfile or Redmine deployment changes.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Expected | Scenario |
|---|---|---|---|
| AC-001 | REQ-001 | A/B/A+B overlap matches once each; unknown name empty | TOOL-036-001,005 |
| AC-002 | REQ-002 | All core filters/includes survive structured conversion | TOOL-036-002 |
| AC-003 | REQ-003 | Correct native totals/order, 2-item pages and offset probes | TOOL-036-001,003 |
| AC-004 | REQ-004 | Invalid arrays fail before query; no LIKE wildcard broadening | TOOL-036-003,004 |
| AC-005 | REQ-005 | Caller visibility and omitted-input compatibility; no inferred tags output | TOOL-036-002,005 |

## 7. Test plan and execution record

| Scenario | Separately authorized verification |
|---|---|
| TOOL-036-001 | Offline exact repeated query encoding, overlap, empty native page and totals |
| TOOL-036-002 | All status variants, assignee/me, tracker, parent, category/version, UTC date, project/subprojects, includes and unchanged omitted path |
| TOOL-036-003 | Offset probe retains arrays; native counts/malformed metadata, read budgets and HTTP/auth errors |
| TOOL-036-004 | REST/MCP parity: omitted vs null/empty, strict strings, duplicates, length/count, whitespace, controls, wildcard/escape rejection, comma/pipe preservation |
| TOOL-036-005 | Already existing authorized environment only: multi-tag overlap, scopes, private ordinary roles, positive/negative controls and Inspector; no installation/mutations |

TOOL-036-EVID-001: initial planning/source review retained, 2026-10-08.
TOOL-036-EVID-004: TAGS-REST-001/002 user observations recorded; native single-name filtering
supported, not MCP acceptance. TOOL-036-EVID-002 records coding/static results below;
At the coding handoff, TOOL-036-EVID-003 automated/runtime/Inspector acceptance was not executed;
the authorized testing phase below records subsequent results.

### Authorized testing phase (2026-10-08)

The user assigned TOOL-036 testing and corrected live target from localhost:3001 to
localhost:3000. [Testing evidence](../../testing/evidence/tool-036-tag-filter-testing.md)
supersedes the earlier unexecuted status for selected scenarios: 82 focused offline tests,
3 read-only live tests and Inspector 2.8.0 discovery/two calls passed. Scoped Ruff and mypy pass.
The selected marked container runs Redmine 6.0.5, not target 7.0.2; installed Tags version was
not independently established. Full target acceptance, real two-tag overlap and known tagged
private-role fixtures remain blocked. No live fixtures, plugins or assignments were changed.
Full offline regression: 1,584 passed; five later budget cases and two cleanup cases passed
in focused runs. Collection timing and all commands are recorded in the linked evidence.

## 8. Implementation and review record

Renumbered from the former filtering task on 2026-10-08 at the user's request, after the
complete-assignment read and discovery plans were removed. Scenario and evidence IDs now use
TOOL-036; existing results are retained, not rerun. See the [mapping](../index.md#tags-task-removal-and-renumbering-2026-10-08).

Historical planning record (the enable gate below is superseded by the user correction):
reviewed and revised with PREP-028 and TAGS-REV-001..006 on 2026-10-08. Removed false full-tag/
catalogue dependencies and speculative server API extensions. Defined scalar/array transport,
all core-filter translations, bounded name rules and an MCP-only support gate. This revision
changes task documentation only; no tag filter code, settings or tests were added. The native
user examples validate the selected upstream path, not the application implementation.

### Assigned coding stage (2026-10-08)

Implemented `tags_any` through the existing router/service/reader/gateway. A shared input type
validates strict list/string values, bounds, uniqueness, whitespace, Unicode control/format
characters and native LIKE wildcard/escape characters. Its OpenAPI/MCP schema describes an
optional array without a null alternative; the default None represents omission. The router
validates supplied values; the service omits the field during model validation when absent and
retains the existing reader call shape for unfiltered requests. No tag names are inferred in
the result schema.

Added the default-off MCP setting, bootstrap gate and Compose/env passthrough. A disabled
tag query fails before issue-query dispatch (ordinary authentication is unchanged). Structured
requests translate all core filters, retain top-level project/sort/include/page controls and
encode names as repeated arrays. The typed client now accepts read-only Mapping parameters
including list values; retry and pagination guards are unchanged, including array retention
in offset probes. No new tool registration, dependency or server code was added.

Preserved the working-tree baseline: existing PREP-028 runtime/docs and staged roadmap files.
No tests, fixtures or unrelated files were modified. Initial scoped Ruff found import wrapping
in the new query type; scoped import fixing/formatting corrected it. Final checks are recorded
in TOOL-036-EVID-002. No acceptance evidence is inferred from those static checks.

TOOL-036-EVID-002, 2026-10-08, Git Bash with installed tools:

- `uv run --frozen --no-sync ruff check` scoped to `config.py`, `bootstrap.py`,
  `features/issues/{queries,router,service,ports}.py` and
  `integrations/redmine/{issues,client}.py` under `src/redmine_mcp/`: passed.
- `uv run --frozen --no-sync ruff format --check` on the same eight files: already formatted.
- `uv run --frozen --no-sync mypy src`: passed, 124 source files.
- `git diff --check`: passed, line-ending notices only.
- Final source diff inspection: stable operation/output, unchanged default-off unfiltered
  query path, native visibility/count/paging retained, no extra tag reads or logging. The only
  deployment edits are the MCP filter flag; no Redmine service artifacts were added.

No repository-wide Ruff pass is claimed. Earlier unrelated repository-wide failures remain
outside this task. Automated/runtime acceptance was pending at the coding handoff; the later
authorized testing record above documents subsequent selected results.

Testing handoff: add/update offline cases for TOOL-036-001..004 using fake settings (no .env),
HTTPX transport fixtures and existing REST/MCP schema/invocation coverage. Cover strict inputs,
omission/null, availability without settings, structured translations, unchanged scalar clients,
offset probes and failure/budget mapping. TOOL-036-005 requires a separately authorized existing
Redmine 7.0.2 + Tags 2.2.0 Light environment with known overlap/private issues and reader keys;
verify native and Inspector behavior without installation, seeding or mutations. No tests,
startup, Inspector, live calls, build, commit or deployment were performed in this coding stage.

## 9. Completion and handoff

### User correction: always available (2026-10-08)

Removed `REDMINE_TAG_FILTERS_ENABLED`, the Settings field, bootstrap wiring, service constructor
argument/gate, env example entry and Compose passthrough. Both tag-filtered and ordinary queries
now work without an enable setting; strict name validation and native structured translation
remain unchanged. Public docs/dashboard and the current contract above reflect this decision.
The earlier gate-related planning/coding results are historical, not the active contract.

Fresh checks: scoped `uv run --frozen --no-sync ruff check` and `ruff format --check` on
`features/issues/{service,router}.py`, `config.py` and `bootstrap.py` under `src/redmine_mcp/`
passed (four files already formatted); `uv run --frozen --no-sync mypy src` passed for 124 files;
`git diff --check` passed with line-ending notices only. No tests or live calls were performed.

- [x] Public contract, upstream mapping and dependencies reviewed.
- [x] Runtime tag filtering implemented.
- [x] Scoped Ruff, mypy and diff checks pass.
- [x] TOOL-036-001..004 focused offline checks pass.
- [x] Offline regression passes; later added budget/cleanup cases pass separately.
- [x] Selected port-3000 live REST/MCP and Inspector checks pass, with version limitations.
- [x] Assigned static checks and offline automated acceptance pass.
- [ ] Required REST/MCP/ordinary-role evidence recorded.
- [x] Dashboard synchronized with planning status.

Final status: **blocked** for complete target runtime acceptance. Implementation and focused
offline testing are finished; selected live/Inspector checks pass on the user-selected Redmine
6.0.5 target. Provide an existing supported 7.0.2 environment and known two-real-tag overlap/
private-role fixtures for the remaining TOOL-036-005 cases. Full-assignment reads
and catalogue discovery are no longer assigned tasks. Assignment writes remain blocked under
TOOL-037 and were not implemented by this assignment.
