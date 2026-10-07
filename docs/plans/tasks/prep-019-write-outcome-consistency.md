# prep-019-write-outcome-consistency: Preserve uncertainty across every writer

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-019-write-outcome-consistency |
| Assigned capability | Let callers reconcile a mutation when an HTTP server error does not prove that it failed |
| Type / access | Shared prerequisite; affects existing writes, adds no tool |
| Destructive effects | Implementation does not mutate Redmine; later live verification creates only disposable owned state |
| Status | complete - implementation and assigned acceptance passed |
| Dependencies | Existing writer/auth implementations; [prep-016](prep-016-unit-testing.md)/[prep-017](prep-017-offline-integration-testing.md) offline baseline; [prep-018](prep-018-live-e2e-testing.md) owned fixture and live-verification infrastructure |
| Related tasks | [Dashboard](../index.md); [acceptance follow-up](prep-020-current-catalog-acceptance.md) |
| Target Redmine version | Pinned 7.0.2; owned commit/HTTP-500 reconciliation and cleanup pass |
| Last updated | 2026-10-07, Codex |
| Progress summary | Uniform JSON/binary policy implemented; offline regression, transport checks, owned 7.0.2 commit/HTTP-500 reconciliation and cleanup, Inspector, and static checks pass |
| Next action | Proceed to prep-020 acceptance-ledger work in its own assignment |

## 2. Discovery and evidence

At the planning baseline, shared `integrations/redmine/write.py` defaulted
`uncertain_server_errors` to false. Membership mutations opted in, but issue/version creation
and binary upload did not. A received 500/503/504 could therefore become a conventional
application error after a mutation was sent. The coding record below documents the correction.
The review found a classification risk, not a reproduced live defect or proof of a commit.

The baseline is 15 registered write operations in `auth/policy.py`, separate reader/writer
deployment gates, single dispatch, bounded transport, and independent read-back verification.
The working tree was clean at planning start. Preserve unrelated changes during execution.

| Source or versioned evidence | Reviewed | Version | Finding / limitation |
|---|---|---|---|
| `src/redmine_mcp/integrations/redmine/write.py` and `client.py` | 2026-10-07 | Current repository | Shared status mapping and mutation receipts inspected; no request executed |
| `issue_creations.py`, `project_versions.py`, `project_memberships.py` | 2026-10-07 | Current repository | Different server-error classification across callers |
| `features/projects/membership_models.py` and `project_memberships.py` | 2026-10-07 | Current repository | Membership results are per item; uncertain items return before read-back |
| `tests/e2e/conftest.py` and `test_live_acceptance.py::test_uncertain_create_reconciles_real_state_without_retry` | 2026-10-07 | prep-018 owned 7.0.2 fixture | Existing ownership, native-ID capture, reconciliation, and cleanup pattern inspected; tests not run |
| `deploy/compose.test.yaml` | 2026-10-07 | Redmine 7.0.2-bookworm, digest pinned | Configuration evidence only |
| [Tool reference](../../tool-reference.md) | 2026-10-07 | Current contract | Existing uncertainty/read-back semantics; no new native endpoint or permission |

No new upstream permission or Redmine API behavior is assumed. The change is a conservative
client-side interpretation of received HTTP 5xx, not a guarantee about database transaction state.

| Decision | Resolution | Blocking? |
|---|---|---|
| DEC-001 | Every mutation path, including binary upload, classifies received HTTP 500-599 as uncertain after dispatch | No |
| DEC-002 | Preserve existing deterministic 4xx errors, accepted response handling, read-back, and no-retry policy | No |
| DEC-003 | Coding excludes tests/startup/live calls unless the future assignment explicitly includes verification | No |
| DEC-004 | Preserve individual result envelopes and membership `phase`/`results[]`; do not add a common top-level outcome or acceptance field | No |
| DEC-005 | Only mutation responses use the new 5xx policy; authentication/preflight/read-back GETs retain `RedmineClient` error mapping | No |
| DEC-006 | Preserve existing per-adapter read-back: membership uncertain items return without observation, and create/upload results without a reliable new ID do not invent a lookup | No |

