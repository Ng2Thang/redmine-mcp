# Test cases for the complete MCP catalog

Status: authored on 2026-10-13; execution pending. This assignment adds executable cases,
not passing evidence or a percentage coverage claim. The catalog has 18 reads and 18 writes.
No pytest collection, unit/integration/E2E execution, Inspector invocation, or live mutation
was performed while authoring these cases.

## Catalog-wide scenarios

`tests/catalog_cases.py` explicitly owns a valid invocation for each of the 36 tools.
`tests/integration/test_catalog_safety.py` uses that inventory for these scenarios:

| Scenario | Scope | Expected result |
| --- | --- | --- |
| CAT-001 | Complete catalog | Case names equal both runtime allowlists; no duplicate case names; every writer has an existing individual or batch success-test owner |
| CAT-002 | All 36 tools, missing and invalid personal keys, REST and MCP | Authentication fails before resource access or mutation; existing issue, time and membership state is unchanged |
| CAT-003 | All 31 tools accepting arguments, REST and MCP | A documented invalid field is rejected without a native write or changed state |
| CAT-004 | All 18 writes, REST and MCP | Reader deployment denies the operation and excludes it from discovery |
| CAT-005 | All 18 writes, REST and MCP | Disabled operation remains unavailable even when the writer deployment is enabled |

The five parameter-free tools use authentication, populated/empty/malformed native response
tests and lifecycle checks rather than inventing unsupported invalid arguments.
The REST helper resolves each operation's public OpenAPI route, including path/query/body
placement and the membership DELETE body. Existing dedicated tests assert exact native paths
and payloads. This matrix supplements them.

## Operation traceability

All rows also use CAT-001/002 and, where applicable, CAT-003/004/005. Paths below are relative
to `tests/`. The existing `e2e/test_mcp_tool_lifecycles.py` covers every registered reader
individually and every registered write in four native lifecycles; those working-tree cases
remain unexecuted for the current implementation.

| Tool | Detailed offline scenario owners | Native lifecycle or additional acceptance owner |
| --- | --- | --- |
| `get_current_user` | `integration/test_reader_contracts.py`, `integration/test_session_isolation.py` | Catalog reader parity; `e2e/test_live_acceptance.py` |
| `list_my_project_capabilities` | `unit/test_capabilities.py`, `integration/test_reader_contracts.py`, `integration/test_allowed_all.py` | Catalog advisory scope; `e2e/test_catalog_acceptance.py` |
| `list_projects` | `integration/test_reader_contracts.py`, `integration/test_bounded_reads.py` | Catalog project discovery parity |
| `get_project` | `integration/test_reader_contracts.py` | Catalog project metadata parity |
| `list_project_versions` | `integration/test_reader_acceptance.py` | Catalog versions; `e2e/test_catalog_acceptance.py` |
| `list_project_issue_categories` | `integration/test_reader_acceptance.py` | Catalog category parity |
| `list_project_files` | `integration/test_reader_contracts.py` | Catalog populated file; file lifecycle |
| `list_project_time_entry_activities` | New `unit/test_project_time_entry_activities.py`, `integration/test_project_time_entry_activities.py` | Catalog populated choices; new creation acceptance permission cases |
| `list_project_members` | `unit/test_project_members.py`, `integration/test_project_members.py` | Catalog memberships; `e2e/test_catalog_acceptance.py` |
| `list_issues` | `integration/test_list_issues_search.py`, `test_issue_estimates.py`, `test_issue_tag_filters.py`, `test_bounded_reads.py` | Catalog issue parity; reporting/tag acceptance |
| `get_issue` | `integration/test_reader_contracts.py`, new `integration/test_issue_tag_mapping.py` | Catalog issue detail parity |
| `get_attachment` | `integration/test_reader_contracts.py`, `test_bounded_reads.py` | Catalog attachment detail; file lifecycle |
| `list_issue_time_entries` | `integration/test_reader_contracts.py` | Catalog issue logs; time lifecycle |
| `list_time_entries` | `unit/test_time_entry_search.py`, `integration/test_time_entries_overview.py` | Catalog project logs; `e2e/test_reporting_acceptance.py` |
| `list_issue_statuses` | `integration/test_reader_acceptance.py`, `test_reader_contracts.py` | Catalog populated status parity |
| `list_issue_priorities` | `integration/test_reader_acceptance.py`, `test_reader_contracts.py` | Catalog populated priority parity |
| `list_document_categories` | `integration/test_reader_contracts.py` | Catalog populated document-category parity |
| `list_trackers` | `integration/test_reader_acceptance.py`, `test_reader_contracts.py` | Catalog populated tracker parity |
| `create_time_entry` | New `unit/test_time_entry_creations.py`, `integration/test_time_entry_creations.py`; added current-writer matrix row | Time lifecycle; new `e2e/test_time_entry_create_acceptance.py` |
| `update_time_entry` | `unit/test_time_entry_updates.py`, `integration/test_time_entry_updates.py` | Time lifecycle; `e2e/test_time_entry_update_acceptance.py` |
| `delete_time_entry` | `unit/test_time_entry_deletions.py`, `integration/test_time_entry_deletions.py` | Time lifecycle; `e2e/test_time_entry_delete_acceptance.py` |
| `upload_attachment` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | File lifecycle; `e2e/test_live_acceptance.py` |
| `add_project_file` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | File lifecycle; `e2e/test_live_acceptance.py` |
| `create_project_version` | `unit/test_project_versions.py`, `integration/test_project_versions.py` | Version lifecycle; `e2e/test_catalog_acceptance.py` |
| `add_project_members` | `unit/test_project_members.py`, `test_project_members_gateway.py`, `integration/test_project_members.py` | Membership lifecycle; `e2e/test_catalog_acceptance.py` |
| `update_project_members` | Membership unit/gateway/integration suites | Membership lifecycle; `e2e/test_catalog_acceptance.py` |
| `delete_project_members` | Membership unit/gateway/integration suites | Membership lifecycle; `e2e/test_catalog_acceptance.py` |
| `update_attachment` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | File lifecycle; `e2e/test_live_acceptance.py` |
| `delete_attachment` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | File lifecycle; `e2e/test_live_acceptance.py` |
| `create_issue` | `unit/test_write_contracts.py`, `integration/test_current_tools.py`, `test_issue_null_assignment.py` | Issue lifecycle; native copy/permissions/fault acceptance |
| `update_issue` | `unit/test_write_contracts.py`, `integration/test_current_tools.py`, `test_issue_null_assignment.py` | Issue lifecycle; permissions, journals and uncertainty |
| `update_issue_note` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | Issue/journal lifecycle; private notes and native state |
| `create_issue_relation` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | Issue relation presence at both endpoints |
| `delete_issue_relation` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | Issue relation absence at both endpoints |
| `add_issue_watcher` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | Issue watcher presence |
| `remove_issue_watcher` | `unit/test_write_contracts.py`, `integration/test_current_tools.py` | Issue watcher absence |

