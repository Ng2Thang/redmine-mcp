# Application testing coverage matrix

This matrix owns current testing traceability, not historical acceptance. Task ownership is unit
prep-016, offline integration prep-017 and live E2E prep-018. Historical evidence below is dated
2026-10-06; current 2026-10-07 reconciliation is recorded in the follow-up section and ledger. Scenarios cover selected behavior,
not every possible workflow, role combination, Redmine version or infrastructure failure.

## Complete catalog testcase additions (2026-10-13)

The user requested additional cases for all supported MCP tools. The
[36-tool testcase inventory](../testing/mcp-catalog-cases.md) maps each operation to executable
offline and owned native scenarios. New catalog safety cases cover missing/invalid keys for
all 36 tools, invalid values for all 31 tools accepting inputs, and both deployment and
operation gates for all 18 writes through REST/MCP. Dedicated additions cover time creation,
project activity choices and issue-detail tag mapping. The current writer matrix includes
creation; new native creation/activity cases reuse guarded owned time fixtures and cleanup.

The user has reported execution failures for these additions. No current pass count or
complete scenario acceptance is claimed. Existing historical waivers, Inspector/native
policy/plugin gaps and dated evidence remain separate.

Following six user-reported creation failures, the payload assertion now isolates time-entry
read-back from the SDK's output-schema discovery GETs, and MCP creation explicitly rejects
extra properties. Both corrections are implemented without a rerun; the testcase inventory
records the reported failures and current execution limit.

## Existing-stack E2E infrastructure

[PREP-029](tasks/prep-029-reuse-versioned-compose-e2e.md) changes setup to reuse the
6.0.1 and 7.0.2 Compose stacks. Current built-in projects are `redmine-mcp-dev-6-0-1`
and `redmine-mcp-dev-7-0-2`, with private fixture state under `.local/e2e/<project>/`;
custom profiles use `.local/e2e/<version>/`.
Its TEST-001..009 cover target selection, coexistence, fresh/repeated/failed seed,
ownership refusal, explicit selected reset, broader 6.x profile validation, opt-in gates,
and version-specific permission/state/cleanup evidence. On 2026-10-13, the complete
6.0.1 E2E command passed all 50 cases with no skips and owned cleanup on the earlier
`redmine-mcp-test-6-0-1` layout; see
[dated evidence](../testing/evidence/prep-029-redmine-6.0.1.md). This does not verify the
later self-contained development-stack refactor. Current lifecycle/profile boundaries,
6.0.1/7.0.2 setup, coexistence, reset, and browser scenarios still need their own evidence.

## Current tools

### MCP catalog lifecycle additions

`tests/e2e/test_mcp_tool_lifecycles.py` adds 22 E2E cases: 18 independently selected
reader cases and four write lifecycles that together call all 18 registered writes through
the MCP SDK. These are implemented cases, not passing execution evidence. They have not
been executed on either 6.0.1 or 7.0.2 as part of this change.

| Cases | Tools | Assertions |
| --- | --- | --- |
| Reader identity and advisory scope | `get_current_user`, `list_my_project_capabilities` | Native caller identity and membership roles; scoped project and known membership; advisory read candidate |
| Reader project discovery and metadata | `list_projects`, `get_project`, `list_project_versions`, `list_project_issue_categories`, `list_project_files`, `list_project_time_entry_activities`, `list_project_members` | Caller-native IDs and selected fields; batch membership outcome; populated reference activities; owned file present |
| Reader issues, attachments and time | `list_issues`, `get_issue`, `get_attachment`, `list_issue_time_entries`, `list_time_entries` | Native caller-visible IDs and selected fields; explicit issue/project scope; populated disposable attachment |
| Reader reference catalogs | `list_issue_statuses`, `list_issue_priorities`, `list_document_categories`, `list_trackers` | Populated catalogs with native ID/name parity |
| Issue lifecycle | `create_issue`, `update_issue`, `update_issue_note`, `create_issue_relation`, `delete_issue_relation`, `add_issue_watcher`, `remove_issue_watcher` | Acceptance/read-back receipts, native subjects and edited journal, relation presence/absence at both endpoints, watcher membership |
| Project file lifecycle | `upload_attachment`, `add_project_file`, `update_attachment`, `delete_attachment` | Upload receipt, project file membership, native/MCP metadata and byte size, native 404 and list absence after deletion |
| Time lifecycle | `create_time_entry`, `update_time_entry`, `delete_time_entry` | Credited caller and issue, rational-compatible native hours, unchanged date, both time readers, deletion receipt/native 404 and zero issue total |
| Version and membership lifecycle | `create_project_version`, `add_project_members`, `update_project_members`, `delete_project_members` | Open/unshared native version, batch receipts, native role replacement and membership absence |

