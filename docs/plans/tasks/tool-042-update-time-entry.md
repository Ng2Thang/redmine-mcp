# TOOL-042: Update spent time on a visible issue

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-042-update-time-entry |
| Assigned capability | Correct the hours, date, activity or comments of one existing issue time entry |
| Type / access | Add tool / write |
| Destructive effects | Overwrites supplied entry fields, changes spent-time totals where applicable, invokes native save hooks/webhooks |
| Status | complete |
| Dependencies | Existing issue/time-entry readers, caller identity and restricted writer; PREP-019/020/027 baseline; PREP-002/016/017/018 for separately authorized testing |
| Related tasks | [TOOL-041](tool-041-create-time-entry.md), [TOOL-043](tool-043-delete-time-entry.md), [TOOL-040](tool-040-list-project-time-entry-activities.md), [TOOL-035](tool-035-list-time-entries.md) |
| Target Redmine version | Pinned 7.0.2; versioned source inspected, runtime acceptance pending |
| Last updated | 2026-10-08, Codex |
| Progress summary | 61 unit/99 dedicated integration cases covered; 10 owned native/Inspector cases pass; regression failure corrected in passing targeted rerun; scoped checks pass |
| Blocker | None for assigned contract; unrelated repository Ruff findings and unforced native policy variants remain documented limits |
| Next action | No required task work; future policy/plugin/concurrency variants require separate assignment |

## 2. Discovery and evidence

### Client outcome and repository baseline

The user reports that entries #919–#924 remain on issues #491–#496 and requests both update
and delete tools. Those IDs are incident context supplied by the user, not live observations
or fixture targets. Their exact pairings, credited users and visibility have not been verified.
Update lets a caller correct an entry without deleting and recreating it.

`list_time_entries` and `list_issue_time_entries` read entries. `create_time_entry` is implemented
in source with TOOL-041 testing pending; it cannot update an existing entry. `update_issue`
excludes time-entry changes. No update/delete time-entry operation exists in `WRITE_OPERATIONS`.
`allowed_all` only selects registered operations; changing that value cannot supply missing code.

Reuse `features/time_entries/{models,write_models,ports,service,write_router}.py`,
`integrations/redmine/{time_entries,time_entry_creations,write,responses}.py`, `bootstrap.py`,
`auth/{policy,capability_models,capabilities}.py`, `integrations/redmine/capabilities.py` and
`mcp/{catalog,annotations}.py`. The existing `TimeEntry` mapper and single-attempt writer are
baseline; services must follow router -> service -> Protocol -> gateway without HTTPX/FastAPI
framework imports or database access.

Apply `AGENTS.md`, [contributor rules](../../../CONTRIBUTING.md),
[workflow](../../workflows/redmine-tools.md), [template](../../templates/redmine-tool-task.md),
[tool reference](../../tool-reference.md), [configuration](../../configuration.md),
[PREP-019](prep-019-write-outcome-consistency.md), [PREP-020](prep-020-current-catalog-acceptance.md)
and [PREP-027](prep-027-redmine-read-retries.md). Working tree was clean at discovery.
Preserve existing code, IDs, waivers and evidence. This assignment writes English planning
documents only; it does not enable a writer, change the server or authorize checks/tests.

The user subsequently assigned TOOL-042 implementation on 2026-10-08. At coding start the
working tree contained the previous dashboard edit and untracked TOOL-042/043 plans; these
were preserved. The implementation skill authorizes static Ruff/mypy checks and diff inspection,
while excluding test changes/execution, startup, Inspector and live calls. No test waiver from
another task is applied to TOOL-042. Git Bash development prerequisites passed without reading
credentials or installing dependencies.

### Upstream evidence

The official release archive already present at `.local/upgrades/source/redmine-7.0.2.tar.gz`
was read without extraction/execution on 2026-10-08. `lib/redmine/version.rb` identifies 7.0.2;
`deploy/compose.test.yaml` pins that version and image digest. Web source and release inspection
are static evidence, not runtime acceptance. Cached GitHub controller fetch failed; the local
official release supplied its source evidence.

