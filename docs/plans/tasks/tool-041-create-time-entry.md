# tool-041: Create a time entry on a visible issue

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../../configuration.md#separate-writer-deployment).

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-041-create-time-entry |
| Assigned capability | Log eight hours today on each selected issue for the authenticated Redmine caller |
| Type / access | Add tool / write |
| Destructive effects | Creates one time entry, changes spent-time totals and invokes native save hooks/webhooks; no intended deletion |
| Status | blocked |
| Dependencies | Existing issue reader/caller identity; existing restricted writer and personal-key authorization; accepted prep-019/020/027 transport/catalog baseline; prep-002/016/017/018 for later testing; TOOL-040 for activity names |
| Related tasks | [tool-040](tool-040-list-project-time-entry-activities.md), [tool-012](tool-012-list-issue-time-entries.md), [tool-035](tool-035-list-time-entries.md), [tool-031](tool-031-list-my-project-capabilities.md) |
| Target Redmine version | Pinned 7.0.2 source inspected; new runtime acceptance pending |
| Last updated | 2026-10-08, Codex |
| Progress summary | Implementation finished; scoped Ruff lint/format and full-source mypy pass; testing pending |
| Blocker | TOOL-041-001..009 acceptance remains unexecuted; unrelated repository-wide Ruff findings remain |
| Next action | Separately authorize test implementation/execution, owned native state/permission checks and Inspector acceptance |

## 2. Discovery and evidence

### Client outcome and repository baseline

The user found two issues with tag `notification`, then requested eight hours on each today.
`list_issue_time_entries` and `list_time_entries` only read existing entries; `update_issue`
explicitly excludes time-entry writes. `REDMINE_WRITER_OPERATIONS=allowed_all` expands the
registered write catalog, which contains no time-entry creation operation. Creation requires
its own mutation; extending an issue reader would mix read and write contracts.

Reuse `features/time_entries/{models,ports,service}.py`, `integrations/redmine/time_entries.py`,
`bootstrap.py`, API dependency wiring, and the bounded single-attempt `RedmineWriter`. The
new write route must register before MCP creation. Follow router -> service -> Protocol ->
gateway; services import neither FastAPI nor HTTPX. Native Redmine remains the authority for
project access, issue visibility, settings, permission and validation. No database access.

Applicable sources: `AGENTS.md`, `CONTRIBUTING.md`,
[workflow](../../workflows/redmine-tools.md), [template](../../templates/redmine-tool-task.md),
[tool reference](../../tool-reference.md), [configuration](../../configuration.md),
[write consistency](prep-019-write-outcome-consistency.md),
[catalog baseline](prep-020-current-catalog-acceptance.md) and
[read retries](prep-027-redmine-read-retries.md).
The working tree was clean at discovery. Preserve existing task IDs/evidence; TOOL-037/038/039
have historical meanings and are not reused. Planning changes documentation only. No credentials,
local runtime configuration, Redmine state, fixtures or tests are changed.

The user assigned TOOL-041 coding on 2026-10-08 and explicitly waived testing for TOOL-040.
That waiver accepts the named-activity prerequisite for continuation and does not waive TOOL-041
testing or create runtime acceptance evidence. At this coding stage's start the working tree
contained TOOL-040 code/docs plus the earlier untracked TOOL-040/041 plans; all prior changes
were preserved. Required Git Bash/Git/Python/uv prerequisites passed `scripts/doctor.sh`.

### Upstream evidence