## 3. Requirements

In scope: shared write transport, affected receipt adapters, existing tool descriptions and
configuration guidance. Out of scope: read error-policy changes, retry queues, idempotency
stores, new tools, new permissions, or production deployment.

| ID | Required observable behavior | Constraint |
|---|---|---|
| REQ-001 | All 15 writers preserve uncertainty for received HTTP 5xx after mutation dispatch | Includes JSON and binary paths |
| REQ-002 | Individual results carry `outcome=uncertain`; membership batches carry `results[i].outcome=uncertain` for the dispatched item | Preserve existing models and batch phase; never infer rejection, acceptance, or a trustworthy new resource ID from 5xx |
| REQ-003 | Pre-dispatch denial/failure, authentication/preflight GET 5xx, native validation, and ordinary accepted responses retain their contract | Preserve `RedmineClient` read-error mapping, reader isolation, and caller authorization |
| REQ-004 | Preserve each adapter's existing read-back behavior and independent receipt/observation semantics | No new read-back for uncertain membership items, automatic retry, or rollback |
| REQ-005 | Documentation explains the intentional compatibility change and reconciliation | Record implementation and testing evidence separately |

Example: an issue-create POST is sent and receives HTTP 500. Return an uncertain receipt with
no fabricated issue ID; advise reconciliation using caller-visible state before any manual retry.
A permission denial before POST must still produce its existing error with zero mutations.

## 4. Public contract and technical specification

| Area | Decision |
|---|---|
| MCP / REST interface | All existing writer names, operation IDs, routes, inputs, and annotations remain stable |
| Inputs / mapping | Existing request models and exact native payloads; no added configuration flag |
| Outputs | Existing REST 200/MCP result envelopes: individual `outcome`, or membership `phase` plus per-item `results[i].outcome` |
| Authentication | Existing personal/pinned-key writer gates, operation ceiling, and resource checks |
| Upstream mapping | Single existing native mutation; classify HTTP 500-599 before general read-style status mapping |
| Acceptance fields | For received mutation 5xx, existing individual `upstream_accepted` fields remain null; membership has no such field and gains none |
| Pagination | N/A - shared mutation outcome policy |

Implement one common policy in `RedmineWriter`; remove or neutralize the per-caller opt-in so
no current mutation can silently opt out. Inspect every adapter in `WRITE_OPERATIONS`, including
`write_binary`, to ensure it translates an uncertain receipt without inventing state.
Preserve the native status only as safe internal receipt metadata, not an upstream error body.
Do not modify `integrations/redmine/client.py::raise_for_upstream_status` or `RedmineClient`
GET behavior to implement this mutation-only policy. Preserve the existing result models;
adapter translation changes must not
add response fields or change schemas.

### Individual and batch results

Individual tools retain their own models. New create/upload identifiers and upload tokens remain
unavailable after a received mutation 5xx. Known input target IDs on update/delete operations
remain present. Adapters that already read back a known target may report matched/mismatch
observations while keeping `outcome=uncertain` and `upstream_accepted=null`.

Example `create_issue` result after an HTTP 500 for a request containing project ID and subject:

```json
{
  "outcome": "uncertain",
  "upstream_accepted": null,
  "resource_id": null,
  "verification": "unavailable",
  "field_verification": {"project_id": "unavailable", "subject": "unavailable"},
  "observed_issue": null
}
```

Membership tools retain `MembershipBatchResult(phase, results)`. For an execution-stage 5xx,
`phase` remains `executed`; the dispatched item is uncertain with
`error.code=write_outcome_uncertain`, `verification=unavailable`, and no new read-back.
Keep its known target IDs and any existing observation fields unchanged. Accepted peers retain
their results; later items stay `not_executed` with `batch_not_executed`. Do not add top-level
`outcome`, `upstream_accepted`, or a new batch-wide acceptance value.