| Source | Date verified | Version | Behavior / permission | Evidence or limitation |
|---|---|---|---|---|
| [REST TimeEntries](https://www.redmine.org/projects/redmine/wiki/Rest_TimeEntries) | 2026-10-08 | Unversioned | PUT time entry, 204 success / 422 validation | Overview; pinned model overrides obsolete comment length |
| [Official release](https://www.redmine.org/releases/redmine-7.0.2.tar.gz), `app/controllers/timelog_controller.rb`, `find_time_entry`, `check_editability`, `update` | 2026-10-08 | 7.0.2 | Requires visible/editable entry; applies safe supplied attributes and native save hooks | No public optimistic concurrency guarantee |
| Same release, `app/models/time_entry.rb`, `visible?`, `editable_by?`, validations | 2026-10-08 | 7.0.2 | `view_time_entries` plus `edit_time_entries`, or credited caller plus `edit_own_time_entries`; comments max 1024 | Author/submitting user is not the ownership test; settings/plugins can reject updates |
| Same release, `lib/redmine/preparation.rb`, time_tracking permissions | 2026-10-08 | 7.0.2 | Both edit permissions cover update and destroy | No separate native delete permission; log permission alone is insufficient |
| Same release, `app/controllers/application_controller.rb`, `render_api_ok`; `app/views/timelog/show.api.rsb` | 2026-10-08 | 7.0.2 | Successful update is 204 without body; GET provides existing entry shape | Hours getter rounds to minutes, API rounds to two decimals |

Native API can change project/issue/user/custom fields. This issue-scoped MCP contract deliberately
exposes only hours/date/activity/comments. Native permission/settings validation remains final.

| Client outcome | Existing coverage | Access | Owner | Dependency / scope |
|---|---|---|---|---|
| Correct an existing issue entry | Readers and creation only | Write | TOOL-042 | Existing read/write baseline; assigned |
| Remove an erroneous issue entry | No deletion | Write | TOOL-043 | Independent task; assigned |
| Discover activity names | Implemented TOOL-040, testing waived | Read | Existing TOOL-040 | Optional client selection, not a mutation prerequisite |

### Questions and decisions

| ID | Decision | Blocking? | Resolution date |
|---|---|---|---|
| DEC-001 | One issue-bound entry per call; require issue_id and time_entry_id; no bulk or reassignment | No | 2026-10-08 |
| DEC-002 | Permit own or other credited users' entries according to native editability, without changing user | No | 2026-10-08 |
| DEC-003 | Require at least one supplied mutable field; reject explicit null; comments="" clears comments | No | 2026-10-08 |
| DEC-004 | Positive hours align with creation; native zero-hour policy is not exposed in this first contract | No | 2026-10-08 |
| DEC-005 | One PUT attempt, independent receipt/read-back, no automatic retry or locking promise | No | 2026-10-08 |

## 3. Requirements

Goal: authenticated callers correct exactly one existing time entry on a selected visible issue.
In scope: partial updates and truthful read-back. Out of scope: entry creation/deletion, moves,
user/author changes, project-only entries, custom fields, bulk writes, server/settings changes.
Future enhancements require separate assignments. Existing readers/creation contracts stay stable.

Prerequisites: separate opt-in writer, caller admission in pinned/personal mode, enabled operation,
visible issue and time entry, native time-tracking/editability checks. TOOL-041's pending creation
acceptance is not a dependency: updating an existing entry does not call the creation tool.

| ID | User need | Required observable behavior | Constraints |
|---|---|---|---|
| REQ-001 | Correct one entry | Apply only supplied fields on the selected entry; omissions remain untouched by the payload | Positive entry/issue IDs, at least one mutable field |
| REQ-002 | Avoid wrong-target edits | Read exact entry and issue; prove entry.issue_id equals issue_id and projects agree before PUT | Reject mismatch; no broad list scan |
| REQ-003 | Restrict writes | Enforce writer/caller/operation gates and native own/all edit permissions | Ownership uses credited user; role evidence is advisory |
| REQ-004 | Know what happened | Separate accepted/uncertain write from matched/mismatch/unavailable independent observation | Read-back failure preserves receipt |
| REQ-005 | Avoid unsafe replay | One PUT per invocation; disclose concurrent overwrite and unknown commit outcome | No retries, rollback or atomicity promise |
| REQ-006 | Use REST or MCP consistently | Stable schema/operation, explicit registration, discovery/report integration, existing tool compatibility | Reader stays read-only |

Synthetic example: `issue_id=491`, `time_entry_id=919`, `hours=7.5`, `comments="Corrected hours"`.
This is a documentation example only. The same entry under issue_id=496 must fail before PUT.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| New tool / stable operation ID | `update_time_entry` |
| Description | Update supplied hours, date, activity or comments on one time entry belonging to a visible issue. Requires the separate restricted writer and native edit permission. Reports acceptance separately from read-back; reconcile uncertainty before retrying. |
| REST route | `PUT /api/v1/issues/{issue_id}/time-entries/{time_entry_id}` |
| Authentication | Existing caller-key authentication and `require_write_access`; operation configured explicitly or via standalone allowed_all after registration |
| MCP exposure | Explicit WRITE_OPERATIONS registration; readOnlyHint=false, destructiveHint=true, idempotentHint=false, openWorldHint=true |
| Authorization | Resolve actual entry project/user via caller-key GET; own alternative only when entry.user.id == caller_id; native visibility/editability remains final |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty | Upstream mapping |
|---|---|---|---|---|---|
| issue_id / path | Integer | Required | Positive ID; service rejects bool/coercion | No null | Guard only, not mutable payload |
| time_entry_id / path | Integer | Required | Positive ID | No null | `time_entries/{id}.json` |
| hours / body | JSON number | Optional | Existing strict finite IssueHours, >0; reject strings/bool | Omitted unchanged; null rejected | `time_entry.hours` |
| spent_on / body | Date string | Optional | Existing IssueDate, YYYY-MM-DD; no datetime | Omitted unchanged; null rejected | `time_entry.spent_on` |
| activity_id / body | Integer | Optional | Strict positive ID; native project activity validation | Omitted unchanged, no default reset; null rejected | `time_entry.activity_id` |
| comments / body | String | Optional | Strict string, max 1024 | Omitted unchanged; null rejected; empty clears subject to native required-comments validation | `time_entry.comments` |

`TimeEntryUpdateRequest` forbids extra properties; reject an empty body. Send only fields in
model_fields_set/exclude_unset. Exclude issue_id/project_id/user_id/author_id/custom_fields.
Reject arrays/batch inputs. REST path parsing and MCP integer schema must match existing ID policy.

### Outputs and mapping

Add `TimeEntryUpdateResult`: `outcome: accepted|uncertain`, `upstream_accepted: bool|null`,
`resource_id: positive int` (the requested time_entry_id), `issue_id: positive int`,
`verification: matched|mismatch|unavailable`, `field_verification: map[field, verification]`,
`observed_time_entry: TimeEntry|null`. Default observation null, verification unavailable;
initialize expected-field observations as unavailable. Reuse existing `TimeEntry` output shape.

Gateway GETs `time_entries/{id}.json` and `issues/{issue_id}.json`; validate exact response IDs,
issue linkage, project linkage and credited user before any PUT. Proven wrong linkage uses
422 invalid_parameters. Do not accept a missing/malformed entry user/issue/project as a match.
Permission resolver uses entry user ownership with `view_time_entries` AND
(`edit_time_entries` OR eligible `edit_own_time_entries`) in the actual project.
Issue visibility is established by the issue GET. Project discovery/reporting may expose
conditional candidates using the edit-permission alternatives; never report an effective grant.

One `PUT time_entries/{id}.json` with `{"time_entry": {"hours": 7.5}}`; expect exactly
204 No Content via existing RedmineWriter. Public HTTP 200 returns the receipt; structured MCP
returns the same result. Optional bounded GET of the same entry independently verifies submitted
fields and preflight issue/project/user identities. Normalize expected hours using TOOL-041's
existing native rounding helper. All expected fields matched => matched; any mismatch => mismatch;
otherwise unavailable. Omitted mutable fields are not included in the update payload or compared
as asserted changes. Concurrent native changes to them cannot be attributed to this call.

Example public receipt:

```json
{"outcome":"accepted","upstream_accepted":true,"resource_id":919,"issue_id":491,"verification":"unavailable","field_verification":{"hours":"unavailable","issue_id":"unavailable","project_id":"unavailable","user_id":"unavailable"},"observed_time_entry":null}
```

No pagination, ordering or expansions; no new public detail-reader tool is needed for preflight.
Existing list readers support bounded manual reconciliation. No existing result models change.

### Errors

| Scenario | Detection layer | REST status / safe code | MCP / retry and reconciliation |
|---|---|---|---|
| Invalid/null/empty/unknown input or issue-entry mismatch | Route/service/gateway | 422 invalid_parameters | Existing error envelope; no PUT |
| Missing/invalid credentials | Authentication/upstream | 401 invalid_credentials | Existing envelope; no automatic write retry |
| Writer/caller/operation denied or proven role denial | Access/capability policy | 403 permission_denied | No PUT; allowed_all does not bypass |
| Native forbidden or missing issue/entry | Preflight or mutation | 403 access_denied / 404 resource_not_found | Sanitized; no hidden state disclosure |
| Native validation rejection | Writer | 422 invalid_parameters | Existing safe write-rejected message; no raw body |
| Malformed/failed preflight | Existing GET mapping/client | Existing read errors, including 502 upstream_response / 504 upstream_timeout | No PUT |
| Known pre-dispatch failure/pool exhaustion | Writer | 502 upstream_unavailable / 503 upstream_busy | No automatic retry |
| Dispatched timeout/transport failure, native 5xx, unexpected 2xx | Writer | 200 uncertain receipt | May have committed; retain known entry ID |
| Other rejected native statuses, including rate limit | Existing writer status mapping | Existing safe status/code | No new retry policy |
| Read-back fails or returns malformed/mismatching state | Gateway | Preserve 200 receipt; unavailable or mismatch | Never turn an accepted PUT into rejection |

### Write semantics

Exact effects: overwrite supplied fields on one existing entry, native totals/hooks/webhooks.
Permission is editing, not merely log_time; moving or recrediting entries is excluded.
Each invocation sends at most one PUT. Repeating equal values may still run hooks; no idempotency
promise, write retry, deduplication or rollback. GET retries retain PREP-027 budgets only.
After uncertainty, reconcile the exact ID through bounded issue-filtered readers; absence cannot
prove non-commit. Failed read-back preserves accepted/uncertain status independently.
No locking/If-Match/version token is promised. Permissions, entry linkage or other fields may
change after preflight; native checks and observation handle this without a transactional guard.

Later live tests require explicitly authorized disposable issues/entries and own/all/denied role
fixtures in the marked 7.0.2 environment. Record original state and owned IDs; verify native
entry fields, unrelated-entry preservation and aggregates where caller visibility is complete.
Cleanup only owned resources with separately authorized native permissions/fixture mechanisms.
Do not restore or edit incident entries #919–#924 as test cleanup; webhook effects are irreversible.

Specification exit check: public behavior resolved; implementation and runtime evidence pending.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Planned verification |
|---|---|---|---|---|
| 1 | Review existing writer/reader receipt and ownership contracts | Linked baseline tasks and source | Baseline | Manual review |
| 2 | Add strict update request/result and TimeEntryUpdater Protocol | `features/time_entries/write_models.py`, `ports.py`, exports | 1 | TOOL-042-001/002 |
| 3 | Add exact entry/issue preflight, one PUT and independent read-back | New `integrations/redmine/time_entry_updates.py`; reuse mapper/writer/rounding | 2 | TOOL-042-002/004/005 |
| 4 | Wire optional updater into service/bootstrap and guarded issue-scoped route | `service.py`, `write_router.py`, `bootstrap.py`, exports | 2-3 | TOOL-042-003/006 |
| 5 | Register operation and time_entry_id intent; entry-derived own/all clauses, discovery/reporting, destructive annotation | `auth/policy.py`, `capability_models.py`, `capabilities.py`, Redmine capabilities, MCP catalog/annotations | 4 | TOOL-042-003/006 |
| 6 | Document contract, explicit allowlist/allowed_all upgrade behavior and reconciliation | Tool reference, configuration, manual verification, changelog | 5 | Manual review |
| 7 | Separately assign tests/catalog fixtures and owned native acceptance | `tests/unit`, `tests/integration`, opt-in `tests/e2e` | Coding and explicit test authorization | TOOL-042-001..009 |

No dependency, lockfile, environment, Compose, plugin or server changes planned. Coordinate
shared files with TOOL-043 without reverting its work. Neither task depends on the other.

## 6. Acceptance criteria and traceability

| Criterion | Given | When | Then |
|---|---|---|---|
| AC-001 | Admitted caller and valid same-issue entry | Update supplied fields | Exact entry changes; no new entry; omitted fields excluded from PUT |
| AC-002 | Invalid input or wrong issue/entry/project | Invoke | Early safe error; no mutation |
| AC-003 | Own/all/denied permissions or reader runtime | Discover/invoke | Correct gates; own means credited user; no privilege inferred from logging |
| AC-004 | 204 or ambiguous dispatch with good/bad GET | Return receipt | Truthful independent acceptance/observation; one PUT |
| AC-005 | REST/MCP and existing catalog | Discover/invoke | Stable schema, destructive metadata, compatible readers/creation |
| AC-006 | Owned native fixture and concurrent observer | Update and verify | Correct native fields/identity and truthful mismatch/unavailable; exact owned cleanup |

| Requirement | Criteria | Verification method | Evidence/result |
|---|---|---|---|
| REQ-001 | AC-001/006 | TOOL-042-001/002/007 | Pass; linked testing evidence |
| REQ-002 | AC-002/006 | TOOL-042-002/007/008 | Pass; linked testing evidence |
| REQ-003 | AC-003 | TOOL-042-003/006/008 | Pass; linked testing evidence |
| REQ-004 | AC-004/006 | TOOL-042-004/005/007/009 | Pass; linked testing evidence |
| REQ-005 | AC-004/006 | TOOL-042-005/009 | Pass; linked testing evidence |
| REQ-006 | AC-005 | TOOL-042-006 | Pass; linked testing evidence |

## 7. Test plan and execution record

### Scenario plan

The user assigned test implementation and execution on 2026-10-08. Tests reuse PREP-002/016/017/018:
fake settings without .env, pytest/asyncio, HTTPX MockTransport, ASGI explicit lifespan and MCP SDK.
The scenario table below is retained; actual source-linked results are in
[TOOL-042 testing evidence](../../testing/evidence/tool-042-testing.md).

| Scenario | Criteria | Layer / setup and expected result | Mode |
|---|---|---|---|
| TOOL-042-001 | AC-001/002 | Unit: single/multiple fields, omitted/null/empty semantics, strict hours/date/IDs, comments clearing/1024 limit, reject unsupported fields | Offline |
| TOOL-042-002 | AC-001/002 | Adapter: exact ID/issue/project/user preflight, partial payload, no default reset, wrong/malformed linkage sends zero PUT | Offline |
| TOOL-042-003 | AC-003 | Auth/service: pinned/personal caller, own vs author vs other user, edit-own/all/no-edit/log-only, conditional/unknown vs proven denial, operation gates | Offline |
| TOOL-042-004 | AC-004 | Adapter: no-body 204, normalization, matching/mismatch/missing observations; 403/404/timeout/malformed GET preserves acceptance | Offline |
| TOOL-042-005 | AC-004 | Transport: pre-dispatch errors, 5xx/timeout/unexpected status after dispatch; one PUT, no mutation retry | Offline |
| TOOL-042-006 | AC-003/005 | REST/MCP: schemas/discovery/errors, annotations, capability report, explicit CSV and allowed_all, existing readers/create unchanged | Offline |
| TOOL-042-007 | AC-001/006 | Owned 7.0.2 + Inspector: update each field, native GET/state and stable ID, preserved unsupplied fields/unrelated entries, aggregate check, cleanup ledger | Opt-in live |
| TOOL-042-008 | AC-002/003 | Owned roles/settings: credited own vs submitting author, other-user/all editor, visibility denial, wrong issue, inactive activity, required comments, future/closed/daily settings | Opt-in live |
| TOOL-042-009 | AC-004/006 | Owned fault/concurrency setup: committed update with lost reply, read-back failure or intervening edit; no retry, reconcile exact ID, cleanup | Opt-in live |

Pagination N/A to mutation; reconciliation retains reader budgets. Empty 204 is success.
Malformed preflight is a hard error; read-back failure is unavailable observation.

### Execution evidence

| Evidence ID | Planned command/procedure | Scenarios | Actual / status |
|---|---|---|---|
| TOOL-042-EVID-001 | `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .` | Repository static lint/format | Failed, 2026-10-08: same seven unrelated lint findings and one unformatted file as TOOL-041 |
| TOOL-042-EVID-002 | `uv run --frozen --no-sync pytest tests/unit tests/integration -q --tb=short` | 001..006 / regressions | 1,755 passed, 1 older catalog case failed; corrected with passing rerun; no final full rerun claimed, 2026-10-08 |
| TOOL-042-EVID-003 | `uv run --frozen --no-sync pytest tests/e2e/test_time_entry_update_acceptance.py --run-e2e -q --tb=short` | 007..009 | Final 10 cases pass; exact owned cleanup, 2026-10-08 |
| TOOL-042-EVID-004 | Temporary owned writer startup and Inspector 2.8.0 discovery/update within E2E test | 006/007 | Pass, native entry checked; temporary server/config removed, 2026-10-08 |
| TOOL-042-EVID-005 | Scoped Ruff lint/format commands below | Changed runtime files | Passed, 2026-10-08: all checks passed, 13 files formatted |
| TOOL-042-EVID-006 | `uv run --frozen --no-sync mypy src` | Full runtime typing | Passed, 2026-10-08: no issues in 128 source files |
| TOOL-042-EVID-007 | `git diff --check`; manual diff review | Whitespace/architecture/contracts | Passed, 2026-10-08; no test/config/dependency changes |
| TOOL-042-EVID-008 | `bash scripts/doctor.sh` | Development prerequisites | Passed, 2026-10-08; credentials not read, no installation |
| TOOL-042-EVID-009 | Targeted additional seven edge cases and corrected all-reader SDK invocation | Offline follow-ups | 7 + 1 cases pass; see exact commands/results in evidence, 2026-10-08 |
| TOOL-042-EVID-010 | Scoped Ruff on changed test/fixture Python files; mypy src; git diff --check | Final test/static checks | Pass; 128 runtime files typed; known repository lint debt preserved, 2026-10-08 |

Exact scoped commands from Git Bash (the shell variable contains task-owned paths only):

```bash
task_files=(
  src/redmine_mcp/features/time_entries/__init__.py
  src/redmine_mcp/features/time_entries/write_models.py
  src/redmine_mcp/features/time_entries/ports.py
  src/redmine_mcp/features/time_entries/service.py
  src/redmine_mcp/features/time_entries/write_router.py
  src/redmine_mcp/integrations/redmine/time_entry_updates.py
  src/redmine_mcp/integrations/redmine/__init__.py
  src/redmine_mcp/integrations/redmine/capabilities.py
  src/redmine_mcp/bootstrap.py
  src/redmine_mcp/auth/policy.py
  src/redmine_mcp/auth/capability_models.py
  src/redmine_mcp/auth/capabilities.py
  src/redmine_mcp/mcp/annotations.py
)
uv run --frozen --no-sync ruff check --fix "${task_files[@]}"
uv run --frozen --no-sync ruff format "${task_files[@]}"
uv run --frozen --no-sync ruff check "${task_files[@]}"
uv run --frozen --no-sync ruff format --check "${task_files[@]}"
```

Ruff lint --fix found no lint changes necessary; formatting changed only service.py. The
repository-wide baseline findings are I001 in `api/dependencies.py`, `common/read_budget.py`,
`features/attachments/router.py`, `integrations/redmine/retry.py`,
`integrations/redmine/transport.py`, `mcp/read_limits.py`, and E501/formatting in
`features/users/capability_service.py`. These files are unchanged by TOOL-042.

Coding-stage limitations: no tests, fixtures, startup, Inspector, live calls or deployment ran
during coding. The subsequent user-authorized testing stage supplies EVID-002/003/004/009/010.
No build or test-bearing check wrapper ran; packaging/dependency changes are N/A. Current native
policy settings were tested without global changes; alternate policy/plugin/concurrency variants
remain limited as documented. Full regression plus passing targeted fixes are not a claim of
a clean full-suite rerun after final additions. TOOL-040/041 acceptance remains independent.

## 8. Implementation and review record

- Changes made: TimeEntryUpdateRequest/Result, TimeEntryUpdater Protocol, optional updater
  service/bootstrap wiring, guarded PUT route, RedmineTimeEntryUpdates and public exports.
  Strict partial updates reject empty/null/unknown inputs; comments="" can clear native comments.
- Gateway: shared require_issue_time_entry validates exact entry/issue/project identities and
  credited user using bounded caller-key GETs. Both personal-key capability resolution and
  mutation preflight use it; separate reads preserve the existing request-local architecture.
  One no-body-success PUT sends only supplied fields; independent GET compares submitted fields
  and original issue/project/user identities with native hour rounding. Observation failure
  preserves acceptance; matching read-back cannot convert uncertainty into acceptance.
- Authorization/registration: explicit WRITE_OPERATIONS/WriteOperation additions, time_entry_id
  intent and entry-derived view-time AND eligible own/all edit clauses. Project-level candidates
  and reports share edit alternatives. Destructive metadata is set; current catalog is 18 reads
  and 17 writes. allowed_all includes update on upgraded writers; fixed CSV requires addition.
- Deviations: none to public behavior. Existing mapper/rounding/writer are reused; capabilities
  and gateway perform separate bounded preflight reads rather than introduce cross-adapter state.
- Checks: EVID-005/006/007/008 pass; EVID-001 records the existing unrelated baseline failures.
  EVID-002/003/004 remain pending. Tests and fixtures were neither written nor executed.
- Documentation: README, changelog, architecture, tool reference, configuration, manual testing
  handoff and task/dashboard updated without changing deployed settings or historical evidence.
- Final diff review: router -> service -> Protocol -> gateway, credited-user ownership, target
  identity, partial payload and receipt semantics inspected. No credentials, dependency/lockfile,
  tests, fixtures or environment changes. TOOL-043 remains planned and unimplemented.
- Testing handoff: implement TOOL-042-001..009. Extend
  `tests/integration/test_current_tools.py` operation/argument/payload/result maps and shared
  `tests/integration/conftest.py` writer catalog/preflight/read-back mocks; preserve TOOL-040/041
  pending fixture additions. Include strict empty/null inputs, own versus author identity,
  wrong linkage/no PUT, rounded fields, 204/read-back failures and one-dispatch ambiguity.
  Cover REST/MCP discovery/schema/annotations/allowed_all/capability-report compatibility.
  Owned 7.0.2 role/settings/fault/concurrency/Inspector checks must verify resulting entry state,
  preserved controls and exact cleanup. Incident entries must not become test fixtures.
- Coding-stage remaining blocker: separately authorized testing and acceptance; no coding blocker.
- Subsequent testing assignment: the user authorized implementation/execution on 2026-10-08.
  Added unit, stateful integration, actual MCP SDK and owned native acceptance tests, extended
  shared catalog fixtures and a separate task-owned Ruby setup/cleanup helper. Native updates,
  credited-user own/all boundaries, inactivity, current native policy validation, commit faults,
  intervening edits, Inspector and exact resource cleanup pass. The final offline regression
  finished with 1,755 passes and one older reader-catalog argument failure. Added its missing
  project_id and reran it passing; seven late edge cases also pass. Final owned live set has
  10 passes, including Inspector, active/inactive activities, current settings, raw aggregate
  semantics and native fault/concurrency observations. Scope/limits and exact commands/results
  are in the linked evidence. No runtime code correction was required.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [x] Every requirement has passing acceptance evidence within the documented scope.
- [x] Relevant tests and scoped repository checks pass; unrelated repository Ruff debt disclosed.
- [x] Owned live verification and cleanup completed.
- [x] Public documentation reflects implemented behavior.
- [x] Implementation reviewed with no unresolved behavior decisions.
- [x] Implementation evidence and dashboard synchronized.

Final status: **complete** for the specified update contract. Offline/native/Inspector evidence
and scoped static checks pass; all observed regression failures are resolved by targeted reruns.
No clean final full-suite rerun or exhaustive native-policy/plugin/race coverage is claimed.
Cleanup confirms zero owned projects/entries/users/roles/activities; no incident entry or shared
server configuration changed. No required task work remains. TOOL-043 stays separately planned.