Verified on 2026-10-08 using the existing local archive of the official
[Redmine 7.0.2 release](https://www.redmine.org/releases/redmine-7.0.2.tar.gz). Files were read,
not executed. `deploy/compose.test.yaml` pins the 7.0.2 image and digest.

| Source URL or versioned source | Date verified | Version | Behavior / permission | Evidence or limitation |
|---|---|---|---|---|
| [REST TimeEntries](https://www.redmine.org/projects/redmine/wiki/Rest_TimeEntries) | 2026-10-08 | Unversioned documentation | POST time entry; hours, date, activity, comments; 201/422 | Overview only; documented comment limit is older than pinned source |
| [TimelogController](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/controllers/timelog_controller.rb), `create`, `find_time_entry` | 2026-10-08 | 7.0.2 | Initializes caller as author/user, native default date/activity, checks `log_time`; 201 renders show template; GET by ID checks visibility | Creation and later read permission are distinct |
| [ApplicationController](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/controllers/application_controller.rb), `find_optional_project` | 2026-10-08 | 7.0.2 | Top-level project_id sets project before controller initialization/authorization | Pass resolved project as query parameter to obtain project/caller activity defaults |
| [TimeEntry model](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/models/time_entry.rb) | 2026-10-08 | 7.0.2 | Validates issue/project/activity, required fields, nonnegative hours, daily maximum, future-date and closed-issue settings; comments maximum 1024 | Native settings can reject an otherwise valid MCP input; concurrent daily-limit checks are not an atomic reservation |
| [TimeEntryActivity model](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/models/time_entry_activity.rb), `default_activity_id` | 2026-10-08 | 7.0.2 | Sole available activity, caller role defaults, project/global defaults | Omit activity to use native selection; never infer a default from catalog order |
| [Permissions](https://raw.githubusercontent.com/redmine/redmine/7.0.2/lib/redmine/preparation.rb) | 2026-10-08 | 7.0.2 | Time-tracking module: `log_time`; reads use `view_time_entries`; other-user writes use `log_time_for_other_users` | Other-user creation is excluded from this task |
| [Time-entry API template](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/views/timelog/show.api.rsb) | 2026-10-08 | 7.0.2 | 201/GET expose entry/project/issue/user/activity, hours, comments and spent_on | Hours getter rounds to minutes and API then rounds hours to two decimals; author is not exposed |

Exact source takes precedence over the unversioned API page for the comments limit. Optional
required time-entry custom fields, plugins and hooks can impose additional native validation.
This first contract exposes no custom fields and must report rejection safely rather than
pretend those installations are fully supported. Previously observed localhost:3000 was 6.0.5;
its results cannot establish new 7.0.2 acceptance. No new runtime/version check was performed.

| Client outcome / tool | Existing coverage | Access | Owner | Dependencies | Scope |
|---|---|---|---|---|---|
| Choose an activity name for the issue's project | None | Read | TOOL-040 | Existing project reader | Separate prerequisite |
| Create one entry for the caller on a visible issue | Read-only entries | Write | TOOL-041 | Existing identity/writer; TOOL-040 for named choices | In scope |
| Log eight hours on two selected issues | No writer | Two calls | TOOL-041 | Resolved issues/date/optional activity | Client orchestration; no batch transaction |

### Questions and decisions

| ID | Decision | Blocking? | Resolution date |
|---|---|---|---|
| DEC-001 | `create_time_entry` logs own time on exactly one visible issue; no user_id/project-only mode | No | 2026-10-08 |
| DEC-002 | Require explicit spent_on; the client resolves relative dates using the user's timezone | No | 2026-10-08 |
| DEC-003 | Optional activity_id uses native defaults with the resolved project initialized before save | No | 2026-10-08 |
| DEC-004 | Positive finite JSON numeric hours; native settings govern maximum/future/closed policies | No | 2026-10-08 |
| DEC-005 | No automatic write retries, deduplication, rollback, batch or idempotency promise | No | 2026-10-08 |
| DEC-006 | Independent read-back is optional evidence; failure preserves write acceptance/uncertainty | No | 2026-10-08 |
| DEC-007 | Planning/coding/testing are separate assignments; commands below remain pending | No | 2026-10-08 |

## 3. Requirements

### Goal and boundaries

Authenticated callers create their own time entry for a previously selected issue. In scope:
one issue, hours, explicit date, optional activity and comments, restricted writer integration,
caller attribution, write receipt and independent state verification. Out of scope: project-only
logs, another user's time, update/delete, bulk creation, activity administration, custom fields,
automatic tag-based selection inside the mutation, arbitrary dates inferred by the server,
settings changes, retries and automatic cleanup. Existing readers and writers remain compatible.

Writer prerequisites are `REDMINE_WRITE_ENABLED=true`, separate writer endpoint, enabled
`create_time_entry` or standalone `allowed_all`, authenticated caller admission under existing
pinned/personal modes, issue visibility and native `log_time` in that issue's project. Preflight
uses the issue reader and therefore also needs issue read access. `view_time_entries` is needed
for activity discovery and independent read-back, not required merely to accept creation.

| ID | User need | Required observable behavior | Constraints |
|---|---|---|---|
| REQ-001 | Log own time | Create one entry on the selected visible issue, credited to the authenticated caller | No caller-supplied user_id |
| REQ-002 | Supply accurate hours/date/activity/comments | Strict early validation and exact native payload; omitted activity uses native default | Explicit spent_on; settings remain native |
| REQ-003 | Keep write access restricted | Operation/user/runtime gates and project `log_time` evidence; native final checks | `allowed_all` includes only registered writes |
| REQ-004 | Know what happened | Separate accepted/uncertain outcome from matched/mismatch/unavailable read-back | Never infer failed write from failed GET |
| REQ-005 | Avoid accidental duplicate entries | One POST attempt per invocation; safe reconciliation instructions after ambiguity | Identical repeated calls may create separate entries |
| REQ-006 | Use the tool through REST/MCP | Stable registered operation, strict schema, truthful annotations/capabilities, existing-contract compatibility | No generic CRUD proxy |

Synthetic workflow: list issues with `tags_any=["notification"]`; independently select IDs;
resolve the calendar date to `2026-10-08` in Asia/Bangkok for this example; call create once per
issue with `hours=8`. Two accepted calls add 16 hours, not eight split between them. An existing
daily maximum may accept the first and reject the second; retain the first receipt and do not
rollback or report an all-or-nothing result. Example issue IDs below are illustrative and must
not be used as live testing fixtures.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| New tool / stable operation ID | `create_time_entry` |
| Exact purpose/description | Log time for the authenticated Redmine caller on one visible issue. Required issue_id, positive numeric hours and explicit spent_on date. Optional activity_id uses the project's native caller default when omitted; comments are optional. Requires the separate restricted writer and Log spent time permission. Each call creates a separate entry and changes spent-time totals. Reports write acceptance separately from independent read-back; reconcile uncertain outcomes before retrying. |
| REST | `POST /api/v1/issues/{issue_id}/time-entries` |
| Authentication | Existing `require_write_access`, caller principal and key; no impersonation |
| MCP exposure | Add to WRITE_OPERATIONS and writer catalog; generated from REST route |
| Annotations | readOnlyHint=false, destructiveHint=false, idempotentHint=false, openWorldHint=true |
| Project capability | Necessary `log_time`; target issue read/visibility and native validation remain conditional |

### Inputs

Use `TimeEntryCreateRequest` with `extra="forbid"`. Unknown body properties are rejected before
mutation, including user_id, project_id, author_id, issue_id in the body, batch and custom_fields.

| Field/location | Type | Required/default | Validation | Omitted/null/empty | Upstream mapping |
|---|---|---|---|---|---|
| issue_id / path, MCP argument | Integer | Required | Positive; strict service validation | Rejected | time_entry.issue_id |
| hours / body | JSON number | Required | Actual int/float, finite and >0; reject bool, numeric strings, negative and zero | Rejected | time_entry.hours as supplied numeric hours |
| spent_on / body | YYYY-MM-DD date | Required | Strict real calendar date; reject datetime and relative words | Rejected | time_entry.spent_on |
| activity_id / body | Integer | Optional, omitted | Strict positive ID; native project membership/activity validation | Explicit null rejected | Include only if supplied |
| comments / body | String | Optional, omitted | Maximum 1024 characters; preserve supplied content; no invented text | Null rejected; empty string sent and subject to native required-comments rules | Include only if supplied |

No MCP user_id or project_id. Resolve project from a bounded visible-issue GET and retain its ID.
TOOL-040 lets a caller supply a known activity; it is not a mandatory gateway request.

### Outputs and mapping

`TimeEntryCreateResult` follows existing single-write receipt conventions:

- `outcome`: `accepted` or `uncertain`.
- `upstream_accepted`: true only after native 201; otherwise null in uncertain results.
- `resource_id`: strict positive ID from a reliable native creation object, otherwise null.
- `verification`: `matched`, `mismatch` or `unavailable`, default unavailable.
- `field_verification`: states for issue_id, project_id, user_id, hours, spent_on, and supplied
  activity_id/comments. Missing comparisons are unavailable, never silently matched.
- `observed_time_entry`: nullable independently read `TimeEntry` from the existing reader model;
  the POST body is not independent read-back evidence.

Sequence:

1. Validate input and runtime/caller/operation admission.
2. Read `issues/{issue_id}.json` without unnecessary expansions; validate issue ID and project.
   In personal-key mode extend the existing `WriteIntent` resolution with project `log_time`,
   preserving conditional/unknown evidence and blocking only proven denial. Pinned-key mode
   retains its existing gate and native checks. Reuse request-local issue evidence when possible.
3. Send exactly one `POST time_entries.json` with top-level query `project_id=<resolved id>`
   and body `{"time_entry":{"project_id":<same id>,"issue_id":<id>,"hours":<number>,
   "spent_on":"YYYY-MM-DD",...supplied optional fields...}}`. Top-level project initializes
   caller/project activity defaults before safe attributes are assigned. Body project guards
   against silently retargeting a moved issue. Never send user_id or author_id.
4. Native 201 returns `time_entry`; validate its strict ID and project/issue/caller references.
   Missing/malformed/empty creation body or inconsistent identity leaves outcome uncertain,
   preserving upstream_accepted=true when 201 was seen. Do not extract IDs from Location URLs.
5. If a reliable ID exists, attempt one logical bounded `GET time_entries/{id}.json` using
   existing eligible GET retries/budgets. Strictly validate wrapper and requested ID, map the
   existing TimeEntry shape, and compare independent fields. GET failure or missing compared
   fields leaves verification unavailable; a known unequal field means mismatch. Matched
   requires every expected field. An uncertain receipt remains uncertain even if GET matches.

Normalize expected hours for comparison only: the pinned TimeEntry getter rounds to the nearest
whole minute using positive half-up rounding, then the API rounds decimal hours to two places.
Use decimal arithmetic for this comparison; do not change the submitted numeric hours or impose
an invented 24-hour limit. Document that returned hours can differ from the submitted fraction.
Do not sum binary floating-point values when reconciling totals.

Request example:

```json
{"issue_id": 488, "hours": 8, "spent_on": "2026-10-08", "activity_id": 9}
```

REST places issue_id in the path. Accepted independently verified response, illustrative only:

```json
{
  "outcome": "accepted",
  "upstream_accepted": true,
  "resource_id": 901,
  "verification": "matched",
  "field_verification": {
    "issue_id": "matched", "project_id": "matched", "user_id": "matched",
    "hours": "matched", "spent_on": "matched", "activity_id": "matched"
  },
  "observed_time_entry": {
    "id": 901, "project": {"id": 2, "name": "Synthetic API"},
    "issue_id": 488, "user": {"id": 7, "name": "Synthetic Caller"},
    "hours": 8, "spent_on": "2026-10-08",
    "activity": {"id": 9, "name": "Development"}, "comments": ""
  }
}
```

Public HTTP 200 with the receipt and structured MCP result, consistent with current writers.
Native 201 is distinguished in upstream_accepted. No pagination, batch, expansions or automatic
list scans. Existing readers, receipt shapes and unrelated writes remain unchanged.

### Errors

| Scenario | Detection layer | REST status / safe code | MCP / reconciliation |
|---|---|---|---|
| Invalid/null/unknown input | Route/service | 422 / `invalid_parameters` | Existing envelope; no mutation |
| Missing/invalid key | Authentication | 401 / `invalid_credentials` | Existing envelope |
| Writer disabled, caller/operation denied or proven project denial | Existing gates/capability service | 403 / `permission_denied` | No POST; allowed_all does not bypass these gates |
| Forbidden/missing issue or project | Native preflight/POST | 403 / `access_denied`, 404 / `resource_not_found` | Sanitized; no hidden state disclosed |
| Native validation: activity/default, required comments/custom fields, daily hours, future date or closed issue | Native POST / RedmineWriteRejected | 422 / `invalid_parameters`, existing safe write-rejected message | Definite rejection; no upstream bodies/comments echoed |
| Failed/malformed preflight | Existing GET transport/mapping | Existing read errors, including 502 / `upstream_response` | No POST |
| Pool unavailable or known pre-dispatch connection failure | RedmineWriter | Existing 503 / `upstream_busy` or 502 / `upstream_unavailable` | No automatic POST retry |
| Dispatched timeout/transport interruption, native 5xx or unexpected success status/body | RedmineWriter/adapter | 200 uncertain receipt | Creation may have committed; preserve any trustworthy acceptance/ID; reconcile |
| Rejected other native statuses, including rate limit | Existing writer mapping | Existing documented safe status/code | No new retry policy |
| Read-back forbidden, missing, malformed, oversized, budget failure or timeout | Adapter/GET client | Preserve existing receipt; verification unavailable | Failed GET does not prove failed POST |

### Write semantics

- Exact effects: one new caller-credited entry, aggregate spent-time changes, native model
  hooks/webhooks. No intentional issue schedule/progress edits; plugin effects remain native.
- Permission: `log_time` in the resolved project plus the issue-reader prerequisite. Discovery
  and read-back use `view_time_entries`; neither `edit_time_entries` nor
  `log_time_for_other_users` is required for own creation. Cleanup permissions are separate.
- Duplicates: each invocation may create another entry, including identical payloads. No
  native unique request key, deduplication by date/hours, automatic retry or rollback.
- Ambiguity: retain the receipt; reconcile known resource IDs using readable state. If no ID
  exists, use bounded `list_time_entries` with issue_id, user_id="me", spent_from/spent_to and
  compare caller/date/hours/activity/comments. Matching fields alone cannot prove which call
  created an entry. Respect pagination/read budgets; report ambiguity rather than infer absence.
- Partial workflow success: two issue calls are independent. Record each receipt; stop or
  report uncertainty before any manual retry. Do not silently redo the first accepted call.
- Concurrency: no locking, reservation or atomic batch guarantee. Issue moves, activity changes,
  settings and permissions may change after preflight; native save checks and read-back apply.
  The native daily-hour check is not a guarantee against concurrent submissions exceeding it.
- Verification: only independent returned entry state establishes field comparison. Do not
  rely on issue totals alone, especially with role visibility and descendant totals.
- Disposable verification: explicitly authorized tests use task-owned issues/users/project
  settings and a cleanup ledger in the marked isolated 7.0.2 environment.
- Cleanup: delete only exact task-created IDs using a separately authorized administrative
  fixture mechanism with native edit/delete permissions. No production delete tool added.
  Reconcile uncertain creations before cleanup; report unidentifiable entries and cleanup
  failures. Delivered webhook effects cannot be undone by deleting a fixture entry.

Specification exit check: material public behavior resolved. Source supports the contract;
runtime acceptance and configured plugin compatibility remain pending testing work.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Planned verification |
|---|---|---|---|---|
| 1 | Review accepted writer baseline and TOOL-040 named-selection contract | Linked task documents and current source | Existing baseline | Manual contract review |
| 2 | Add strict creation input/result and dedicated creator Protocol | `features/time_entries/models.py` or new `write_models.py`, `ports.py`, exports | 1 | TOOL-041-001/002 |
| 3 | Add issue preflight, project-initialized POST and optional independent read-back using existing transports | New `integrations/redmine/time_entry_creations.py`, existing reader mapping helpers | 2 | TOOL-041-002/004/005 |
| 4 | Add optional creator/authorizer to service and caller-aware bootstrap wiring | `features/time_entries/service.py`, `bootstrap.py`, integration exports | 2-3 | TOOL-041-001/003 |
| 5 | Add guarded writer route and register before MCP creation | New `features/time_entries/write_router.py`, `app.py`; reuse API service dependency | 4 | TOOL-041-003/006 |
| 6 | Register operation, WriteIntent literal/resolution, log_time permission and discovery/reporting | `auth/policy.py`, `auth/capability_models.py`, `auth/capabilities.py`, `integrations/redmine/capabilities.py`, MCP catalog | 5 | TOOL-041-003/006 |
| 7 | Update public contracts, allowed_all examples and manual workflow | `docs/tool-reference.md`, `docs/configuration.md`, `docs/manual-verification.md`, `CHANGELOG.md` | 6 | Manual source/prose/example review |
| 8 | Separately authorized test implementation and execution | `tests/unit/`, `tests/integration/`, selected `tests/e2e/`, synthetic fixture helpers | Implementation and fixture ownership | TOOL-041-001..009 |

The catalog grows by one writer here and one reader in TOOL-040. `allowed_all` includes the new
writer automatically after registration and server upgrade; fixed CSV configurations require
explicit addition. Do not enable writes, change `.env`/Compose values, install plugins or alter
the running Redmine server in planning/coding. No dependencies/lockfile changes planned.
Coding assignments use the coding skill and hand off tests without writing/running them.

## 6. Acceptance criteria and traceability

| Criterion | Given | When | Then |
|---|---|---|---|
| AC-001 | Admitted caller, visible issue and native log permission | Create eight hours on explicit date | One caller-credited entry; correct issue/project/date/hours and ID |
| AC-002 | Valid/invalid input and default configurations | Invoke | Exact payload or early error; project/caller native default when omitted; invalid default/activity rejected |
| AC-003 | Reader, denied writer/caller/operation/project or log-only caller | Discover/invoke | Gates enforced; creation does not require time-entry read permission |
| AC-004 | Accepted POST with matching, differing or unreadable GET | Read back | Truthful independent verification and preserved acceptance |
| AC-005 | Native 5xx, dispatched timeout or unusable 201 payload | Invoke | Uncertain receipt; exactly one POST; no duplicate inferred absent |
| AC-006 | Two separate calls and native daily limit | Log eight hours per issue | Distinct receipts; 16 hours if both accepted; partial rejection does not undo first |
| AC-007 | REST/MCP client and existing catalog | Discover/invoke | Stable schema, non-idempotent metadata, capability mapping and compatible readers/writers |

| Requirement | Criteria | Scenarios | Evidence/result |
|---|---|---|---|
| REQ-001 | AC-001 | TOOL-041-002/007 | Pending |
| REQ-002 | AC-002 | TOOL-041-001/002/004/007/008 | Pending |
| REQ-003 | AC-003 | TOOL-041-003/006/008 | Pending |
| REQ-004 | AC-004/005 | TOOL-041-004/005/007/009 | Pending |
| REQ-005 | AC-005/006 | TOOL-041-005/007/009 | Pending |
| REQ-006 | AC-007 | TOOL-041-006/007 | Pending |

## 7. Test plan and execution record

### Scenario plan

Reuse [offline baseline](prep-002-offline-tests.md),
[unit](prep-016-unit-testing.md), [integration](prep-017-offline-integration-testing.md) and
[owned live infrastructure](prep-018-live-e2e-testing.md). Offline tests use fake settings without
`.env`, HTTPX MockTransport, explicit ASGI lifespan and MCP SDK clients. The scenario table is
a future assignment, not authorization to add/run tests now.

| Scenario ID | Criteria | Layer | Setup/input and expected result | Mode |
|---|---|---|---|---|
| TOOL-041-001 | AC-002 | Unit/service | Positive numbers/date, decimals; reject zero/negative/bool/string/NaN/infinity, invalid IDs/date/datetime/null and unsupported properties before POST | Offline |
| TOOL-041-002 | AC-001/002 | Gateway | Exact one POST, issue-derived project in query/body, caller field omissions, optional activity/comments mapping; valid 201 and strict ID/reference mapping | Offline |
| TOOL-041-003 | AC-003 | Service/security | Disabled writer, explicit CSV, allowed_all, caller admissions and pinned/personal modes; issue-derived log_time expression; proven denial vs conditional/unknown; no other-user input | Offline |
| TOOL-041-004 | AC-002/004 | Gateway | Matching/mismatching/missing fields, rounded hours and comments; 201 payload is not independent verification; unreadable/malformed GET preserves receipt; settings/activity rejection | Offline |
| TOOL-041-005 | AC-005 | Transport/adapter | Commit ambiguity: 5xx, dispatched timeout, pre-dispatch/pool failure, empty/malformed/oversized 201, unexpected status, wrong references; exactly one POST | Offline |
| TOOL-041-006 | AC-003/007 | REST/MCP | Discovery, schema parity/null/number rules, writer gates, annotations, invocation/errors, allowed_all and capability reports; old readers/writers unchanged | Offline |
| TOOL-041-007 | AC-001/004/006/007 | Owned native 7.0.2 + Inspector | Two task-owned tagged issues, eight hours each on explicit date; two IDs and 16 caller-visible hours, independent GETs/native parity, deliberate duplicate creates distinct ID; cleanup exact owned IDs | Opt-in live |
| TOOL-041-008 | AC-002/003/006 | Owned role/settings fixtures | Issue-visible caller with log_time but no view_time_entries vs time-read-only/no-log/foreign project, private issue, closed/future policy, required comments, disabled/wrong activity; role/project default differs from global; no default => 422; daily limit accepts first/rejects second | Opt-in live |
| TOOL-041-009 | AC-004/005 | Owned fault-injection fixture | Native commit followed by lost/500 response; reconcile exact fixture ID with no retry; read-back forbidden; unidentifiable outcomes reported and owned cleanup verified | Opt-in live |

Pagination applies only to optional manual reconciliation through the existing reader, whose
budgets must remain respected. No creation pagination/no-body success contract exists: native
201 is expected to contain `time_entry`. Empty 201 is uncertain. Failed responses are sanitized.
Live fixture changes require explicitly authorized isolated setup and cleanup, never a reset
or modification of the shared localhost:3000 server merely to validate this feature.

### Execution evidence

| Evidence ID | Planned command/procedure | Scenarios/check | Expected | Actual/status/date |
|---|---|---|---|---|
| TOOL-041-EVID-001 | `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .` | Repository lint/format | No introduced findings | Same seven unrelated pre-existing lint findings and one unformatted file recorded in TOOL-040; failed, 2026-10-08 |
| TOOL-041-EVID-002 | `uv run --frozen pytest tests/unit tests/integration -q` after separately authorized test implementation | TOOL-041-001..006 | New writer contracts and relevant regressions pass | Not run; pending |
| TOOL-041-EVID-003 | `uv run --frozen pytest tests/e2e/test_time_entry_create_acceptance.py --run-e2e -q` after that task-owned file/fixtures exist and live testing is authorized | TOOL-041-007..009 | Pinned native state/permissions/ambiguity/cleanup pass | Not run; pending |
| TOOL-041-EVID-004 | Startup of the isolated writer and Inspector discovery/selected creation calls | TOOL-041-006/007 | Correct native MCP schema, result and state; owned cleanup | Not run; pending |
| TOOL-041-EVID-005 | Scoped Ruff commands below | Writer feature/integration points | Lint/format pass | All checks passed; 18 files already formatted; passed, 2026-10-08 |
| TOOL-041-EVID-006 | `uv run --frozen --no-sync mypy src` | Runtime typing | Pass | No issues in 127 source files; passed, 2026-10-08 |
| TOOL-041-EVID-007 | `git diff --check`; manual code/docs inspection | Whitespace/architecture/contracts | Pass | Passed, 2026-10-08; tests/config/dependencies untouched |
| TOOL-041-EVID-008 | `bash scripts/doctor.sh` | Prerequisites | Required tools available | Passed, 2026-10-08; no credentials read or dependency installation |

Exact scoped commands executed from Git Bash:

```bash
uv run --frozen --no-sync ruff check src/redmine_mcp/features/time_entries src/redmine_mcp/integrations/redmine/time_entry_creations.py src/redmine_mcp/integrations/redmine/time_entries.py src/redmine_mcp/integrations/redmine/__init__.py src/redmine_mcp/bootstrap.py src/redmine_mcp/app.py src/redmine_mcp/auth/policy.py src/redmine_mcp/auth/capability_models.py src/redmine_mcp/auth/capabilities.py src/redmine_mcp/integrations/redmine/capabilities.py
uv run --frozen --no-sync ruff format --check src/redmine_mcp/features/time_entries src/redmine_mcp/integrations/redmine/time_entry_creations.py src/redmine_mcp/integrations/redmine/time_entries.py src/redmine_mcp/integrations/redmine/__init__.py src/redmine_mcp/bootstrap.py src/redmine_mcp/app.py src/redmine_mcp/auth/policy.py src/redmine_mcp/auth/capability_models.py src/redmine_mcp/auth/capabilities.py src/redmine_mcp/integrations/redmine/capabilities.py
```

Repository findings remain I001 imports in `api/dependencies.py`, `common/read_budget.py`,
`features/attachments/router.py`, `integrations/redmine/retry.py`,
`integrations/redmine/transport.py`, `mcp/read_limits.py`, and E501/formatting in
`features/users/capability_service.py`. Those files have no task changes. Ruff import fixes and
formatting were applied only to task-owned runtime files; no unrelated fixes or suppressions.

Limitations: no tests/fixtures were added, changed or executed; no startup, Inspector, Redmine
mutation, deployment or runtime configuration changes occurred in this coding stage. The full
check wrapper/architecture script and build were not run. Source findings, static checks and old
catalog results are not new acceptance evidence. TOOL-040 testing is waived; TOOL-041 testing is
pending separately. Build
is N/A unless implementation changes packaging/dependencies. Broader runtime versions and
installations requiring unsupported time-entry custom fields remain outside this first contract.

## 8. Implementation and review record

- Changes made: strict TimeEntryCreateRequest/Result and dedicated creator Protocol; optional
  creator/authorizer/caller identity in the existing service; guarded writer route registered
  before MCP creation; authenticated principal wiring in bootstrap; explicit write catalog and
  WriteIntent registration; issue-derived log_time resolution for discovery/invocation/reporting.
- Gateway: bounded visible-issue preflight resolves project, sets top-level/native-body project,
  omits user/author IDs, preserves supplied date/hours/optional activity/comments and dispatches
  one POST. Positive native creation IDs and 201 acceptance survive uncertainty. Independent GET
  maps the existing TimeEntry shape and compares expected fields, using decimal native hour
  normalization. Missing/invalid observations preserve acceptance and unavailable verification.
- Compatibility: existing reader mapping extracted into a shared public helper while retaining
  its private reader delegate and output behavior; optional service constructor parameters
  preserve existing reader callers. No shared transport retry, reader schema or config changes.
  New catalog has 18 reads/16 writes; allowed_all includes creation on upgraded writer processes.
- Plan deviations: no material contract change. Personal-key permission resolution and gateway
  retain separate bounded issue reads rather than adding a cross-adapter cache; native project
  binding/read-back still enforce target semantics. A known positive creation ID is retained
  for reconciliation even if other creation fields are malformed or inconsistent.
- Static checks: EVID-005/006/007/008 pass; EVID-001 reports the known unrelated baseline findings.
  No automated tests, startup, Inspector or live checks; EVID-002/003/004 remain pending.
- Documentation updated: tool reference, writer configuration, manual verification, README,
  architecture, changelog and both task/dashboard records. TOOL-040's explicit testing waiver
  is documented without claiming passed tests. Dated historical acceptance is preserved.
- Final diff inspection: router -> service -> creator Protocol -> gateway, strict inputs,
  issue/project/caller binding, one POST, sanitized shared errors and independent verification
  reviewed on 2026-10-08. No credentials, dependency/lockfile, configuration, tests or live changes.
- Testing handoff: add TOOL-041-001..009 request/service/adapter/auth/REST/MCP scenarios. Extend
  `tests/integration/test_current_tools.py` operation/payload/result mappings and shared
  synthetic fixtures in `tests/integration/conftest.py` for issue project/defaults, POST and
  GET time_entry responses, authenticated caller injection and the newly registered writer.
  Existing all-reader maps also need the waived TOOL-040 operation as described in its record.
  Cover null/unknown/strict inputs, native rounding and defaults, one-dispatch faults, read-back
  missing/malformed/forbidden/mismatch and allowed_all/discovery/reporting. Owned 7.0.2 role,
  setting, ambiguous-commit, Inspector and exact-ID cleanup scenarios remain required unless
  separately waived by the user. Test infrastructure is preserved for that future assignment.
- Remaining blocker: TOOL-041 testing/acceptance outstanding; no implementation blocker.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed; resulting native entries and cleanup checked.
- [x] Public documentation reflects implemented behavior.
- [x] No unresolved decision changes the specified behavior.
- [x] Implementation diff reviewed and task/dashboard synchronized.

Final status: **blocked — implementation finished; testing pending**. Outcome: own-time creation
is present in source and registered for the separate restricted writer; scoped lint/format and
runtime types pass. No tool was deployed, started or invoked and no time entries were created.
Next action: separately authorize the TOOL-041-001..009 test additions/execution and marked
pinned 7.0.2 state/permissions/Inspector/cleanup verification. TOOL-040's waiver authorizes this
coding continuation only and does not imply TOOL-041 acceptance.