## New detailed cases

Creation unit cases cover required fields, strict numbers/dates/IDs, null versus omission,
comment bounds, unsupported identity fields, invalid caller/service dependencies, exact issue
authorization and the `log_time` capability. Integration cases cover exact issue-derived
project query/body and caller-key forwarding, optional native defaults, minute rounding and
Redmine 6 rational hours, independent duplicate calls, different callers, inaccessible or
malformed issues, native rejection, pre-dispatch failures, dispatched ambiguity, committed
lost replies, unusable 201 receipts, wrong references and failed/mismatching read-back.
The existing writer matrix now includes creation success, reader/native permission denial,
received 5xx uncertainty and `allowed_all` at both REST and MCP boundaries.

Activity cases cover strict project IDs, the exact expansion request, populated and empty
collections, omitted permission-gated choices, malformed rows/IDs, duplicate IDs and native
errors. Issue-detail tag cases cover unavailable/null/empty/populated values, exact names,
deterministic order and malformed/duplicate names through REST and MCP.

The new opt-in creation E2E module covers two owned issues with 16 caller hours on explicit
dates, repeated identical calls, a read-only role, logging without time-view permission,
native activity visibility/rejection, and committed-write receipt faults. The existing guarded
time fixture now creates one extra owned read-only role/user and includes it in its existing
ledger-driven cleanup. No global setting, existing grant or shared issue is changed by these
new scenarios. Run the time-fixture modules sequentially because they share a private ledger.

## Execution handoff and remaining limits

The new strict creation tests require MCP to reject undeclared identity/project fields.
The user subsequently reported six failures: five MCP creation cases counted discovery GETs
as extra creation read-back, and the schema case found a missing `additionalProperties=false`.
The SDK refreshes its output schema through `list_tools` after the first successful call;
caller discovery reads authentication/capability evidence. The creation assertion now counts
only time-entry GETs after the POST, still requiring exactly one same-key, query-free GET
of the created entry and rejecting collection scans or extra entry reads.

`mcp/registration.py` now explicitly forbids extra properties for `create_time_entry`, matching
the existing strict REST request model. The schema and identity/project injection regressions
remain enabled. These corrections have not been rerun; no passing result is claimed.

Previously recorded task waivers and acceptance are historical. Adding these files does not
retroactively pass TOOL-040/041 acceptance, Inspector checks, broader native policy/default
matrices, tag overlap/private-role checks on 7.0.2, setup coexistence/recovery, CI or percentage
thresholds. Those limits remain visible in the [coverage matrix](../plans/testing-coverage.md)
and original task records. No finite matrix establishes every plugin, workflow or release.

After execution is separately authorized, use Git Bash from the repository root:

```bash
uv run --frozen pytest tests/unit tests/integration -q
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e -q
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e --run-e2e -q
```

Record failures, targeted corrections, full versus focused reruns, the selected environment
and owned cleanup independently. Do not reuse the historical passing counts as current results.
