# prep-023-membership-batch-budgets: Budget documented membership batches

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-023-membership-batch-budgets |
| Assigned capability | Execute a valid one-to-ten membership batch within an explicit batch budget while preserving individual receipts |
| Type / access | Extend existing restricted membership writers; membership reads remain unchanged |
| Destructive effects | Existing add/update/delete membership effects only; planning performs none |
| Status | complete |
| Dependencies | [tool-033](tool-033-project-members-management.md) and [prep-019](prep-019-write-outcome-consistency.md), accepted current paths in [prep-020](prep-020-current-catalog-acceptance.md) |
| Related tasks | Existing prep-015 read-budget implementation; prep-016/017/018 infrastructure; [dashboard](../index.md) |
| Target Redmine version | 7.0.2; tested functional scope accepted |
| Last updated | 2026-10-07, Codex |
| Progress summary | Accepted: 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed |
| Next action | None in this assignment; retain regression coverage for future changes |

## 2. Discovery and evidence

`MembershipBatch.items` accepts one to ten items. `ProjectMembershipService.manage` creates a
single `ReadBudget` from the reader policy: 30 physical requests, 10 MiB of GET response bytes and
a 90-second cooperative deadline. Physical writes also consume request permits. Preflight,
permission refresh, target rechecks and read-back share these counters.

A source-derived example with an administrator profile, ten absent target memberships, available
user membership expansions and small responses needs approximately 22 preflight calls plus five
calls per executed add: 72 total. This is a modeled path, not a measured production workload.
Native denial, larger inventories, roles and response sizes can require different work.

