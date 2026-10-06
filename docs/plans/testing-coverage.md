# Application testing coverage matrix

This matrix owns current testing traceability, not historical acceptance. Task ownership is unit
prep-016, offline integration prep-017 and live E2E prep-018. All evidence below is dated
2026-10-06; final suite results are recorded in the phase tasks. Scenarios cover selected behavior,
not every possible workflow, role combination, Redmine version or infrastructure failure.

## Current tools

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