Illustrative update-membership response fragment; other unchanged item fields are omitted here:

```json
{
  "phase": "executed",
  "results": [
    {"index": 0, "project_id": 10, "membership_id": 101,
     "outcome": "accepted", "verification": "matched", "error": null},
    {"index": 1, "project_id": 10, "membership_id": 102,
     "outcome": "uncertain", "verification": "unavailable",
     "error": {"code": "write_outcome_uncertain",
               "message": "Reconcile before any further attempt", "status": null}},
    {"index": 2, "project_id": 10, "membership_id": 103,
     "outcome": "not_executed", "verification": "unavailable",
     "error": {"code": "batch_not_executed",
               "message": "Shared execution failure stopped this batch", "status": null}}
  ]
}
```

| Scenario | REST / MCP behavior | Reconciliation |
|---|---|---|
| Invalid input, missing key, denied writer/project | Existing sanitized 4xx/error envelope; no mutation | Correct input/access |
| Native 400/422, 401/403/404/429 | Existing deterministic status mapping | Existing policy; no automatic retry |
| Admission/pool failure before dispatch | Existing sanitized busy/unavailable error | No dispatched mutation claimed |
| Authentication/initial preflight GET receives HTTP 5xx before the first mutation | Existing sanitized read error or existing batch preflight/item error; zero mutations | Preserve existing GET mapping and batch stopping rules |
| Membership execution recheck GET receives HTTP 5xx after earlier items executed | Preserve earlier receipts and current read-error/stopping behavior; no mutation for the affected or later items | Do not replace earlier accepted results with a blanket preflight failure |
| Received mutation HTTP 500-599 after dispatch | Individual `outcome=uncertain` or batch `results[i].outcome=uncertain` | Inspect visible state before a manual retry |
| Timeout/transport failure after possible dispatch | Existing uncertain result | Preserve current reconciliation |
| Accepted response followed by read-back GET 5xx | Preserve accepted receipt and existing unavailable-verification/error fields | Do not label the write failed or apply the mutation policy to GET |
| Uncertain response followed by matched read-back on an adapter that already observes known targets | Preserve uncertainty and independent observation | Observation does not establish invocation ownership |
| Uncertain membership item or create/upload without a reliable new ID | Preserve current return without read-back; membership stops later items | Caller reconciles separately; no speculative resource lookup |

There is no transaction, retry, or rollback guarantee. Membership batches retain already accepted
items and stop later dispatch after uncertainty. Live cleanup may leave owned journal history;
delete only task-owned resources and record any cleanup failure.

Specification exit: the shared policy is decided; no native permission or endpoint is added.

## 5. Implementation plan

| Step | Change / owner | Files or components | Stage |
|---|---|---|---|
| 1 | Inventory all 15 writer paths and current result handling | `auth/policy.py`, gateway adapters | Read-only coding preparation |
| 2 | Apply uniform received-5xx classification | `integrations/redmine/write.py`, membership opt-in call sites | Coding |
| 3 | Preserve individual/per-item receipt translation and existing read-back decisions | Existing write gateways; result schemas unchanged | Coding |
| 4 | Explain changed 5xx behavior and reconciliation | `docs/tool-reference.md`, `docs/configuration.md`, `CHANGELOG.md` | Coding |
| 5 | Run assigned Ruff/mypy/format checks and record exact results | Existing static tooling | Coding, when assigned |
| 6 | Add/run focused transport, REST/MCP, and state scenarios | Existing test layers; scenarios below | Separate authorized testing |

