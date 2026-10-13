# prep-014-multi-user-writer-acceptance: Verify caller isolation and resulting write state

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../../configuration.md#separate-writer-deployment).

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-014-multi-user-writer-acceptance |
| Assigned capability | Establish evidence for personal-key writer access and caller-specific discovery |
| Type / access / destructive effects | Shared verification prerequisite / offline and opt-in synthetic writes / Task-owned fixture mutations only |
| Status | blocked |
| Dependencies | [prep-011](prep-011-multi-user-writer-auth.md), [prep-012](prep-012-project-resource-authorization.md), [prep-013](prep-013-caller-tool-discovery.md) implemented; existing [prep-002](prep-002-offline-tests.md) baseline and [prep-008](prep-008-synthetic-writer-verification.md) fixture guidance; separate testing authorization |
| Related tasks | [Roadmap](../multi-user-writer-authorization.md); [dashboard](../index.md); existing tool-020 through tool-030 and prep-009 |
| Target Redmine version | Pinned 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Predecessor code is implemented. Unrequested tests and acceptance tooling were removed following the user's correction; separately approved acceptance remains pending |
| Next action | Retain the coding handoff. Do not create or execute tests, Inspector checks, synthetic seeding or live verification without explicit separate user approval |

## 2. Discovery and evidence

