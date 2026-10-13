# TOOL-043: Delete spent time from a visible issue

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../../configuration.md#separate-writer-deployment).

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-043-delete-time-entry |
| Assigned capability | Remove one selected erroneous time entry from its visible issue |
| Type / access | Add tool / destructive write |
| Destructive effects | Permanently removes one time-entry record; changes spent-time totals and invokes native destruction hooks/webhooks |
| Status | complete |
| Dependencies | Existing issue/time-entry readers, caller identity and restricted writer; PREP-019/020/027 runtime baseline; PREP-002/016/017/018 testing baseline |
| Related tasks | [TOOL-042](tool-042-update-time-entry.md), [TOOL-041](tool-041-create-time-entry.md), [TOOL-035](tool-035-list-time-entries.md) |
| Target Redmine version | Pinned 7.0.2; owned native/Inspector acceptance recorded with limits |
| Last updated | 2026-10-08, Codex |
| Progress summary | Implementation/tests finished; 1889 full offline passes, 12 owned native/Inspector cases pass; cleanup and scoped checks pass |
| Blocker | None within the assigned evidence scope; broader policy/plugin variants remain disclosed |
| Next action | No remaining assigned acceptance work; future authorized reruns use the evidence record and owned fixtures |

## 2. Discovery and evidence

### Client outcome and repository baseline

The user cannot remove spent-time entries #919–#924 from issues #491–#496 because the current
connection offers reading/creation but no deletion. These are user-reported IDs, not verified
live state. Exact entry-to-issue pairing, credited users and permission eligibility are unknown.
Planning does not authorize deleting them. Each future call must name one verified issue/entry pair.

Existing `list_time_entries`, `list_issue_time_entries` and implemented `create_time_entry` cannot
delete records. `update_issue` is not a time-entry writer. Current WRITE_OPERATIONS has no spent-time
delete; `allowed_all` cannot expose absent code. Add one dedicated tool rather than extending a reader.

Reuse `features/time_entries/{models,write_models,ports,service}.py`, existing entry mapper,
`integrations/redmine/{client,write,responses}.py`, bootstrap and caller-key access policy.
Attachment deletion is receipt precedent, not evidence of time-entry permissions or absence.
Follow router -> service -> Protocol -> gateway and explicit route/MCP registration.

Applicable instructions: `AGENTS.md`, [CONTRIBUTING](../../../CONTRIBUTING.md),
[workflow](../../workflows/redmine-tools.md), [template](../../templates/redmine-tool-task.md),
[tool reference](../../tool-reference.md), [configuration](../../configuration.md),
[PREP-019](prep-019-write-outcome-consistency.md), [PREP-020](prep-020-current-catalog-acceptance.md)
and [PREP-027](prep-027-redmine-read-retries.md). Working tree was clean at discovery.
Preserve existing IDs/code/evidence; TOOL-037/038/039 are not reused. English documents and
Git Bash only. No tests, configuration changes, server changes or live mutations in this assignment.

### Upstream evidence

Official source in the existing `.local/upgrades/source/redmine-7.0.2.tar.gz` was read without
execution/extraction on 2026-10-08; version.rb identifies 7.0.2. Compose pins the 7.0.2 digest.
The release archive supplied controller evidence when the web fetch of that source failed.