No dependency upgrade, lockfile change, or new tool is planned. Do not modify tests in a
coding-only assignment. Synchronize this task and the dashboard after each stage.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | Any registered JSON or binary mutation receives 500/503/504 | One mutation dispatch; individual outcome or dispatched membership item uncertain; response closed |
| AC-002 | Permission/input failure, native deterministic rejection, or authentication/initial preflight GET 5xx | Existing sanitized contract and batch semantics; failure before the first mutation dispatches zero mutations |
| AC-003 | Accepted mutation encounters read-back GET 5xx, or an uncertain known-target adapter obtains a matching observation | Preserve accepted/uncertain receipt independently; existing GET mapping and result fields unchanged |
| AC-004 | Membership batch encounters uncertain item | Phase executed; accepted peers retained; uncertain item has no read-back; later items not executed |
| AC-005 | Reader deployment and existing callers are exercised | Catalog, schemas, auth boundaries, and unrelated reads remain compatible |
| AC-006 | Guidance and execution record are reviewed | 5xx change, reconciliation, and actual limitations are explicit |
| AC-007 | Owned real issue creation receives a synthetic HTTP 500 after native 201 | Exactly one native issue; no returned created ID; explicit reconciliation by owned ID/unique subject and isolated cleanup |

| Requirement | Criteria | Scenario / evidence | Result |
|---|---|---|---|
| REQ-001 | AC-001, AC-004, AC-007 | STAB-019-001/004/006 | Pending |
| REQ-002 | AC-001, AC-003, AC-004, AC-007 | STAB-019-001/003/004/006 | Pending |
| REQ-003 | AC-002, AC-003, AC-005 | STAB-019-002/003/005/007 | Pending |
| REQ-004 | AC-003, AC-004, AC-007 | STAB-019-003/004/006 | Pending |
| REQ-005 | AC-006 | Document review and dated execution record | Pending |

## 7. Test plan and execution record

| Scenario | Layer | Setup / expected observation |
|---|---|---|
| STAB-019-001 | Offline transport + parameterized REST/MCP | All 15 writers; native mutation 500/503/504; one mutation dispatch, correct individual/per-item outcome, unchanged schema, closed response, no upstream error body exposure |
| STAB-019-002 | Offline | Pre-dispatch admission/permission failure and native 400/401/403/404/422/429; previous status behavior preserved |
| STAB-019-003 | Offline stateful gateway + REST/MCP | Successful mutation then read-back GET 500/503/504 preserves acceptance and unavailable verification; uncertain known-target update/delete with matched read-back stays uncertain; create/upload without reliable new ID retains no read-back |
| STAB-019-004 | Offline batch + REST/MCP | All preflight passes; accepted first item, mutation 5xx on second, unexecuted third; assert phase/results schema, error codes, zero read-back for uncertain item and zero later mutation dispatches |
| STAB-019-005 | Offline REST/MCP | Reader denies writes; configured writer schemas, discovery, inputs, and ordinary success unchanged |
| STAB-019-006 | Opt-in owned 7.0.2 | Procedure below: one owned native POST returns 201, application receives synthetic HTTP 500, uncertain result has no created ID, exactly one native issue reconciled and cleaned up |
| STAB-019-007 | Offline transport + REST/MCP | Authentication or initial target/whole-batch preflight GET 500/503/504: preserve current error shape, zero mutations, no fabricated uncertain receipt. Separately fail an execution recheck GET after an accepted peer: retain that receipt and current stopping rules, with zero affected/later mutation dispatches |

Only run these in an explicit testing assignment. Reuse MockTransport/ASGI/MCP SDK helpers;
offline fixtures must not load dotenv or perform real network dispatch. Live injection is owned
test tooling, not a production proxy or fault against the shared Redmine deployment.

### Owned live procedure for STAB-019-006

Implement this scenario only in a separately authorized testing assignment. Its owner is
`tests/e2e/test_live_acceptance.py`, reusing the `live` fixture in `tests/e2e/conftest.py` and
the ownership/cleanup pattern of `test_uncertain_create_reconciles_real_state_without_retry`.
Keep that existing timeout scenario intact; add a dedicated received-HTTP-500 case.

1. Require prep-018's isolated `redmine-mcp-e2e` environment at `127.0.0.1:3001`, its pinned
   image, synthetic markers, volume labels, private fixture manifest, and `assert_ownership(live)`.
   Use the owned project `live.manifest["projects"]["a"]` and ordinary caller `a` through
   `live.client(user="a", writer=True)`. If any prerequisite is missing, stop with a blocker;
   do not reset or alter the shared synthetic deployment to obtain it.
