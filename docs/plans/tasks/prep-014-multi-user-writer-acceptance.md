# prep-014-multi-user-writer-acceptance: Verify caller isolation and resulting write state

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-014-multi-user-writer-acceptance |
| Assigned capability | Establish evidence for personal-key writer access and caller-specific discovery |
| Type / access / destructive effects | Shared verification prerequisite / offline and opt-in synthetic writes / Task-owned fixture mutations only |
| Status | planned |
| Dependencies | [prep-011](prep-011-multi-user-writer-auth.md), [prep-012](prep-012-project-resource-authorization.md), [prep-013](prep-013-caller-tool-discovery.md) implemented; existing [prep-002](prep-002-offline-tests.md) baseline and [prep-008](prep-008-synthetic-writer-verification.md) fixture guidance; separate testing authorization |
| Related tasks | [Roadmap](../multi-user-writer-authorization.md); [dashboard](../index.md); existing tool-020 through tool-030 and prep-009 |
| Target Redmine version | Pinned 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Verification scenarios and fixture requirements planned; nothing executed |
| Next action | Complete preceding contracts/implementation; obtain separate assignment before writing or running tests or live checks |

## 2. Discovery and evidence

Repository has a completed credential-free offline baseline; earlier writer tasks still have
pending permission/state evidence. Those records must remain separate from this acceptance.
Sources checked 2026-10-05: [testing roadmap](../../testing-roadmap.md), prep-002, prep-007/008,
prep-009, current dashboard, locked dependencies and synthetic Compose pin.
Exact permission limitations and authoritative upstream links are in the [roadmap evidence](../multi-user-writer-authorization.md#baseline-evidence-and-limitations).
All target state behavior is unverified for this change. Initial working tree was clean.

The user requested planning, not automated verification. Historical runtime waiver remains
history; do not infer permission to seed, reset, restore, change real roles, or execute writes.

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
| EVID-001 | `bash scripts/check.sh` after implementation | Not run | Pending |
| EVID-002 | `uv run --frozen pytest` with reviewed selected paths after separate authorization | Not run; paths assigned by testing implementation | Pending |
| EVID-003 | `uv build` if dependency/package changes justify it | Not run | Pending |
| EVID-004 | Authorized startup/Inspector and marked synthetic VERIFY-002/004/005/007/008 | Not run | Pending |

No planned scenario is passing evidence. If runtime checks remain waived or unavailable, retain
the limitation and mark acceptance blocked; do not invent successful target-version outcomes.

## 8. Implementation and review record

Planning documents only. No tests written/run, no server startup, Docker operation, Inspector
session, seed/reset, or live write. Predecessor coding and fixture availability remain dependencies.

## 9. Completion and handoff

- [ ] Predecessor contracts and implementations reviewed.
- [ ] Separately authorized offline scenarios and static checks pass.
- [ ] Authorized target permission and resulting-state evidence recorded.
- [ ] Task-owned cleanup and residual effects recorded.
- [ ] Migration/rollback documentation reviewed.
- [ ] All affected task records/dashboard synchronized and final diff reviewed.

Final status: planned. Next action: finish predecessor contracts/implementation; testing fixtures
and execution require a separate assignment. Release acceptance cannot be inferred from planning.