| Source | Date verified | Version | Behavior / permission | Evidence or limitation |
|---|---|---|---|---|
| [REST TimeEntries](https://www.redmine.org/projects/redmine/wiki/Rest_TimeEntries) | 2026-10-08 | Unversioned | DELETE time entry by ID | Documentation alone does not establish full permission/status semantics |
| [Official release](https://www.redmine.org/releases/redmine-7.0.2.tar.gz), `app/controllers/timelog_controller.rb`, `find_time_entries`, `destroy` | 2026-10-08 | 7.0.2 | Checks editable_by? before destruction; failed destruction rolls back native transaction, renders validation errors | This contract sends one ID, not the native bulk mechanism |
| Same release, `app/models/time_entry.rb`, `visible?`, `editable_by?` | 2026-10-08 | 7.0.2 | Visible entry plus edit_time_entries, or credited caller plus edit_own_time_entries | Ownership is credited user, not author; no separate delete permission |
| Same release, `lib/redmine/preparation.rb`, time_tracking permissions | 2026-10-08 | 7.0.2 | Both edit permissions cover destroy | log_time alone cannot authorize deletion |
| Same release, `app/controllers/application_controller.rb`, `render_api_ok` | 2026-10-08 | 7.0.2 | Successful destroy returns 204 No Content | Failed destroy is validation rejection; plugin behavior remains native |

Differences: upstream supports bulk/project-only entries; this tool deletes one issue-linked entry
after checking its declared issue. A post-write GET 404 cannot distinguish absence from changed
visibility and must not become definitive proof of deletion after an uncertain write.

| Client outcome | Existing coverage | Access | Owner | Dependency / scope |
|---|---|---|---|---|
| Delete erroneous issue entry | Readers and creation only | Write | TOOL-043 | Existing baseline; assigned |
| Correct fields without deleting | No update | Write | TOOL-042 | Independent assigned tool |
| Clean up a list of selected entries | No bulk deletion | Multiple independent calls | TOOL-043 contract | Client orchestration only; no all-or-nothing guarantee |

### Questions and decisions

| ID | Decision | Blocking? | Resolution date |
|---|---|---|---|
| DEC-001 | Exactly one issue/entry pair; no hard-coded incident IDs or bulk route | No | 2026-10-08 |
| DEC-002 | Support own/all deletion according to native editing permissions and credited user | No | 2026-10-08 |
| DEC-003 | Native 204 proves acceptance; GET 404 reports not_found observation only | No | 2026-10-08 |
| DEC-004 | Duplicate call that finds no entry returns 404 without DELETE; no invented idempotent success | No | 2026-10-08 |
| DEC-005 | No additional approval parameter/UI flow; caller authorization and existing writer gates govern the tool | No | 2026-10-08 |

## 3. Requirements

Goal: remove one erroneous existing entry selected by the caller on a visible issue.
In scope: exact target checks, native permission integration, one DELETE and truthful receipt.
Out of scope: bulk/range/tag-driven deletion, issue deletion, project-only entries, updates,
restore/undo, automatic retries, server/settings changes and administrative cleanup endpoints.
Future bulk behavior needs another assignment. Existing reader/creation contracts remain compatible.

Required: separate opt-in writer, admitted authenticated caller, configured operation and native
visible/editable entry. Issue GET additionally requires issue visibility. Creation is not called;
TOOL-041's pending tests do not block deletion planning/implementation.

| ID | User need | Required observable behavior | Constraints |
|---|---|---|---|
| REQ-001 | Remove one selected entry | Dispatch DELETE only for the requested positive entry ID belonging to the requested issue | Permanent removal, no automatic restore |
| REQ-002 | Prevent wrong-target deletion | Validate exact entry/issue/project linkage and credited user before dispatch | Missing/mismatched/malformed preflight => no DELETE |
| REQ-003 | Preserve access boundaries | Existing writer/caller/operation gates; own/all edit alternatives based on credited user | log_time is insufficient; native authority remains final |
| REQ-004 | Know whether deletion was accepted | Return acceptance/uncertainty separately from not_found/still_present/unavailable observation | 404 observation cannot prove an uncertain DELETE committed |
| REQ-005 | Handle retries and multi-entry workflows safely | One DELETE attempt; independent receipts; absent duplicate target returns 404 | No bulk transaction or retry |
| REQ-006 | Expose a consistent public tool | REST/MCP registration/schema/errors, destructive annotations and capability reporting | Reader stays read-only |

Synthetic request example: issue_id=491, time_entry_id=919. Do not assume the remaining entries
pair sequentially with issues; discover each pairing using existing readers before future action.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| New tool / stable operation ID | `delete_time_entry` |
| Description | Permanently delete one time entry belonging to a visible issue. Requires the separate restricted writer and native edit permission. Deletes one entry per call and changes spent-time totals. Reports acceptance separately from later visibility; reconcile uncertain outcomes before retrying. |
| REST route | `DELETE /api/v1/issues/{issue_id}/time-entries/{time_entry_id}` |
| Authentication/access | Existing caller-key auth and require_write_access; configured operation or standalone allowed_all after registration |
| MCP exposure | Explicit WRITE_OPERATIONS entry; readOnlyHint=false, destructiveHint=true, idempotentHint=false, openWorldHint=true |
| Authorization | Exact caller-key entry/issue preflight; view_time_entries AND edit_time_entries, or eligible edit_own_time_entries; native checks remain final |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty | Upstream mapping |
|---|---|---|---|---|---|
| issue_id / path | Integer | Required | Positive ID; service rejects bool/coercion | No null | Guard only |
| time_entry_id / path | Integer | Required | Positive ID | No null | DELETE `time_entries/{id}.json` |

No request body, confirmation flag, query filters, ranges or arrays. MCP accepts only its declared
arguments under the existing schema/admission policy. No upstream ids list/body is sent.

### Outputs and mapping

Add `TimeEntryDeleteResult`: `outcome: accepted|uncertain`, `upstream_accepted: bool|null`,
`resource_id: positive int` (requested time_entry_id), `issue_id: positive int`,
`verification: not_found|still_present|unavailable` (default unavailable),
`observed_present: bool|null` (default null). This new deletion observation vocabulary avoids
equating invisible/missing resources with proven deletion. Do not change existing receipt models.

GET `time_entries/{id}.json` and `issues/{issue_id}.json`; validate exact IDs and entry.issue_id,
project linkage and credited user. Mismatch => 422 invalid_parameters; missing project-only issue
link is not accepted. Resolve actual entry project and use eligible ownership alternatives; issue
GET establishes issue visibility. Conditional discovery/reporting uses edit-permission alternatives,
not a definitive deletion grant. Partial/unknown role evidence follows the existing baseline.

Dispatch one `DELETE time_entries/{id}.json`, no payload/query, accepted_statuses=(204,).
Native 204 means outcome=accepted and upstream_accepted=true; preserve this if read-back fails.
Ambiguous dispatch => outcome=uncertain and upstream_accepted=null; later GET does not rewrite it.
Public HTTP 200 and structured MCP return the receipt, including for uncertainty.

Independent bounded GET of the same ID: valid same-ID response => observed_present=true and
verification=still_present; native 404 => observed_present=false and verification=not_found;
403, transport/budget failure or malformed/wrong-ID response => null/unavailable. `not_found`
means only that the caller's GET returned 404, not proof of physical absence or which actor removed
it. A 404 during preflight instead returns the normal error and dispatches zero DELETE.

```json
{"outcome":"accepted","upstream_accepted":true,"resource_id":919,"issue_id":491,"verification":"not_found","observed_present":false}
```

No pagination/ordering/expansions. Do not scan lists automatically to prove absence, bypass role
visibility with admin credentials, or infer deletion from aggregate hours alone.

### Errors

| Scenario | Detection layer | REST status / safe code | MCP / retry and reconciliation |
|---|---|---|---|
| Invalid IDs or wrong issue/project linkage | Route/service/gateway | 422 invalid_parameters | Existing envelope; no DELETE |
| Missing/invalid authentication | Auth/upstream | 401 invalid_credentials | Existing envelope |
| Writer/caller/operation denial or proven role denial | Access/capability policy | 403 permission_denied | No DELETE; allowed_all never bypasses gates |
| Forbidden/missing issue or entry before dispatch, or definitive native rejection | Preflight/writer | 403 access_denied / 404 resource_not_found | Sanitized; duplicate absent target is 404, not success |
| Native destroy validation/hook rejection | Writer | 422 invalid_parameters | Existing write-rejected message; no raw errors |
| Malformed/failed preflight | Existing GET mapping/client | Existing read errors, including 502 upstream_response / 504 upstream_timeout | No DELETE |
| Known pre-dispatch failure/pool exhaustion | Writer | 502 upstream_unavailable / 503 upstream_busy | No automatic retry |
| Dispatched timeout/transport interruption, native 5xx, unexpected 2xx | Writer | 200 uncertain receipt | May have committed; retain exact ID and reconcile |
| Other rejected native status, including rate limit | Existing writer mapping | Existing safe status/code | No new retry behavior |
| Post-dispatch GET 404 | Gateway observation | Preserve receipt; not_found/false | Does not prove commit when receipt uncertain |
| Post-dispatch GET 403/failure/malformed or entry still present | Gateway observation | Preserve receipt; unavailable or still_present | Failed verification never negates native 204 acceptance |

### Write semantics

Exact effects: permanent removal of one entry with native totals/callback effects. No native undo
contract. A later recreation has another identity and is not restoration. Duplicate invocations
preflight again; an absent entry returns 404 without dispatch. No automatic DELETE retry, rollback,
bulk transaction or idempotent caller-visible guarantee. GET retries remain PREP-027 bounded.

Timeout/5xx after dispatch is uncertain even if a later GET returns 404. Reconcile with authorized
native state/audit evidence where needed; preserve ambiguity when only caller-visible absence is
available. For six entries, client executes six verified pairs with independent receipts; earlier
accepted deletions remain accepted if a later call fails. Do not silently repeat uncertain calls.

Preflight and DELETE are not atomic: entries/permissions may change between reads and mutation.
No If-Match/lock token prevents a moved/edited entry race. Native permissions apply at dispatch;
the contract cannot guarantee issue linkage remains unchanged after preflight. State this limitation.

Future live acceptance uses task-owned disposable entries with explicit recorded IDs and native
own/all/denied roles in the marked 7.0.2 environment. Verify actual storage-visible absence via
authorized native fixture evidence, not aggregate totals or caller 404 alone, and preserve a control
entry. Creation may use a separately authorized fixture mechanism; TOOL-041 acceptance is not assumed.
Cleanup only remaining owned entries/issues; do not recreate deleted records merely to simulate undo.
Reconcile uncertain deletions and record cleanup failures. Never use #919–#924 as test fixtures.

Specification exit check: contract decision-complete; no implementation or runtime evidence claimed.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Planned verification |
|---|---|---|---|---|
| 1 | Review native permission and uncertainty baseline | Linked tasks/source | Baseline | Manual review |
| 2 | Add deletion receipt and TimeEntryDeleter Protocol | `features/time_entries/write_models.py`, `ports.py`, exports | 1 | TOOL-043-001/002 |
| 3 | Implement exact preflight, one no-body DELETE, independent observation | New `integrations/redmine/time_entry_deletions.py`, existing mapper/writer | 2 | TOOL-043-002/004/005 |
| 4 | Wire optional deleter and guarded issue-scoped DELETE route | `service.py`, `write_router.py`, `bootstrap.py`, exports | 2-3 | TOOL-043-003/006 |
| 5 | Register operation/time_entry_id intent, own/all resolver, candidate/report rules and destructive annotation | Auth policy/models/capabilities, Redmine capabilities, MCP catalog/annotations | 4 | TOOL-043-003/006 |
| 6 | Document permanent removal, allowlist/allowed_all upgrade, uncertainty and independent multi-call workflow | Tool reference, configuration, manual verification, changelog | 5 | Manual review |
| 7 | Separately assign tests/catalog fixtures and owned acceptance | `tests/unit`, `tests/integration`, selected opt-in `tests/e2e` | Coding + explicit testing authorization | TOOL-043-001..009 |

Reuse TOOL-042 registration/intent additions if already present; each operation owns its own
contract and gateway. No dependency cycle or requirement to implement update first. Shared files
must preserve the other task's edits. No dependencies/lockfile/runtime settings/server changes.

## 6. Acceptance criteria and traceability

| Criterion | Given | When | Then |
|---|---|---|---|
| AC-001 | Valid admitted caller and selected entry | Delete | One exact native DELETE, permanent owned entry removal, control preserved |
| AC-002 | Invalid/missing/wrong target or malformed preflight | Invoke | Safe error and zero DELETE |
| AC-003 | Own/all/denied permission variants and reader | Discover/invoke | Correct caller/operation/native boundary; credited-user ownership |
| AC-004 | 204/ambiguous dispatch plus readable/404/failed GET | Return receipt | Acceptance preserved; no false proof from 404; one mutation attempt |
| AC-005 | Duplicate absent entry or multiple independent calls | Invoke | 404 with no DELETE on absent target; independent receipts, no rollback/retry |
| AC-006 | REST/MCP and current catalog | Discover/invoke | Schema/errors/annotations/report consistent; existing tools compatible |

| Requirement | Criteria | Verification method | Evidence/result |
|---|---|---|---|
| REQ-001 | AC-001 | TOOL-043-002/007 | Passed; scoped evidence below |
| REQ-002 | AC-002 | TOOL-043-001/002/008 | Passed; scoped evidence below |
| REQ-003 | AC-003 | TOOL-043-003/006/008 | Passed; scoped evidence below |
| REQ-004 | AC-004 | TOOL-043-004/005/009 | Passed; scoped evidence below |
| REQ-005 | AC-004/005 | TOOL-043-005/007/009 | Passed; scoped evidence below |
| REQ-006 | AC-006 | TOOL-043-006/007 | Passed; scoped evidence below |

## 7. Test plan and execution record

### Scenario plan

Separately authorized tests reuse PREP-002/016/017/018, fake settings without .env,
pytest/asyncio, HTTPX MockTransport, explicit ASGI lifespan and MCP SDK. No test files/run now.

| Scenario | Criteria | Layer / setup and expected result | Mode |
|---|---|---|---|
| TOOL-043-001 | AC-002 | Unit/service: invalid IDs, arrays/batch/extra MCP arguments under existing policy, no mutation | Offline |
| TOOL-043-002 | AC-001/002 | Gateway: exact entry/issue/project/user preflight, correct no-body DELETE, mismatched/malformed/project-only target => zero DELETE | Offline |
| TOOL-043-003 | AC-003 | Auth: own credited user vs author, edit-own/all/log-only/denied, pinned/personal modes, conditional/unknown/proven-denied and writer operation gates | Offline |
| TOOL-043-004 | AC-004 | Adapter: no-body 204; GET404 not_found; valid present response still_present; 403/malformed/wrong-ID/timeout unavailable, receipt preserved | Offline |
| TOOL-043-005 | AC-004/005 | Transport: pool/pre-dispatch errors, dispatched timeout/5xx/unexpected 2xx, native validation; single DELETE and no retry; duplicate preflight404 | Offline |
| TOOL-043-006 | AC-003/006 | REST/MCP: path schema, errors, discovery, destructive hints, allowed_all/explicit CSV/report, existing tools unchanged | Offline |
| TOOL-043-007 | AC-001/005/006 | Owned 7.0.2 + Inspector: delete selected exact IDs, native fixture absence/control preservation, duplicate404, partial multi-call receipts, owned cleanup | Opt-in live |
| TOOL-043-008 | AC-002/003 | Owned permissions: credited own vs submitting author, other-user/all editor, no-view/no-edit/private/wrong issue; denied calls preserve entries | Opt-in live |
| TOOL-043-009 | AC-004/005 | Owned fault/concurrency setup: committed delete with lost reply; changed visibility404, accepted204 with read-back failure, entry changes after preflight; truthful receipt and no replay | Opt-in live |

Pagination N/A to deletion; bounded reconciliation uses existing readers. Empty 204 is success;
preflight404 is an error, post-write404 is limited observation. Live absence verification requires
explicitly authorized native fixture access, never adding a runtime database dependency.

### Execution evidence

| Evidence ID | Planned command/procedure | Scenarios | Actual / status |
|---|---|---|---|
| TOOL-043-EVID-001 | Scoped `uv run --frozen --no-sync ruff check`, `ruff format --check`, full-source `mypy src`, `git diff --check` | Static checks | Results recorded in section 8 |
| TOOL-043-EVID-002 | `uv run --frozen --no-sync pytest tests/unit tests/integration -q --tb=short` | 001..006 | 1889 passed; clean final full run after MCP correction; 32 unit/82 dedicated integration cases included |
| TOOL-043-EVID-003 | `uv run --frozen --no-sync pytest tests/e2e/test_time_entry_delete_acceptance.py --run-e2e -q --tb=short`; added case with `-k time_no_issue` | 007..009 | 11 passed plus 1 added permission case passed; owned native absence/control/totals and zero remaining cleanup verified |
| TOOL-043-EVID-004 | Isolated temporary writer startup and Inspector 2.8.0 tools/list + delete_time_entry on exact owned entry | 006/007 | Passed in native acceptance; server stopped and private credential config removed |

The coding stage ran only static checks, without tests, startup, Inspector or live calls.
The separately authorized testing stage below records subsequent runtime acceptance. Build is
N/A: no packaging/dependency changes. Source evidence alone is not functional acceptance. User-reported
incident entries and older 6.0.5 observations do not establish 7.0.2 deletion acceptance.

## 8. Implementation and review record

Implementation assigned on 2026-10-08. Working-tree baseline was clean, including previously
completed TOOL-042 code/tests/docs; existing test files remain unchanged.

- Added `TimeEntryDeleteResult`, `TimeEntryDeleter`, optional service dependency, strict target
  ID validation and caller-aware `WriteIntent`. Added issue-scoped writer DELETE route and wiring.
- Added `RedmineTimeEntryDeletions`: reuse exact entry/issue/project/credited-user preflight,
  one no-body native DELETE accepting only 204, and independent bounded same-ID GET observation.
  Read-back 404 reports not_found only; unavailable and still_present never rewrite receipts.
- Added explicit WRITE_OPERATIONS/typed intent registration, own/all permission alternatives,
  shared native resolver branch and destructive/non-idempotent MCP hints. Discovery/reports and
  standalone allowed_all use the existing registered operation policy. Catalog is 18 reads/18 writes.
- Updated README, tool reference, configuration, architecture, manual verification, changelog
  and dashboard. No runtime settings, dependencies, deployment or incident data changes.
- Deviations: none. Reused TOOL-042 helper and intent field as planned; no shared helper refactor.
- Review correction on 2026-10-08: a received native 204 now sets both `outcome=accepted`
  and `upstream_accepted=true`, even when the shared writer reports uncertainty after response
  cleanup fails or exceeds its deadline. Other receipt outcomes and read-back semantics are
  unchanged. Scoped gateway Ruff lint/format, full-source mypy (129 files) and diff checks passed.
  Add a regression case for `WriteReceipt("uncertain", 204)` during the separate testing stage;
  no tests were added or executed for this correction.
- Static checks passed on 2026-10-08 using installed locked tools from Git Bash:
  `uv run --frozen --no-sync ruff check` on the 13 task runtime files passed;
  `uv run --frozen --no-sync ruff format --check` reported all 13 formatted;
  `uv run --frozen --no-sync mypy src` passed for 129 source files;
  `git diff --check` passed. Ruff formatting was applied only to changed task files.
  No repository-wide Ruff pass is claimed; unrelated lint debt was not modified.
  Final diff inspection confirms no test/fixture/deployment/dependency changes.
- Coding-stage tests, fixtures, startup, Inspector and live calls were not assigned or executed;
  the later separately authorized testing stage below records their execution.
- Final source/diff review: confirms router -> service -> Protocol -> gateway, one mutation
  attempt, exact requested IDs and preservation of acceptance/uncertainty. No behavior decisions
  remain unresolved; runtime compatibility is pending tests, particularly shared catalog fixtures.
- Testing handoff: add unit/integration coverage for TOOL-043-001..006; update all-operation
  maps and SyntheticRedmine DELETE support without weakening existing cases. Implement owned
  7.0.2 deletion fixtures and TOOL-043-007..009 acceptance, isolated startup/Inspector, authorized
  native absence/control/totals checks, permission/fault/race cases and exact owned cleanup.
  Existing offline and live prerequisites are available; no new dependency installation assumed.

### Separately assigned testing stage (2026-10-08)

The user authorized test implementation and execution after review. Added 32 unit and 82
dedicated offline integration cases, exact DELETE support in the shared synthetic fixture and
four current-writer matrix cases. Added task-owned native fixture/inspection/cleanup helpers,
isolated Inspector writer factory and native deletion/permission/fault/race checks.

Initial focused execution: 305 passed, four MCP extra-argument/schema cases failed. They exposed
undeclared arguments being ignored by the tool. Fixed `delete_time_entry` registration with
`additionalProperties=false`; the four failures and two added receipt cases now pass together.
This runtime correction is within the deletion contract and leaves other operations unchanged.
Review cleanup regression coverage includes an actual HTTPX close error after receiving 204.

Owned native/Inspector execution: 11 cases pass in 272.36 seconds, plus the added no-issue-view
case passes in 20.82 seconds (11 deselected). Final full offline regression: 1889 passed in
1035.05 seconds, including all final task cases and the MCP correction. Scoped Ruff lint/format
on 21 runtime/test files, full-source mypy on 129 source files and staged/unstaged whitespace
checks pass. Exact final owned cleanup reports zero projects/entries/users/roles/activities; no
fixture ledger or Inspector credential config remains. Global settings/shared data are unchanged.
Faults are application-level injections after native commit, not TCP-loss experiments. A real
owned moved-entry race is covered; live visibility-policy changes and arbitrary plugins are not
forced. See the evidence limits; no final single 12-case native rerun is claimed.
See [testing evidence](../../testing/evidence/tool-043-testing.md) for exact commands, results,
ownership, initial defect, fault-injection limits and final cleanup evidence.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [x] Every requirement has passing acceptance evidence.
- [x] Relevant tests and repository checks pass.
- [x] Owned live state/permission verification and cleanup completed.
- [x] Public documentation reflects implemented behavior.
- [x] Implementation reviewed with no unresolved behavior decisions.
- [x] Implementation evidence and dashboard synchronized.

Final status: **complete** within the recorded offline and owned native evidence scope. Coding
removed no Redmine entry; authorized testing deleted only recorded disposable owned entries.
No further assigned work remains. Broader policy/plugin/infrastructure variants and production
readiness are separate follow-ups. No build is required by unchanged packaging/dependencies.