2. Generate a unique task-owned subject. Scope a temporary transport interception to the exact
   native origin, `POST /issues.json`, and that request's project/subject. Authentication,
   preflight, reconciliation reads, and unrelated requests must pass through unchanged.
3. Forward the targeted POST once using the original transport. Consume its native response;
   require HTTP 201 and a valid created issue ID, register that ID in `live.created_issues`
   for cleanup, and close the native response. Keep captured native metadata private.
4. Return a synthetic HTTP 500 response bound to the original request instead of the native 201.
   Do not inject a timeout, send another mutation, or return the captured native ID/body to the
   application. Assert REST 200 with uncertain outcome, null `upstream_accepted`/`resource_id`,
   unavailable verification, and exactly one targeted native dispatch.
5. Restore the original transport immediately after the application invocation, including on
   failure, using a scoped monkeypatch context or equivalent `finally` restoration. Through
   native reads, reconcile the captured ID's project/subject and exactly one unique-subject match
   in the complete bounded owned-project issue inventory. Do not treat an incomplete page as
   uniqueness evidence; if inventory cannot be collected within limits, record a blocker.
6. Always call `live.cleanup()` in the outer `finally` after restoring transport. Delete only
   registered task-owned issues. If creation succeeded but trustworthy ID capture failed,
   perform explicit owned project/unique-subject reconciliation before any cleanup or retry;
   unresolved ownership remains a cleanup blocker. Record redacted cleanup evidence under
   ignored `.local/testing-e2e/`; do not overwrite unrelated evidence or expose credentials.

Inspector verification in EVID-019-003 is a separate discovery/schema/read-only compatibility
check against an owned localhost application. Use registered owned IDs for any reads; do not
repeat the fault-injected create or other mutations merely to exercise Inspector.

| Evidence | Planned procedure | Actual result | Status |
|---|---|---|---|
| EVID-019-001 | Git Bash: `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .`; `uv run --frozen --no-sync mypy src` | Lint passes; 250 files already formatted; mypy succeeds for 120 source files | Passed, 2026-10-07 |
| EVID-019-002 | Authorized focused cases, then `uv run --frozen --no-sync pytest -q` | Final full offline regression: 1035 passed, one existing dependency warning, 300.17 seconds. Individual-writer matrix: 72 passed; supplemental GET/delete cases: 12 passed; transport/admission tests: 22 passed (including two admission cases added after full-run collection) | Passed, 2026-10-07 |
| EVID-019-003 | `uv run --frozen --no-sync pytest tests/e2e/test_live_acceptance.py::test_received_500_after_real_commit_is_uncertain_without_retry --run-e2e -q`; `uv run --frozen --no-sync python scripts/verify-write-outcome-inspector.py` | Owned 7.0.2 scenario: 1 passed; native 201 replaced with HTTP 500, one dispatch, null created ID, complete inventory reconciliation and cleanup pass. Inspector 2.8.0: catalog/writer input schemas and one read call pass; zero Inspector mutation calls; localhost application stopped | Passed, 2026-10-07 |
| EVID-019-004 | Git Bash: `bash scripts/doctor.sh` | Required prerequisites ready; existing environment used, no dependencies installed | Passed, 2026-10-07 |
| EVID-019-005 | Git Bash: `git diff --check` and manual scoped diff review | No whitespace errors; only Git line-ending normalization notices. Runtime/docs/test diff reviewed; no dependency, GET mapping, model, or authorization changes | Passed, 2026-10-07 |

## 8. Implementation and review record

### Original planning record

- Changes made: planning document and dashboard only.
- Code, tests, startup, Inspector, and live checks: not performed.
- Source review establishes the policy inconsistency; it does not reproduce a committed 5xx.
- Future review must inspect transport cleanup, all adapters, auth compatibility, and log secrecy.

