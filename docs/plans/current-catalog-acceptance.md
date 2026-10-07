# Current catalog acceptance ledger

Date: 2026-10-07. Owner: [prep-020](tasks/prep-020-current-catalog-acceptance.md).
Target: owned Redmine **7.0.2**, digest pinned in `deploy/compose.test.yaml`.
Scope: 17 reads and 15 writes from `auth/policy.py`; MCP reader registration agrees with
`mcp/catalog.py`. `download_attachment` is retired and excluded. Counts are inventory checks,
not substitutes for scenario assertions. Reader deployments exclude all mutations.

Revision R020: Git base `533202519485ac1510e72e688fd40d6a695ac968`, which includes prep-019,
plus the current uncommitted prep-020 changes, inspected on 2026-10-07. Each row below uses R020 and that execution date.
The audit script stores per-file SHA-256 digests privately, so evidence does not imply a commit
exists. Preserve earlier tasks' dates and waivers; this ledger is the current reconciliation.

## Evidence definitions

| ID | Procedure and observable assertion | Result |
|---|---|---|
| O020 | Default offline `uv run --frozen --no-sync pytest -q`; includes earlier feature tests and new sentinel cases | 1086 passed, one existing Pydantic dependency warning, 335.59 seconds |
| A020 | `test_allowed_all.py` in unit/integration plus `test_allowed_all_admits_every_individual_writer` and `test_allowed_all_admits_each_membership_writer` | All 15 writers through REST/MCP; settings forms, operation ceilings, personal/pinned admission, reader/project denial and capability filtering |
| L020-B | `tests/e2e/test_live_acceptance.py`: ordinary writer lifecycle, native state, current-reader SDK invocation; private visibility, own/tracker/project-state restrictions, reader/admin gates, merged/inherited roles, scoped revocation, timeout and received-500 reconciliation | Passed in final 21-case live run; obsolete missing `project_ids` in the older catalog test corrected |
| L020-V | `test_live_versions_fields_duplicates_no_issue_read_and_denial` | Native project/name/description/date/open/unshared state, duplicate ID/state/count unchanged, manage_versions without view_issues, denied ordinary caller, SDK and capabilities; passed focused execution |
| L020-M | `test_live_membership_visibility_managed_roles_inheritance_and_assignment_effects` | Public/private visibility, zero-change mixed preflight, unmanageable role filtering, protected role retained/mismatch, native protected deletion rejected, group/inherited denial, child role propagation/removal, default/category/issue assignment effects, REST/SDK calls; passed focused execution |
| L020-H | `test_live_historical_read_variants_with_populated_owned_state` | Populated shared versions/categories, category/target-version filters, exact versus descendant scope, nonempty dated direct-hour sums, nonempty workflow/native parity, registries/project trackers, issue logs and two ordinary caller profiles; passed in final 21-case live run |
| L020-R | `tests/e2e/test_reporting_acceptance.py` | Native list/detail estimate parity; general log dates/scopes/order/own visibility, decimals and SDK numeric/me inputs; passed in final 21-case live run |
| I020 | `scripts/verify-catalog-inspector.py`, invoked inside the owned catalog test | Inspector 2.8.0 allowed_all catalog and writer schema/annotation checks; three read calls compare versions/memberships/capabilities with native state; zero Inspector mutations; focused execution passed |
| S019 | [prep-019 evidence](tasks/prep-019-write-outcome-consistency.md) plus current O020/L020-B | All writer mutation 5xx, GET-stage separation, single dispatch, no fabricated creation IDs/token, response closure, independent observations and batch stopping |

## Operation ledger

`Functional` means the named current contracts are accepted in the selected owned fixture and
offline failure matrix. It does not close every historical task or authorize production release.
`H1`..`H6` below identify broader original criteria and their exact remaining scope. All 32 rows have passing current functional evidence. Wider original criteria remain explicit
follow-ups below; no missing criterion is inferred from a suite count.

