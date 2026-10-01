# prep-008-synthetic-writer-verification: Prepare disposable writer verification

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-008-synthetic-writer-verification |
| Assigned capability | Build a controlled fixture and state-inspection plan for write-tool acceptance. |
| Type / access / destructive effects | Shared prerequisite / planning or infrastructure / None in this documentation task |
| Status | blocked - documentation only |
| Dependencies | [prep-007-restricted-writer-foundation](prep-007-restricted-writer-foundation.md); predecessor acceptance required |
| Related tasks | [Master plan](../redmine-7-1-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.1 isolated instance required; repository currently pins 6.0.5-bookworm |
| Last updated | 2026-10-01, Codex |
| Progress summary | Prerequisite defined; no code, tests, migration, or live check performed. |
| Blocker / next action | Wait for prep-007 acceptance and separate authorization before creating or mutating fixtures. |

## 2. Discovery and evidence

Build a controlled fixture and state-inspection plan for write-tool acceptance. Specify marker checks, restricted users and roles, task-owned project/issues/documents/files, mutation state comparisons, duplicate/timeout scenarios, and cleanup; do not run seeding or mutations in this planning stage.

| Source | Checked | Evidence and limitation |
|---|---|---|
| [Current roadmap](../index.md) | 2026-10-01 | Existing task status and architecture; no pending acceptance is treated as passed. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-01 | Current synthetic Redmine is 6.0.5, so it cannot establish 7.1 behavior. |
| [Tool reference](../../tool-reference.md) | 2026-10-01 | Existing public catalog is the compatibility baseline. |

Decisions: this prerequisite owns no public MCP operation; prep-007-restricted-writer-foundation must be
reviewed without rewriting prior evidence. Testing and any live rehearsal
require separate user authorization. The exact build remains an execution
blocker where 7.1 behavior is needed.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Build a controlled fixture and state-inspection plan for write-tool acceptance. |
| REQ-002 | Specify marker checks, restricted users and roles, task-owned project/issues/documents/files, mutation state comparisons, duplicate/timeout scenarios, and cleanup; do not run seeding or mutations in this planning stage. |
| REQ-003 | Scope and existing capability compatibility are preserved; evidence is dated and redacted. |

In scope: Synthetic fixture inventory and verification procedure; no public MCP operation. Out of scope: unrelated Redmine APIs, an administrator
production credential, and claims based on unrun checks.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP name / operation ID / REST route | N/A - shared prerequisite |
| Inputs | Marked isolated 7.1 environment and task-owned fixture namespace |
| Outputs | Every write tool can demonstrate allowed/denied behavior and resulting state on disposable data; cleanup changes only owned fixtures. |
| Access | No new public permission |
| Version support | 7.1 isolated instance required; exact target evidence is required before completion. |
| Errors | Record failed prerequisite or recovery as blocked; never fabricate a successful result. |

Write semantics: N/A - no Redmine mutation belongs to this planning task.

Specification exit check: the prerequisite's procedure and expected evidence
are assigned. Exact version and execution evidence remain pending.

## 5. Implementation plan

1. Inspect the predecessor's accepted evidence and current configuration.
2. Review authoritative versioned source or repository contracts relevant to this prerequisite.
3. Specify marker checks, restricted users and roles, task-owned project/issues/documents/files, mutation state comparisons, duplicate/timeout scenarios, and cleanup; do not run seeding or mutations in this planning stage.
4. Update only the owned implementation or operations documentation; preserve unrelated edits.
5. Run applicable static checks during a separately assigned coding stage.
6. Hand off exact offline and synthetic scenarios; run them only with separate testing authorization.
7. Update this task and the dashboard from actual results, then request user acceptance.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Build a controlled fixture and state-inspection plan for write-tool acceptance. | Pending |
| AC-002 | REQ-002 | Every write tool can demonstrate allowed/denied behavior and resulting state on disposable data; cleanup changes only owned fixtures. | Pending |
| AC-003 | REQ-003 | Existing tools and unrelated state remain compatible; failures are reported. | Pending |

Each criterion requires a dated procedure and redacted actual result. A draft
or static check alone does not pass acceptance.

## 7. Test plan and execution record

Testing is planned, not authorized or run. For prep-008-synthetic-writer-verification, verify:
- Success: Every write tool can demonstrate allowed/denied behavior and resulting state on disposable data; cleanup changes only owned fixtures.
- Failure: unavailable artifact, rejected permission, malformed response,
  timeout, or failed recovery as applicable; record a blocker.
- Compatibility: compare existing reader catalog and outcomes before/after.
- Synthetic: use the marked isolated environment only after separate authorization.

| Evidence ID | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-001 | `bash scripts/check.sh` in a future coding stage, when applicable | Not run | Pending |
| EVID-002 | `uv run --frozen pytest` only after explicit testing authorization, when applicable | Not run | Pending |
| EVID-003 | Inspector and synthetic procedure only after explicit authorization | Not run | Pending |

## 8. Implementation and review record

- Changes made: this task document only.
- Static checks: not run for this task.
- Automated tests: not run.
- Startup, Inspector, and live state checks: not run.
- Remaining blocker: Wait for prep-007 acceptance and separate authorization before creating or mutating fixtures.

## 9. Completion and handoff

- [ ] Required prerequisite implemented or performed.
- [ ] Acceptance criteria have passing evidence.
- [ ] Authorized verification and applicable static checks pass.
- [ ] Compatibility and recovery/state checks pass where relevant.
- [ ] Dashboard and documentation match actual evidence.
- [ ] User accepts this task before the next task starts.

Final status: blocked. Next action: Wait for prep-007 acceptance and separate authorization before creating or mutating fixtures.