### Planning correction and re-review, 2026-10-07

The initial review verdict was **changes required**. Preserve these finding IDs and their
original severity; their resolution below concerns plan quality, not runtime acceptance.

| Finding | Severity | Original issue / impact | Correction and current resolution |
|---|---|---|---|
| R019-001 | major | A uniform outcome description could change membership batch schemas or add unwanted read-back | Resolved in planning: DEC-004/006, REQ-002/004, section 4 JSON examples, AC-001/003/004, and STAB-019-001/003/004 preserve individual/per-item contracts and adapter-specific observation |
| R019-002 | minor | Verification did not explicitly distinguish authentication/preflight, mutation, and read-back 5xx | Resolved in planning: DEC-005, REQ-003, section 4 stage-specific error table, AC-002/003, and STAB-019-003/007 retain GET mapping and zero mutations before failed preflight |
| R019-003 | minor | Required live case lacked explicit infrastructure dependency and a concrete injection/cleanup handoff | Resolved in planning: prep-018 dependency, named fixture/scenario owner, six-step STAB-019-006 procedure, and AC-007 identify target, native-ID capture, restoration, reconciliation, and cleanup |

Correction/review cycle 1: manually compared the revised specification with current result
models, membership early-return behavior, `RedmineClient` mapping, prep-018 fixture guards, and
the existing live timeout procedure. All nine task sections remain present; dependencies and
the dashboard match; no new native permission or endpoint claim is introduced.

Re-review verdict: **ready for the coding stage**. No unresolved planning findings remain in
this reviewed scope. No runtime implementation, automated checks, startup, Inspector, or live
verification was performed. EVID-019-001..003 and completion items remain pending.

### Coding assignment, 2026-10-07

The user explicitly assigned prep-019 implementation. The redmine-implement-task skill limits
this stage to runtime code/documentation, installed Ruff/format/mypy checks, and diff inspection.
No tests, fixtures, test dependencies, startup, Inspector, live calls, build, or deployment were
created, modified, or executed. Existing review corrections and future scenarios remain intact.

Working-tree baseline: `docs/plans/index.md` was already modified and the stabilization plans
were untracked documents from prior assignments, including an operational draft later removed
at the user's request. Preserve the retained plans and unrelated
content; this stage changes only prep-019's record/dashboard row plus its runtime/public docs.

Changes made:

- `integrations/redmine/write.py`: remove `uncertain_server_errors` from both internal write
  interfaces and classify `response.is_server_error` before general status mapping. The installed
  HTTPX predicate covers 500-599. Both JSON mutations and binary uploads use this same branch.
  It returns an uncertain receipt without consuming the error body and retains response closure
  in the existing `finally` block. No new retry, configuration setting, or accepted-status rule.
- `integrations/redmine/project_memberships.py`: remove both opt-in keyword arguments. Existing
  uncertain-item errors, early return without read-back, batch stopping, and result shapes remain.
- `docs/tool-reference.md`, `docs/configuration.md`, `CHANGELOG.md`: document the compatibility
  change from ordinary upstream errors to uncertain result envelopes for received mutation 5xx;
  distinguish GET stages, individual receipts, and membership batches. Acceptance remains pending.
- No edits to `client.py`, authorization, routers, models, MCP catalog, dependencies, or lockfile.

All 15 registered writer paths were inspected in source. Their existing adapters already map
the shared receipt correctly, so no additional gateway/model edits were necessary:

| Operations | Existing receipt/read-back handling retained |
|---|---|
| upload_attachment, create_issue, create_project_version, create_issue_relation | Uncertain receipt has no new trustworthy ID/token; return without speculative read-back |
| add_project_file, update_attachment, delete_attachment | Known attachment/input identity retained; any existing observation is independent of the uncertain receipt |
| update_issue, update_issue_note, delete_issue_relation | Known issue/journal/relation identity retained; field/absence observations do not rewrite the receipt |
| add_issue_watcher, remove_issue_watcher | Known issue/principal identity retained; membership observation remains independent |
| add_project_members, update_project_members, delete_project_members | Per-item uncertainty and unavailable verification; no uncertain-item read-back; accepted peers preserved and later dispatch stopped |