Repository has a completed credential-free offline baseline; earlier writer tasks still have
pending permission/state evidence. Those records must remain separate from this acceptance.
Sources checked 2026-10-05: [testing roadmap](../../testing-roadmap.md), prep-002, prep-007/008,
prep-009, current dashboard, locked dependencies and synthetic Compose pin.
Exact permission limitations and authoritative upstream links are in the [roadmap evidence](../multi-user-writer-authorization.md#baseline-evidence-and-limitations).
No user-approved target acceptance is established for this change. Initial working tree was clean.

The user explicitly clarified that implementing prep-010 through prep-014 did not authorize
creating or running tests. The latest repository instructions require separate approval for unit
tests and other testing tools. This instruction takes precedence over this task's planned test
workflow. Historical runtime waivers remain history; do not infer testing or seeding approval from
the general implementation assignment.

## 3. Requirements

| ID | Required observable behavior |
|---|---|
| REQ-001 | Authentication, admission, forwarding, and stateful sessions isolate concurrent users |
| REQ-002 | Project/resource permissions and discovery agree with authoritative target behavior |
| REQ-003 | Role/key changes do not preserve stale local grants, and guessed tool calls cannot bypass checks |
| REQ-004 | Reader/pinned-key compatibility and write receipts remain correct |
| REQ-005 | Actual synthetic writes, denied writes, side effects, and cleanup are recorded truthfully |

Scope: separately assigned fixtures/tests, operational checks, evidence, and handoff. No new
public tools, production writes, CI/coverage threshold, automatic hook installation, or unrelated
data reset. No test implementation/execution occurs in this planning assignment.

## 4. Public contract and technical specification

N/A - no new API. This task verifies prep-011/012/013 and preserves existing operation contracts.
Inputs are fake offline settings plus authorized task-owned synthetic fixture identities and
resources. Output is dated, redacted evidence mapped to acceptance criteria, not returned key data.

### Fixture contract

Reuse the marked synthetic Redmine 7.0.2 environment and separate writer deployment. Before any
mutation verify environment marker, target pin and fixture ownership. Store credentials/manifests
only in ignored `.local/`; never print keys, tokens, payload secrets, or snapshots.

| Fixture | Needed contrast |
|---|---|
| Two ordinary personal-key users | Create/edit in A versus read-only in A; reverse or different rights in B |
| Own versus other author | Edit-own issue/note alternative, private journal visibility |
| Multiple/inherited roles and group-derived role | Preserve effective membership and alternate paths |
| Tracker-specific restrictions | Permission present in role JSON but denied for selected tracker |
| Public non-member project with built-in override | Missing membership cannot establish definitive denial |
| Explicit admin caller fixture | Own admin evidence does not bypass deployment/user admission |
| Closed/archived/module-disabled project | Role grant cannot override project/module state |
| Task-owned upload/files/issues/journals/relations/watchers | All eleven write operation contexts and state side effects |

Administrative fixture creation uses the separate seed/admin path, never the MCP application key.
Any role revocation, account lock, or key rotation affects only owned synthetic identities and
requires the verification assignment's mutation scope. Do not mutate an existing reader account.

### Failure and state contract

Confirm denied operations produce no dispatch when locally denied and no state change when denied
upstream. Observe known ignored-field/no-op behavior and read-back mismatch/unavailability without
turning an accepted write into a failed write. For post-dispatch timeout record uncertainty and
reconcile owned state before any manual retry. Do not use a write to probe permission discovery.

Cleanup removes only manifest-owned disposable resources through an authorized administrative
fixture path. Journal/mail/history effects may persist; document them instead of promising rollback.
Upload cleanup follows native retention and existing fixture rules, not an invented public delete
for an unattached object. Stop if the marker or ownership cannot be established; do not reset or
restore unrelated data merely to finish verification.

Specification exit: procedure is decision-complete; exact scenario payloads use prep-010's reviewed
matrix and predecessor implementations. Execution is pending separate authorization.

## 5. Implementation plan

1. Review predecessor implementation/diff and resolve contract blockers before verification.
2. In a separately authorized testing assignment, extend existing offline fixtures and scenarios
   using fake settings without `.env`, HTTPX MockTransport, ASGI lifespan, and MCP SDK clients.
3. Run selected AUTH/PERM/DISC scenarios, compatibility checks, and static checks; build only if
   package/dependency changes require it. Record exact selected test paths once implemented.
4. In separately authorized synthetic scope, provision task-owned fixture contrasts and verify
   marker/version/ownership before startup, Inspector calls, and controlled writes.
5. Record permission denials, actual resulting state, uncertainty/read-back, and cleanup separately.
6. Update this task, predecessor evidence and dashboard without erasing old limitations. Publish a
   release recommendation only if supported by evidence; production deployment is outside scope.

No dependency changes planned; reuse locked verification packages and existing test structure.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Scenarios |
|---|---|---|---|
| AC-001 | REQ-001 | Concurrent callers and session ID theft cannot change identity/key/state | VERIFY-001/002 |
| AC-002 | REQ-002 | A/B, tracker, ownership, admin, inherited and public variants produce correct target behavior | VERIFY-003/004 |
| AC-003 | REQ-003 | Revocation/rotation rechecked; hidden/cached tool call cannot bypass authorization | VERIFY-005 |
| AC-004 | REQ-004 | Reader/pinned defaults and existing schemas/receipts/no-retry semantics preserved | VERIFY-006 |
| AC-005 | REQ-005 | All affected writes have resulting-state and denial evidence plus owned cleanup record | VERIFY-007/008 |

Every result remains pending. Mocks establish adapter behavior, not real target permissions.

## 7. Test plan and execution record

| Scenario | Acceptance | Procedure / expected result | Mode |
|---|---|---|---|
| VERIFY-001 | AC-001 | AUTH-001 through AUTH-005 and REST key forwarding/admission matrix | Offline |
| VERIFY-002 | AC-001 | AUTH-006; concurrent sessions, guessed session ID, changed key, GET/DELETE, shutdown | Offline MCP; synthetic Inspector |
| VERIFY-003 | AC-002 | PERM-001 through PERM-008; source matrix, context proof, error boundaries | Review; offline |
| VERIFY-004 | AC-002 | Compare A/B, tracker, own/other, group/inherited, admin, non-member and project state with same-key Redmine outcomes | Synthetic |
| VERIFY-005 | AC-003 | DISC-002/003/005/006; role revocation, lock/rotation, repeated discovery and direct call | Offline; synthetic |
| VERIFY-006 | AC-004 | AUTH-007/008, PERM-009, DISC-004/007; stable contracts and accepted/uncertain receipts | Offline; opt-in startup |
| VERIFY-007 | AC-005 | Each affected write observes allowed state change and forbidden unchanged state, including upload/copy/move/relation side effects | Synthetic |
| VERIFY-008 | AC-005 | Manifest-owned cleanup and remaining journal/mail/upload effects recorded | Synthetic |

| Evidence | Command/procedure | Actual result | Status |
|---|---|---|---|
| EVID-001 | `bash scripts/check.sh` during the earlier coding/verification work; current `git diff --check` | Earlier Ruff/format/mypy/architecture checks passed; current whitespace check passes. No tests rerun following the user's correction | Static-check history only |
| EVID-002 | Separately authorized offline verification | Agent-created tests and changes to existing tests were removed; unrequested execution is not approved acceptance | Pending separate authorization |
| EVID-003 | Earlier `uv build --offline` after dependency pinning | Source and wheel built successfully | Package build history |
| EVID-004 | Separately authorized startup/Inspector and synthetic verification | Agent-created acceptance scripts and Compose definition were removed; no further verification authorized | Pending separate authorization |

No planned scenario is passing evidence. If runtime checks remain waived or unavailable, retain
the limitation and mark acceptance blocked; do not invent successful target-version outcomes.

## 8. Implementation and review record

The agent incorrectly interpreted the full-range implementation assignment as permission to create
and execute acceptance tests. Offline tests and synthetic fixture/write checks were run before the
user corrected that interpretation. Those actions are recorded as history, not approved acceptance.
The agent then removed the new test modules, `tools/acceptance/` scripts, isolated acceptance
Compose definition and environment initializer, and restored its edits to existing tests.

The synthetic work used separate prep-014 containers/volumes and ignored `.local/prep014/` state;
existing synthetic accounts and volumes were not reused. Generated state must not be committed.
The two temporary containers were stopped after their Compose ownership labels were checked.
Their ignored state and separate Docker volumes were retained; their data and historical
fixture/mail effects are not claimed to have been rolled back. No existing environment was stopped.

A runtime correction found during that work remains in
`integrations/redmine/capabilities.py`: relation detail endpoints are read from the API's `issue_id`
and `issue_to_id`, rather than the internal database field `issue_from_id`. This matches the pinned
source's `app/views/issue_relations/show.api.rsb` and the existing relation gateway contract.
The correction does not add testing tools or change public operation identifiers.

## 9. Completion and handoff

- [ ] Predecessor contracts and implementations reviewed.
- [ ] Separately authorized offline scenarios and static checks pass.
- [ ] Authorized target permission and resulting-state evidence recorded.
- [ ] Task-owned cleanup and residual effects recorded.
- [ ] Migration/rollback documentation reviewed.
- [ ] All affected task records/dashboard synchronized and final diff reviewed.

Current status: blocked on separately approved acceptance. Keep the coding and verification
handoffs distinct. Do not run or generate testing tooling automatically; release acceptance cannot
be inferred from the implementation assignment or the unrequested verification history.