Reader cases also check that a reader deployment exposes exactly `READ_OPERATIONS`.
The explicit reader case inventory must match that allowlist, so adding a reader requires
adding its parity scenario. The retired `download_attachment` operation is not registered
and is excluded from the 36-tool catalog.

The cases reuse the existing preparation and ownership guards. Issue/file cases clean up
only resources they created; catalog and time fixtures remove their disposable projects,
roles and users through existing guarded cleanup. Run sequentially: the time fixture uses
a selected-environment ledger and is not designed for parallel pytest workers.

For a separately authorized focused run from Git Bash:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e/test_mcp_tool_lifecycles.py --run-e2e
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e/test_mcp_tool_lifecycles.py --run-e2e
```

These cases supplement existing permission, visibility, retry, uncertain-write and Inspector
acceptance. Covering every registered tool does not cover every argument, role, plugin,
concurrency condition or Redmine release. Native Redmine traffic uses the selected container;
the MCP SDK connects to the application in process through the existing ASGI test transport.

### Issue time-entry deletion acceptance

The user separately assigned TOOL-043 testing on 2026-10-08. [Deletion evidence](../testing/evidence/tool-043-testing.md)
records 32 unit cases in `tests/unit/test_time_entry_deletions.py`, 82 dedicated integration
cases in `tests/integration/test_time_entry_deletions.py`, four current-writer matrix additions,
and 1889 clean full offline regression passes. Tests exposed and fixed ignored undeclared
MCP arguments; deletion now explicitly rejects them. Native acceptance in
`tests/e2e/test_time_entry_delete_acceptance.py` passed 11 cases plus one added no-issue-view
permission case, including Inspector 2.8.0. Owned storage absence/control/totals, role boundaries,
duplicate/independent-call receipts, committed faults and moved-entry race have passing evidence.
Exact cleanup reports zero projects/entries/users/roles/activities and no private task ledger or
Inspector config remains. Scoped checks pass; injection/policy/plugin limits remain disclosed.
No final single 12-case native rerun is claimed. TOOL-041 creation remains a separate task.


### Issue time-entry updates

The user assigned TOOL-042 test implementation/execution on 2026-10-08. The task is complete
within its documented evidence scope; [testing evidence](../testing/evidence/tool-042-testing.md)
records full versus targeted execution, native current settings and exact fixture cleanup.

| Operation | Unit coverage | Offline integration coverage | Owned native coverage |
|---|---|---|---|
| `update_time_entry` | `tests/unit/test_time_entry_updates.py`: 61 strict input/service/permission cases | `tests/integration/test_time_entry_updates.py`: 99 state/identity/own-all/auth/receipt/REST-MCP cases; extended current-writer matrix and all-reader argument map | `tests/e2e/test_time_entry_update_acceptance.py`: 10 native/Inspector state, role, activity, current-policy and fault/concurrency cases; task-owned setup/cleanup validates zero remaining resources |

Full offline run: 1,755 passed and one older activity-reader argument failure. Corrected
catalog rerun and seven additional late edge cases pass separately; no final clean full rerun
is claimed. Required-comments/future/closed variants under different global settings and
arbitrary plugins remain unverified. TOOL-041 creation and TOOL-043 deletion are separate tasks.

### Estimate and general spent-time acceptance

The user separately authorized testing for [tool-034](tasks/tool-034-list-issue-estimates.md)
and [tool-035](tasks/tool-035-list-time-entries.md) on 2026-10-06. The assignment adds service,
REST, gateway and MCP SDK coverage, extends the stateful reader fixture and catalog checks,
and runs dedicated live acceptance on the owned pinned Redmine 7.0.2 environment.

| Behavior | Planned offline coverage | Planned live coverage | Status |
|---|---|---|---|
| Issue-list estimates | TOOL-034-001..004: `tests/integration/test_issue_estimates.py`, additive OpenAPI coverage and existing reader contracts | TOOL-034-005: `tests/e2e/test_reporting_acceptance.py`, eight 12-hour issues and native/list/detail/SDK parity | Passed; execution records in task 034 |
| General time entries | TOOL-035-001..006: `tests/unit/test_time_entry_search.py`, `tests/integration/test_time_entries_overview.py`, extended reader errors/catalog/stateful fixture | TOOL-035-007: `tests/e2e/test_reporting_acceptance.py`, project-only entries, scopes, date boundaries, same-day ordering, own/all-log visibility | Passed; execution records in task 035 |

The new tests preserve issue-preflight coverage and exercise numeric user IDs and `me` through
the real SDK. Broad previews, scope growth, malformed metadata and exhausted request budgets
cannot be claimed as complete totals. Client examples deduplicate IDs and use decimal sums.
The live fixture adds an owned reporting project and a role with own-log visibility and no
issue-read grant; disposable issues and logs are removed in `finally` blocks.

Inspector 2.8.0 discovery and six reader calls passed with
`uv run --frozen --no-sync python scripts/verify-reporting-inspector.py`. Its reader-only server
stops after execution; credentials and detailed evidence remain ignored under `.local/testing-e2e`.
This assignment did not change the shared Redmine deployment or run unrelated live write tests.

Final execution: **883 offline cases passed**, including **139 new dedicated reporting cases**
and eight additional shared reader-error scenarios. Both focused owned live tests passed;
Inspector discovery and six calls passed. Ruff lint/format, mypy and whitespace checks passed.
One existing Pydantic deprecation warning remains in test output.

Follow-up on 2026-10-06: [tool-032](tasks/tool-032-create-project-version.md) adds 80 feature cases
plus four existing writer-matrix cases. That assignment passed 581 offline cases. Its live
acceptance remains pending; earlier prep-018 evidence does not cover this operation.

The tool-033 follow-up adds 155 cases (86 unit/service/gateway and 69 REST/MCP integration),
updates the existing reader catalog checks and extends the stateful offline fixture. The full
offline suite at that assignment passed **736 cases** with one existing Pydantic deprecation warning. Execution
results are recorded in [tool-033](tasks/tool-033-project-members-management.md). Live
TOOL-033-011 remains pending; synthetic role filtering and inheritance do not establish
Redmine 7.0.2 runtime acceptance. The shared container observed during planning was 6.0.5.

| Added operation | Unit coverage | Offline integration coverage | Live coverage |
|---|---|---|---|
| `create_project_version` | `tests/unit/test_project_versions.py`: invalid/optional fields, exact dates, invalid project IDs, permission denial and manage_versions evidence | `tests/integration/test_project_versions.py`: REST/MCP payloads and nullable schema regression, stateful duplicates, lookup failures, sanitized upstream errors, uncertainty, read-back, deployment/caller gates, discovery and capabilities; generic writer matrix in `test_current_tools.py` | TOOL-032-008 pending separately authorized isolated 7.0.2 state/permission verification |
| `list_project_members` | `tests/unit/test_project_members.py`: strict project scopes, principal/role mapping, normalization and local/shared errors | `tests/integration/test_project_members.py`: reader REST/MCP pagination, groups, inheritance, empty pages and malformed upstream data; existing reader catalog invocation | TOOL-033-011 pending owned 7.0.2 public visibility and inherited membership verification |
| `add_project_members` | Membership unit/service tests: strict IDs, batch bounds, permissions, preflight, cancellation; `test_project_members_gateway.py`: accepted response normalization and malformed receipts | Membership integration tests: exact POST payload, existing/concurrent duplicates, complete inventory fallback, budgets, writer gates, schemas, discovery and capabilities | TOOL-033-011 pending real native role restrictions and resulting state |
| `update_project_members` | Membership unit/service/gateway tests: unique targets/roles, managed permission evidence, queued deadline and interrupted dispatch | Membership integration tests: exact PUT payload, empty 200/204, protected/inherited retention, project mismatch, refreshed grants, partial execution, uncertainty and accepted read-back failures | TOOL-033-011 pending real managed roles, descendant effects and assignments |
| `delete_project_members` | Membership unit/service tests: strict targets, batch boundaries and shared dispatch controls | Membership integration tests: MCP DELETE body forwarding, exact bodyless native DELETE, group/inherited blocking, complete absence proof, retained/access-lost/incomplete inventory, allowlists and caller restrictions | TOOL-033-011 pending native inheritance/deletion restrictions, side effects and cleanup |

| Operation | Unit scenario | Offline integration scenario | Live scenario | Baseline classification |
|---|---|---|---|---|
| `get_current_user` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `get_current_user`; preserved REST scenarios | LIVE-001: reader SDK invocation `get_current_user` | Preserved baseline |
| `list_my_project_capabilities` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_my_project_capabilities`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_my_project_capabilities` | New current-tool acceptance |
| `list_projects` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_projects`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_projects` | Preserved baseline |
| `get_project` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `get_project`; preserved REST scenarios | LIVE-001: reader SDK invocation `get_project` | Preserved baseline |
| `list_project_versions` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_project_versions`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_project_versions` | Preserved baseline |
| `list_project_issue_categories` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_project_issue_categories`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_project_issue_categories` | Preserved baseline |
| `list_project_files` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_project_files`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_project_files` | New current-tool acceptance |
| `list_issues` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_issues`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_issues` | Preserved baseline |
| `get_issue` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `get_issue`; preserved REST scenarios | LIVE-001: reader SDK invocation `get_issue` | Preserved baseline |
| `get_attachment` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `get_attachment`; preserved REST scenarios | LIVE-001: reader SDK invocation `get_attachment` | New current-tool acceptance |
| `list_issue_time_entries` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_issue_time_entries`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_issue_time_entries` | Preserved baseline |
| `list_issue_statuses` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_issue_statuses`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_issue_statuses` | Preserved baseline |
| `list_issue_priorities` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_issue_priorities`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_issue_priorities` | Preserved baseline |
| `list_document_categories` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_document_categories`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_document_categories` | New current-tool acceptance |
| `list_trackers` | UNIT-001/002: shared authorization and relevant validation | INT-001: current-reader SDK invocation `list_trackers`; preserved REST scenarios | LIVE-001: reader SDK invocation `list_trackers` | Preserved baseline |
| `upload_attachment` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `upload_attachment` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `add_project_file` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `add_project_file` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `update_attachment` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `update_attachment` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `delete_attachment` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `delete_attachment` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `create_issue` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `create_issue` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `update_issue` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `update_issue` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `update_issue_note` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `update_issue_note` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `create_issue_relation` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `create_issue_relation` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `delete_issue_relation` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `delete_issue_relation` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `add_issue_watcher` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `add_issue_watcher` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |
| `remove_issue_watcher` | UNIT-003: writer validation/denial | INT-002: writer success/denial parameter `remove_issue_watcher` | LIVE-001: real write lifecycle and state | New acceptance for previously pending writer tasks |

Pure forwarding services and parameter-free registries use shared authorization and integration
mapping assertions; separate forwarding-only unit tests are intentionally unnecessary.

## Scenario ownership

| ID | Implementation and observable coverage |
|---|---|
| UNIT-001 | `test_existing_services.py`: original strict input, service ID/include/filter and identity tests; all reader operation authorization. |
| UNIT-002 | `test_offline_isolation.py`, `test_read_policy.py`, `test_capabilities.py`: settings/import construction, pagination and request/byte/time boundaries, nested/fresh budgets, role merging, partial/unknown evidence and bounded inventory. |
| UNIT-003 | `test_write_contracts.py`: create/update/note/relation/watcher models, omission/null/empty semantics, artifact bounds/paths and denial before all eleven writer ports. |
| INT-001 | Preserved five integration modules plus `test_current_tools.py`: original REST contracts, all 15 reader SDK calls, current discovery and tool annotations. |
| INT-002 | `test_current_tools.py`: all eleven writers through REST and MCP, exact method/path, single dispatch, accepted verification, reader deployment denial and project role denial. |
| INT-003 | `test_current_tools.py`: sanitized create failures, no retry, uncertain timeout and accepted write with failed read-back. |
| INT-004 | `test_bounded_reads.py`: million-record preview, same-filter probe, rejected broad continuation, retired download, safe public/subpath links, default/small admission contention, direct/proxy sharing and pre-header deadline. |
| INT-005 | `test_session_isolation.py` and preserved foundation cases: different callers/rotated keys cannot reuse POST/GET/DELETE sessions; lifecycle, concurrency, readiness, cancellation and cleanup. |
| LIVE-001 | `test_all_live_tools_and_resulting_state`: all readers, all writers, native copy, metadata and actual watcher/relation/file state, isolated cleanup. |
| LIVE-002 | Contrasting project roles, private issue/private journal visibility and unchanged rejected write state; own-author/tracker ignored-field receipts; closed/archived/module-disabled denial. |
| LIVE-004 | Multiple merged roles, group-derived inherited memberships, and role revocation within an existing MCP session. Scoped capabilities and direct calls re-evaluate grants; global unknown public-project candidates may remain discoverable. |
| LIVE-005 | A real create commits before an injected response timeout; receipt is uncertain, one dispatch occurs, exact unique subject reconciles to one resulting issue, then owned cleanup passes. |
| LIVE-003 | Separate reader deployment denies writes; admin cannot bypass writer admission; supplemental Inspector discovery/call and Edge authenticated download compare actual content. |
| GATE-001 | Explicit E2E selection without its flag rejects collection before fixtures; default selection is unit plus integration only. |

## Compatibility corrections and historical evidence

The original flat suite contained 356 test cases. Service/policy cases moved to unit; adapter,
REST and MCP cases moved to integration. Existing fixture data and SDK helpers moved to a shared
helper module. Historical `prep-004-verification.md` remains intact.

Catalog expectations now include 15 readers. Continuation fixtures provide a same-filter limit-one
metadata probe and remain within the approved matching-page ceiling. Dedicated regressions cover
oversized previews and denial rather than retaining unlimited-pagination expectations. The retired
download operation has negative tests; it is excluded from the 26 active operation count.

Existing application tasks retain their original evidence and broader pending criteria. These
new phase results establish only the named scenarios; they do not silently close every older
acceptance matrix. CI, coverage thresholds, seed-system tests and restore acceptance are deferred.

## Recorded acceptance, 2026-10-06

Unit: 102 passed. Offline integration: 395 passed. Default discovery: 497 passed.
Live E2E: 14 passed. The live opt-in rejection, static checks, Inspector catalog/call,
authenticated Edge attachment content and owned cleanup pass. The phase task records
link execution artifacts and limitations. A Pydantic deprecation warning is retained.

## Current catalog reconciliation, 2026-10-07

[prep-020](tasks/prep-020-current-catalog-acceptance.md) owns the
[32-operation current ledger](../testing/evidence/current-catalog-acceptance.md): 17 reads and 15 writes, with one
contract owner and original criteria/evidence/limitations for each operation. Earlier counts,
waivers and dated tables above are historical; the ledger supplies current functional status.

- Full offline: **1086 passed**, 335.59 seconds, including 49 new allowed_all cases. Unit
  parsing and integration cases preserve syntax/catalog rejection, empty/CSV compatibility,
  caller/deployment/project gates, all 15 writer REST/MCP payloads and filtered capabilities.
- Owned pinned 7.0.2 live suite: **21 passed**, 115.61 seconds. TOOL-032-008/TOOL-033-011 now
  pass in `tests/e2e/test_catalog_acceptance.py`: actual version/duplicate/read-permission state,
  native protected/managed/inherited memberships, child effects, assignment defaults and cleanup.
- Historical populated read variants now include nonempty workflow, shared parent/child versions,
  categories/Target version filters, exact/descendant scope, September direct-hour aggregates,
  registry/project tracker parity, native issue logs and two ordinary caller profiles.
- Inspector 2.8.0 with allowed_all passes catalog/writer schemas and three native-parity reads.
  The owned localhost application stops afterward. Existing baseline/reporting live scenarios
  and prep-019 mutation-500 reconciliation also pass in the current full run.
- Catalog audit, source digests, Ruff lint/format (256 Python files), mypy (120 runtime files)
  and scoped diff checks pass. One existing Pydantic dependency warning remains.

The new fixture helper creates disposable projects/roles without changing existing grants;
teardown verifies zero matching resources and no external role use. Baseline temporary grant
revocation is restored, and its registered resources are cleaned up. Journals may remain;
CI, coverage thresholds, restore/production readiness and blanket older permission matrices
remain outside these passing functional results. H1..H5 in the ledger list exact outstanding
original-owner scope; no dated pending row is treated as passed solely from the suite count.


## Preparation acceptance (2026-10-07)

The user separately assigned testing for prep-022 through prep-026. The final full offline
suite passed 1395 tests (724.39 seconds); the owned pinned 7.0.2 live suite passed
23 tests (246.84 seconds), including Inspector 2.8.0 and owned cleanup.
[Preparation regression testing](../testing/evidence/prep-022-026-testing.md) maps every scenario to executable
coverage and records the SDK upload-cap and native null-assignment corrections. Static
lint/format, mypy, architecture and diff checks passed. Earlier counts above are historical.
No CI, coverage threshold, recovery or production-readiness claim is added.