Static results: EVID-019-001 and prerequisite doctor EVID-019-004 pass. No pre-existing or
introduced lint/format/type failure was reported. Runtime regressions have not been assessed.
Final coding diff inspection confirms the change is centralized, schemas and caller gates are
preserved, and no test files or credentials were altered. EVID-019-005 records no whitespace
errors; Git reports only the repository's CRLF-to-LF normalization notices. Existing planning
documents remain untracked as at assignment start; they were not staged or committed.

Plan deviations: none. Removing the internal opt-in is the specified common policy. Existing
adapters suffice for the prescribed result translation. No new package/build work is required
by a dependency or packaging change; no build was run as runtime-verification substitution.

Testing handoff:

- Add STAB-019-001/002/003/005/007 transport and REST/MCP cases to the existing offline layers,
  including `tests/integration/test_current_tools.py` and the existing shared synthetic helpers.
  Parameterize all 15 writers for mutation 500/503/504 and verify input/GET/ordinary success
  behavior, response closure, sanitized output, one mutation dispatch, and unchanged schemas.
- Extend `tests/unit/test_project_members_gateway.py` and
  `tests/integration/test_project_members.py` for STAB-019-004/007: per-item uncertain receipt,
  no read-back, preserved accepted peers, stopped later writes, and execution-recheck failures.
- Keep current tests and valid historical evidence intact. Do not weaken deterministic 4xx
  assertions; distinguish any obsolete mutation-5xx expectation from GET error expectations.
- Add STAB-019-006 separately in `tests/e2e/test_live_acceptance.py` using the guarded `live`
  fixture and the six-step owned procedure above; retain the existing timeout scenario. Capture
  task-owned native IDs privately, restore transport, reconcile exactly one issue, and clean up.
- Complete the authorized Inspector discovery/schema/read compatibility procedure, then update
  EVID-019-002/003, acceptance criteria, and task/dashboard from actual results. Do not continue
  dependent prep-020 verification until prep-019's required acceptance evidence is established.

Coding outcome: **implementation finished; testing pending**. Status is blocked only on the
outstanding separately authorized offline/live acceptance work, not an unfinished code change.

### Authorized testing assignment, 2026-10-07

The user's instruction, "continue for testing", authorizes this separate testing stage.
Testing remains limited to prep-019; no broader prep-020 acceptance, deployment, commit,
dependency installation, or shared-environment reset was performed.

Changes and scenario ownership:

- `tests/unit/test_write_server_errors.py`: STAB-019-001/002 verifies all JSON mutation
  methods and binary upload at 500/503/504/599. Unreadable error streams prove that bodies
  are not consumed, responses close, payloads are absent, and exactly one send occurs.
  Admission/pool failures preserve sanitized busy/unavailable errors rather than uncertainty.
- `tests/integration/test_current_tools.py`: STAB-019-001/003/007 covers all 12 individual
  writers at 500/503/504 through both REST and MCP, creation/upload ID/token absence,
  initial authentication/preflight GET failures, accepted writes with failed read-back,
  and committed update/delete observations that never promote uncertain receipts.
- `tests/integration/test_project_members.py`: STAB-019-001/003/004/007 covers the three
  batch writers through REST/MCP, accepted/uncertain/not-executed sequencing, absent uncertain
  item read-back, whole-batch preflight failures, accepted receipts after read-back failures,
  and execution recheck errors that preserve accepted peers and stop affected/later mutations.
- Existing reader, caller discovery, input/schema, permission, ordinary success, transport,
  and deterministic rejection tests remain the STAB-019-002/005 regression baseline.
  `test_project_versions.py` replaces its obsolete mutation-503 error expectation with
  explicit deterministic 429 mapping (REST 502, `upstream_rate_limited`); the new all-writer
  matrix separately verifies mutation 503 uncertainty. Other 4xx assertions remain intact.