| Operation | Contract owner | Revision/date | Offline criteria | Live/Inspector criteria | Limitations / exact next action | Status |
|---|---|---|---|---|---|---|
| `get_current_user` | [tool-013](tasks/tool-013-get-current-user.md) | R020 / 2026-10-07 | USER-001..009, identity/session isolation; O020 | L020-B/H: two ordinary keys, native profile fields; merged/group/child membership | H3: preserve unexecuted account variants | Functional passed |
| `list_my_project_capabilities` | [tool-031](tasks/tool-031-list-my-project-capabilities.md) | R020 / 2026-10-07 | UNIT-002, role dedup/merge, bounded scoped inventory; A020; O020 | L020-B/V/I: native grants, scopes and session revocation | H4: broader mapping matrix is not blanket accepted | Functional passed |
| `list_projects` | [prep-004 baseline](tasks/prep-004-accept-existing-baseline.md) | R020 / 2026-10-07 | Project pages, strict metadata, caller visibility; O020 | L020-B: current SDK call and contrasting project roles | Pagination extremes use offline evidence | Functional passed |
| `get_project` | [tool-003](tasks/tool-003-get-project.md) | R020 / 2026-10-07 | PROJECT-001..003; O020 | L020-B/H: ordinary visible/restricted projects, native tracker settings | H1: original baseline combinations remain dated | Functional passed |
| `list_project_versions` | [tool-007](tasks/tool-007-list-project-versions.md) | R020 / 2026-10-07 | VERSION-002/003 metadata, scopes; O020 | L020-V/H/I: populated own/shared parent-child versions and denied private caller | H1: no hierarchy/tree/system-sharing matrix claim | Functional passed |
| `list_project_issue_categories` | [tool-008](tasks/tool-008-list-project-issue-categories.md) | R020 / 2026-10-07 | CATEGORY-002/003 mapping/errors; O020 | L020-B/H: permitted populated private project and native IDs | H1: preserve any remaining original permission alternatives | Functional passed |
| `list_project_files` | [tool-017](tasks/tool-017-list-project-files.md) | R020 / 2026-10-07 | INT-001/004, bounded safe links; O020 | L020-B: upload/file lifecycle and caller SDK listing | Historical tool matrix remains distinct, H2 | Functional passed |
| `list_project_members` | [tool-033](tasks/tool-033-project-members-management.md) | R020 / 2026-10-07 | TOOL-033-001..004/010, page/principal/role strictness; O020 | L020-M/I: public/private, groups, direct/inherited roles and two scopes | Native role metadata does not expose every management restriction | Functional passed |
| `list_issues` | [tool-001](tasks/tool-001-list-issues-search.md), extensions tool-009/010/011/034 | R020 / 2026-10-07 | Search/sort/filter; CATISSUE/TARGETISSUE/DATE/HOURS/AGG; estimate fields/budgets; O020 | L020-B/H/R: category/version filters, descendants, dates/hours, estimate parity and privacy | H1: selected populated fixtures do not prove every filter/role combination | Functional passed |
| `get_issue` | [tool-002](tasks/tool-002-get-issue-context.md), extensions tool-011/014/015 | R020 / 2026-10-07 | DETAIL-001..004, associations/write context and nullable fields; O020 | L020-B/H/R: private journals, relations/watchers/files, nonempty statuses and estimates | H2: no new changeset/wiki/document-container matrix claim | Functional passed |
| `get_attachment` | [tool-018](tasks/tool-018-get-attachment.md) | R020 / 2026-10-07 | INT-001/004 safe metadata/links, gates and container evidence; O020 | L020-B: created project attachment/native metadata and reader SDK | H2: selected project container only in current live lifecycle | Functional passed |
| `list_issue_time_entries` | [tool-012](tasks/tool-012-list-issue-time-entries.md) | R020 / 2026-10-07 | ENTRY/PAGE/AGG/AUTH/VIS/COMPAT; O020 | L020-B/H: nonempty native log IDs, credited users and issue scope | H1: per-issue all-user visibility variants remain separate from general logs | Functional passed |
| `list_time_entries` | [tool-035](tasks/tool-035-list-time-entries.md) | R020 / 2026-10-07 | TOOL-035-001..006, preview/continuation, ordering, decimal totals; O020 | TOOL-035-007 / L020-R: own/all, project-only, dates/descendants/numeric/me | Totals remain requesting-user visible; incomplete scans are not totals | Functional passed |
| `list_issue_statuses` | [tool-004](tasks/tool-004-list-issue-statuses.md) | R020 / 2026-10-07 | STATUS-001/002; O020 | L020-B/H: native registry and nonempty per-issue workflow comparison | H1: registry does not grant transitions | Functional passed |
| `list_issue_priorities` | [tool-006](tasks/tool-006-list-issue-priorities.md) | R020 / 2026-10-07 | PRIORITY-001/002; O020 | L020-B/H: native current registry IDs/names | H1: do not infer account-specific defaults | Functional passed |
| `list_document_categories` | [tool-016](tasks/tool-016-list-document-categories.md) | R020 / 2026-10-07 | UNIT/INT reference mapping/errors; O020 | L020-B: registered reader SDK call | H2: no document content/attachment workflow added | Functional passed |
| `list_trackers` | [tool-005](tasks/tool-005-list-trackers.md) | R020 / 2026-10-07 | TRACKER-001/002; O020 | L020-B/H: registry and visible-project native tracker settings | H1: role/tracker write restrictions covered separately by L020-B | Functional passed |
| `upload_attachment` | [tool-020](tasks/tool-020-upload-attachment.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003/004, A020/S019 | L020-B: opaque token/ID used once for owned file | H2: expired/unused token native variants not inferred | Functional passed |
| `add_project_file` | [tool-021](tasks/tool-021-add-project-file.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: native file state/verification and reader listing | H2: no blanket versioned file matrix closure | Functional passed |
| `create_project_version` | [tool-032](tasks/tool-032-create-project-version.md) | R020 / 2026-10-07 | TOOL-032-001..007, A020/S019 | TOOL-032-008 / L020-V/I: fields/state/duplicate/roles/no view_issues | Open/unshared creation contract only; accepted observation can be unavailable | Functional passed |
| `add_project_members` | [tool-033](tasks/tool-033-project-members-management.md) | R020 / 2026-10-07 | TOOL-033-004..006/009/010, A020/S019 | TOOL-033-011 / L020-M: ordinary manager, native filtering and child inheritance | No add-to-update fallback or rollback | Functional passed |
| `update_project_members` | [tool-033](tasks/tool-033-project-members-management.md) | R020 / 2026-10-07 | TOOL-033-004/005/007/009/010, A020/S019 | TOOL-033-011 / L020-M: protected retention/mismatch, SDK matched update and child propagation | Native management restrictions not fully exposed in public metadata | Functional passed |
| `delete_project_members` | [tool-033](tasks/tool-033-project-members-management.md) | R020 / 2026-10-07 | TOOL-033-004/005/008..010, A020/S019 | TOOL-033-011 / L020-M: inherited/group/protected rejection, positive absence and assignment effects | Existing issue assignment retained; project/category defaults clear | Functional passed |
| `update_attachment` | [tool-022](tasks/tool-022-update-attachment.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: matched receipt and changed native description | H2: selected project attachment container | Functional passed |
| `delete_attachment` | [tool-023](tasks/tool-023-delete-attachment.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: positive native/observed absence and cleanup | H2: access loss is not absence proof | Functional passed |
| `create_issue` | [tool-024](tasks/tool-024-create-issue.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: create/copy/native state; committed timeout/500 reconciliation | H2: no native every-custom-field/upload/workflow combination claim | Functional passed |
| `update_issue` | [tool-025](tasks/tool-025-update-issue.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: subject/note state, own-author/tracker restrictions, denied unchanged state | H2: workflow-specific ignored fields remain explicit observations | Functional passed |
| `update_issue_note` | [tool-026](tasks/tool-026-update-issue-note.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: owned journal edit and contrasting private visibility | H2: private/own-author permutations are not all combinations | Functional passed |
| `create_issue_relation` | [tool-027](tasks/tool-027-create-issue-relation.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: native endpoints and created relation | H2: cross-project and schedule-direction live variants remain distinct | Functional passed |
| `delete_issue_relation` | [tool-028](tasks/tool-028-delete-issue-relation.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: endpoint observation/absence after deletion | H2/H4: cross-project capability evidence is not a grant | Functional passed |
| `add_issue_watcher` | [tool-029](tasks/tool-029-add-issue-watcher.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: caller watcher membership/native state | H2: nonvisible-user policy remains native | Functional passed |
| `remove_issue_watcher` | [tool-030](tasks/tool-030-remove-issue-watcher.md) | R020 / 2026-10-07 | UNIT-003, INT-002/003, A020/S019 | L020-B: absent caller watcher/native state | H2: broader no-op/other-principal variants not inferred | Functional passed |

## Historical criterion reconciliation and shared policies

| ID / owner | Current supported criteria | Remaining limitation and exact next action |
|---|---|---|
| H1 / tool-002..012 | L020-H refreshes nonempty allowed statuses, populated versions/categories, CATISSUE-005, exact/descendant Target version scope, nonempty September direct-hour aggregation, registry/project tracker parity and native issue-log IDs. L020-B/R cover contrasting visibility and own-log scope | Do not close whole original tasks from one fixture. Any broader sharing modes, per-issue all-user accounting and permission alternatives require an explicitly selected role/fixture matrix before their original owner can be marked complete |
| H2 / tool-014..030 | O020/L020-B refresh current contracts, actual write state, reader/writer separation, private resources, author/tracker/module/status restrictions and cleanup | Historical 2026-10-02 runtime waiver remains a waiver. Document/wiki/changeset containers, cross-project relation/schedule variants and all optional write fields need criterion-specific native fixtures before blanket original-task closure |
| H3 / tool-013, prep-003 | Two ordinary caller keys, same-key native profiles, multi-role/inherited membership, POST/GET/DELETE session ownership and rotated-key isolation are supported | Locked/deleted-account and every nullable-profile variant remain original owner follow-ups; never use an administrator result as ordinary-user evidence |
| H4 / tool-031, prep-010..014 | O020 tests dedup/merged/partial role evidence and bounded filtered inventory. A020 verifies disabled/denied omission, ceiling and identity rules; L020-B verifies native session revocation/group inheritance; L020-V/I verifies target management grants | Full every-container/permission-alternative/admin/partial-metadata live matrix is not claimed. Add exact native fixtures where the original criterion requires them; retain conditional/unknown language |
| H5 / prep-015, tool-034/035 | O020 covers request/byte/deadline/admission limits, probe/continuation, changed/short metadata, truthful incomplete aggregates and decimal/dedup recipes; L020-R provides native selected scopes | Million-record previews, saturation and malformed transports are offline fault scenarios; no production load benchmark or complete cross-role global total is claimed |
| H6 / prep-019, allowed_all | S019 receipts/read stages/batch stopping; A020 parsing and all-writer REST/MCP paths; L020-V/M/I native roles and expanded catalog | Sentinel is configuration convenience, not permission. No retry, transaction, rollback, or production writer activation is implied |

These limitations block unsupported **original criterion or release claims**, not recording
the executed functional scenarios. The audit explicitly separates accepted current paths from
unexecuted broader variants. Original task histories and statuses are retained unless a named
criterion has sufficient matching evidence. No historical waiver is labeled a passing test.

## Cleanup and release boundary

The prep-020 Rails fixture helper validates environment/owner/version and uses unique prefixes.
It creates four disposable projects and five disposable roles using existing ordinary users;
it never changes existing grants or memberships. The child belongs to the disposable parent.
Cleanup validates tree ownership, deletes descendants before parents, verifies task roles have
no external memberships, and confirms zero matching projects/roles remain. Issues, versions,
categories and logs owned by those projects are removed with them. Failed preparation can still
be reconciled by the unique prefixes. Private fixture IDs/logs/config remain ignored.

Existing prep-018 lifecycle cleanup removes its separately registered issues/attachments.
Owned journal history may remain; no history rollback is promised. Inspector runs on a separate
localhost application and terminates it in `finally`. No shared reset, dependency change, commit,
production deployment, CI activation or release publication belongs to this assignment.
Final operational/recovery/user-release approval remains [prep-009](tasks/prep-009-release-acceptance.md)
and [prep-022](tasks/prep-022-operational-readiness.md).

## Final execution, 2026-10-07

- Offline: `uv run --frozen --no-sync pytest -q` — **1086 passed**, one existing dependency
  warning, 335.59 seconds. Includes 49 new allowed_all cases and the complete prep-019 baseline.
- Live: `uv run --frozen --no-sync pytest tests/e2e --run-e2e -q --tb=short` — **21 passed**,
  one existing dependency warning, 115.61 seconds. Includes four dedicated prep-020 scenarios,
  Inspector 2.8.0 and all existing selected baseline/reporting scenarios; teardown passes.
- Audit: `uv run --frozen --no-sync python scripts/audit-catalog-acceptance.py` — 17 reads,
  15 writes, unique rows, existing contract owners, registry agreement and private source digests.
- Static: Ruff lint passes; 256 Python files formatted; mypy passes for 120 runtime source files;
  final whitespace and scoped diff review pass.

Private execution logs are `.local/prep-020-offline-final.log` and
`.local/prep-020-live-accepted.log`. Unique fixture/audit directories under
`.local/testing-e2e/prep-020/` hold native fixture actions, cleanup, Inspector configuration/logs,
native read parity and source digests. The full baseline also exercises temporary owned role
revocation and restores the original grants in `finally`; no grant snapshot remains outstanding.
New prep-020 fixtures themselves never edit existing grants. No runtime defect or additional
production code change was needed. The older lifecycle test needed the membership reader's
required project scope; other initial failures were test/fixture expectations and output capture.

STAB-020-001..004 and TOOL-032-008/TOOL-033-011 have passing named evidence. AC-004 is an
explicit reconciliation result: H1..H5 preserve unexecuted broader original-owner variants.
They are not blanket accepted or erased. The current functional catalog is accepted for the
executed contracts; final release still needs criterion-specific remaining evidence and the
documentation/operational work in prep-021/022. No production-readiness claim is made.