| Source | Inspected | Evidence / limitation |
|---|---|---|
| `features/projects/membership_models.py`, `membership_service.py` | 2026-10-07 | Ten-item contract; whole-batch preflight; per-item refresh and shared reader budget |
| `integrations/redmine/project_memberships.py`, `transport.py` | 2026-10-07 | Inventory/read-back calls and charging of every physical request |
| `common/read_budget.py`, `config.py`, `bootstrap.py` | 2026-10-07 | Reader defaults and budget construction |
| [tool-033](tool-033-project-members-management.md), [current ledger](../../testing/evidence/current-catalog-acceptance.md) | 2026-10-07 | Existing native permissions, side effects, read-back and receipt acceptance remain authoritative |
| [Redmine membership API](https://www.redmine.org/projects/redmine/wiki/Rest_Memberships) | Existing task reference; not newly fetched | No new native API or permission assumption; use TOOL-033-011 evidence |
| `deploy/compose.test.yaml` | 2026-10-07 | Pinned 7.0.2 target; no live command executed |

Clean planning baseline: `36ff5f0`. Repository/workflow rules and historical acceptance gaps apply.

| Decision | Resolution | Blocking? |
|---|---|---|
| DEC-001 | Add a dedicated batch policy; keep reader defaults unchanged | No |
| DEC-002 | One counter scope per entire write batch, never a fresh budget per item | No |
| DEC-003 | Preserve per-item permission/target refresh; optimize only request-local preflight reuse | No |
| DEC-004 | Deadline stops new dispatches; no outer cancellation that erases accepted receipts | No |

## 3. Requirements

| ID | Required behavior | Constraint |
|---|---|---|
| REQ-001 | Small valid batches through ten items finish under batch defaults in the defined ordinary-manager fixture | Not a guarantee for arbitrary role counts, inventories, latency or access changes |
| REQ-002 | Requests, aggregate GET bytes and new dispatches remain bounded per batch | Physical mutation requests count; mutation responses retain existing per-response byte limits |
| REQ-003 | Whole-batch preflight fails without writes; execution rechecks current permissions and targets | No cross-caller cache, skip of native authorization or parallel writes |
| REQ-004 | Budget/transport failures preserve prior accepted or uncertain receipts and stop appropriately | No automatic retry or rollback |
| REQ-005 | Batch policy is configurable and distinct from normal readers | Existing reader concurrency/page/deadline settings stay effective |

Out of scope: more than ten items, transactions, concurrency, new member permissions, generic
writer operation budgets, changes to native protected-role/inheritance behavior or `extra_fields`.

## 4. Public contract and technical specification

| Area | Decision |
|---|---|
| Operations / routes | `add_project_members` POST, `update_project_members` PUT, `delete_project_members` DELETE at `/api/v1/projects/memberships/batch` |
| Inputs | Existing 1..10 typed items, unique targets/roles, positive IDs and null/omission rules |
| Auth | Existing reader isolation, separate writer, admitted caller, operation ceiling and native manage-members checks |
| Outputs | Existing `phase`, ordered per-item outcome/error/verification/observations |
| Native mapping | Existing project/user/membership/role reads and one native mutation per item |

New settings, all positive and finite where applicable:

| Environment setting | Default | Exact meaning |
|---|---|---|
| `REDMINE_MEMBERSHIP_BATCH_MAX_REQUESTS` | 300 | All physical preflight, execution, mutation and read-back requests in one write batch |
| `REDMINE_MEMBERSHIP_BATCH_MAX_READ_BYTES` | 31457280 (30 MiB) | Sum of consumed GET response bytes in that scope |
| `REDMINE_MEMBERSHIP_BATCH_DEADLINE_SECONDS` | 300 | Cooperative deadline checked before dispatch and while consuming read responses |

Per-request timeout/response limits and the shared transport semaphore remain unchanged. An
in-flight mutation may complete within its existing request deadline after the cooperative batch
deadline; do not describe 300 seconds as a hard wall-clock cancellation bound. External client or
shutdown cancellation still propagates and requires reconciliation; returned receipts are only
promised when a response can be delivered.

Inject a batch-specific policy through bootstrap without loading configuration in the service.
Use one context token with unconditional restoration. Retain existing error codes and batch-stop
rules. Reader routes continue using the existing reader policy. Preflight may deduplicate project
proofs and identical user evidence within the current preflight only; discard reused evidence
before execution. Refresh caller roles and actual targets before every mutation.

The ten-item acceptance fixture uses a non-admin manager, one readable necessary role per
selected project, direct user memberships, complete native expansions/inventories no larger than
one page, small response bodies and prompt responses. Cover each of add/update/delete separately.
Inventories or budgets that cannot complete still return the documented partial/not-executed
results; no claim of unconditional ten-item completion is made.

| Scenario | REST / MCP result |
|---|---|
| Invalid item, duplicate, unknown role or failed preflight | Existing validation/error or `preflight_failed`; zero writes |
| Request/GET-byte/deadline exhaustion during execution | Preserve completed receipts; reject or leave later items not executed under existing rules |
| Received mutation 5xx / dispatched timeout | Item uncertain; stop later execution; reconcile before retry |
| Read-back failure after accepted write | Acceptance retained; verification unavailable and safe error; stop when existing policy requires |
| Native permission change | Rechecked and enforced; no use of stale preflight grants |

Native deletion may affect descendants and assignment defaults. No idempotency, rollback or
history restoration is introduced. Later live checks require an owned writer, disposable
projects/users/memberships and ownership-checked cleanup following tool-033. Specification is
decision-complete; default policy tuning beyond these values is a later explicit change.

## 5. Implementation plan

| Step | Concrete change | Files/components |
|---|---|---|
| 1 | Add and validate dedicated batch settings | `config.py`, `.env.example` |
| 2 | Construct/inject one batch policy separately from reader policy | `bootstrap.py`, `membership_service.py` |
| 3 | Deduplicate bounded preflight proofs without retaining stale execution evidence | Membership service/ports/gateway only as needed |
| 4 | Preserve charging, context cleanup, receipt classification and stop behavior | `common/read_budget.py`, transport/write gateways only if required |
| 5 | Document exact budget meanings, defaults and partial completion | Configuration/tool reference/changelog/task/dashboard |
| 6 | Hand off fake/ASGI/SDK and disposable native fixture work | Separate verification assignment |

No dependency or lockfile change. Do not broaden reader limits or weaken role refresh to make a
test pass. Code changes must fit router -> service -> port -> gateway.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | Defined manager fixture executes batches of 1, 2 and 10 | All eligible items dispatch once and return expected native observations |
| AC-002 | Tiny request/byte/deadline caps are configured | Bounded rejection occurs at the documented stage; contexts restore |
| AC-003 | One preflight item fails or caller permissions change | Zero preflight writes or fresh execution denial; no stale-grant bypass |
| AC-004 | Accepted/uncertain write is followed by exhaustion/read failure | Prior receipt remains accurate; later items stop |
| AC-005 | Reader and batch settings differ | Reader caps remain unchanged; invalid batch settings fail configuration |

| Requirement | Criterion | Scenario | Evidence / result |
|---|---|---|---|
| REQ-001 | AC-001 | BATCH-023-001/006 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |
| REQ-002 | AC-002 | BATCH-023-002 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |
| REQ-003 | AC-003 | BATCH-023-003 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |
| REQ-004 | AC-004 | BATCH-023-004 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |
| REQ-005 | AC-005 | BATCH-023-005 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |

## 7. Test plan and execution record

The user explicitly authorized testing for prep-022 through prep-026 on 2026-10-07.
See [the verification record](../../testing/evidence/prep-022-026-testing.md) for executable coverage, corrections
and current results. Earlier coding-only prohibitions apply to that historical assignment.

| Scenario | Layer / setup | Observable assertion |
|---|---|---|
| BATCH-023-001 | Offline fake ports and MockTransport through REST/SDK | Each action at 1/2/10 items; count actual physical calls and independent results |
| BATCH-023-002 | Offline low request/GET-byte caps and controlled deadlines | No dispatch after exhaustion; no counter reset per item or leaked context |
| BATCH-023-003 | Offline invalid last item; self-revocation/changed target | Preflight has zero writes; execution rereads permissions/targets |
| BATCH-023-004 | Offline 204/201 followed by failed read-back; 500/timeout | Accepted/uncertain receipts survive; no second mutation or rollback |
| BATCH-023-005 | Offline settings and concurrent reader/batch calls | Defaults/custom/invalid settings; reader budget and caller isolation unchanged |
| BATCH-023-006 | Authorized owned 7.0.2 and Inspector | Ten-item ordinary-manager add/update/delete; compare native role/inheritance/assignment state and clean owned fixtures |

Future Git Bash procedures: `bash scripts/check.sh`, explicitly selected membership unit and
integration scenarios, then opt-in owned live tests and Inspector after authorization. Include
large/changed inventories and cancellation in offline fault cases; no production load benchmark.

| Evidence | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-023-001 | Read-only source inspection on 2026-10-07 | Default mismatch modeled; no measured/tested call count | Planning only |
| EVID-023-002 | Authorized offline, static and owned live/Inspector verification | 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed; [record](../../testing/evidence/prep-022-026-testing.md) | Passed |

Existing passing suites do not accept the new defaults. No setup/reset or mutation ran in planning.

## 8. Implementation and review record

Implemented on 2026-10-07 from clean HEAD `7310cb9`:

- Added positive batch request/GET-byte settings and a positive finite cooperative deadline.
  Shared default policy values keep direct service construction and Settings consistent.
- Bootstrap injects the dedicated policy. Normal readers retain their existing policy.
  The existing single batch context, unconditional reset, physical request charging and
  GET-only byte accounting are retained; no outer mutation cancellation was added.
- Preflight reuses successful project/user proofs using local sets. Execution passes no
  reuse sets, refreshes caller permissions and obtains current target evidence per item.
  Failed proofs are never cached as successes. Role validation and whole-batch failure remain.
- Documented settings, receipt boundaries and runtime limitations in configuration, tool
  reference and changelog. Also forwarded the new settings to the writer in
  `deploy/compose.yaml`: this necessary configuration wiring extends the listed file scope
  without changing the contract. No testing infrastructure, dependencies or tests changed.
- `uv run --frozen --no-sync ruff check .`: passed.
- `uv run --frozen --no-sync ruff format --check .`: 261 files already formatted.
- `uv run --frozen --no-sync mypy src`: passed, 121 source files.
- `git diff --check`: passed.
- Diff review confirms unchanged mutation/read-back classification, sequential writes,
  stop rules, caller isolation and external cancellation. No runtime behavior was exercised.

Handoff BATCH-023-001..005 to an authorized offline assignment: add/update/delete at
1/2/10 items, tiny budgets, cancellation/context restoration, stale permission/target
changes, prior accepted receipts and concurrent reader isolation. BATCH-023-006 needs
the owned Redmine 7.0.2 writer, non-admin manager, small complete inventories and disposable
memberships; verify native roles/inheritance/assignment effects and ownership-checked cleanup.
Startup and Inspector remain pending, as does EVID-023-002. No historical gap is closed.

## 9. Coding-stage handoff (superseded by section 10)

- [x] Dedicated settings/policy implemented and documented.
- [ ] Defined ten-item fixtures and bounded failure cases pass.
- [ ] Role refresh, receipts, reader limits and context restoration accepted.
- [ ] Owned native state and cleanup verified after explicit authorization.
- [x] Final diff/task/dashboard synchronized.

Final status: blocked for acceptance. **Implementation finished; testing pending.**
Next action: confirm the implementation commit, then separately authorize BATCH-023-001..006.
Configuration rollout and live verification have not been performed.


## 10. Authorized testing record (2026-10-07)

The user assigned testing for all five preparation tasks. Coverage, runtime corrections,
owned fixture cleanup and final execution results are recorded in
[Preparation regression testing](../../testing/evidence/prep-022-026-testing.md). Acceptance passed: 1395 offline tests, 23 owned live tests including Inspector,
Ruff/mypy/architecture/diff checks and owned cleanup. All mapped acceptance criteria
passed within the selected functional scope. This section
supersedes the coding-stage testing handoff without removing its historical decisions.