- `tests/e2e/test_live_acceptance.py`: STAB-019-006 adds the received-500-after-real-commit
  scenario while preserving the existing timeout scenario. Owned origin/project/unique-subject
  interception forwards one native POST, captures a validated native ID, closes native 201,
  returns synthetic 500, restores transport, collects the complete bounded issue inventory,
  reconciles exactly one issue, and always runs owned cleanup. Failed native-ID capture has
  a unique-subject reconciliation fallback before cleanup.
- `scripts/verify-write-outcome-inspector.py`: owned writer application, complete current
  catalog, writer input schemas/annotations, and one `get_issue` call through pinned Inspector
  2.8.0. The script terminates its localhost server in `finally` and performs no mutation calls.

Test development found incorrect assertions, not additional runtime defects: existing create
results use `resource_id`; MCP SDK result validation refreshes caller discovery with GETs;
membership read-back failure already stops later items; native 429 maps to sanitized REST 502.
Assertions now distinguish caller/discovery reads from resource read-back. Intermediate failing
runs and an interrupted stale full run are retained privately; final results supersede them.
No additional runtime changes were needed during testing.

Private evidence uses `.local/prep-019-*.log` and unique run directories under
`.local/testing-e2e/prep-019/`. Each live run archives the previous cleanup record before
writing its own evidence; credentials/native IDs remain ignored. Ownership/image/volume/version
guards passed against prep-018's isolated 7.0.2 environment at `127.0.0.1:3001`.
Cleanup passed for both live executions; the disposable issues were deleted. Existing owned
journal history is not rolled back. This demonstrates the requested committed-write/received-500
case; it does not characterize every possible native server failure or complete prep-020.

The only test warning observed is the existing Pydantic schema-hook deprecation in a dependency.
Final offline regression results and the acceptance matrix are recorded at completion below.

## 9. Completion and handoff

| Acceptance | Actual evidence | Result |
|---|---|---|
| AC-001 / STAB-019-001 | All 15 writers at 500/503/504 through REST/MCP; JSON/binary error stream closure without consumption or retry, also 599 | Passed |
| AC-002 / STAB-019-002/007 | Existing input/permission/reader gates and deterministic 400/401/403/404/422/429; focused writer admission errors; initial authentication/target/batch preflight GET 5xx with zero mutations | Passed |
| AC-003 / STAB-019-003 | Accepted receipts survive read-back GET 5xx; committed update/delete observations retain uncertain receipts; new creation/upload IDs and token absent | Passed |
| AC-004 / STAB-019-004/007 | REST/MCP partial batch retains accepted peer, uncertain second item has no resource read-back, later item not executed; execution GET recheck preserves earlier receipts | Passed |
| AC-005 / STAB-019-005 | Full offline catalog/schema/caller/ordinary-success regressions; Inspector 2.8.0 catalog, writer input schemas/annotations, and read-only invocation | Passed |
| AC-006 | Public guidance, changelog, task evidence, dashboard, and final scoped diff reviewed; limitations recorded | Passed |
| AC-007 / STAB-019-006 | Owned pinned 7.0.2 native issue commit returns 201, caller receives synthetic 500; one dispatch, uncertain receipt, complete unique-subject reconciliation, disposable issue cleanup | Passed |

- [x] Uniform shared mutation policy implemented.
- [x] Every requirement has passing evidence, including all writer paths.
- [x] Required live resulting-state scenario and cleanup recorded.
- [x] Guidance, task, and dashboard synchronized.
- [x] Final runtime, test, and documentation diff and compatibility inspected.

Final status: **complete**. All AC-001..007 and STAB-019-001..007 have passing evidence.
Next action: prep-020's acceptance ledger and remaining current-catalog scenarios in a separate
assignment. This completion accepts prep-019's shared write-outcome correction; historical tool
acceptance gaps remain scoped to prep-020. No commit or deployment was performed.
