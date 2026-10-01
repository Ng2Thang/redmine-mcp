# prep-009-release-acceptance: Accept complete capability release

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-009-release-acceptance |
| Assigned capability | Check the complete Redmine 7.1 catalog and release evidence. |
| Type / access / destructive effects | Shared prerequisite / planning or infrastructure / None in this documentation task |
| Status | blocked - documentation only |
| Dependencies | [tool-035-remove-issue-watcher](tool-035-remove-issue-watcher.md); predecessor acceptance required |
| Related tasks | [Master plan](../redmine-7-1-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | Pinned 7.1 build required; repository currently pins 6.0.5-bookworm |
| Last updated | 2026-10-01, Codex |
| Progress summary | Prerequisite defined; no code, tests, migration, or live check performed. |
| Blocker / next action | Wait for tool-035 acceptance; consolidate evidence and request final release review. |

## 2. Discovery and evidence

Check the complete Redmine 7.1 catalog and release evidence. Audit 11 preserved operations, two extensions, twenty additions, all task acceptance, reader/writer isolation, permission matrix, Gantt client recipe, documentation, backup and recovery.

| Source | Checked | Evidence and limitation |
|---|---|---|
| [Current roadmap](../index.md) | 2026-10-01 | Existing task status and architecture; no pending acceptance is treated as passed. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-01 | Current synthetic Redmine is 6.0.5, so it cannot establish 7.1 behavior. |
| [Tool reference](../../tool-reference.md) | 2026-10-01 | Existing public catalog is the compatibility baseline. |

Decisions: this prerequisite owns no public MCP operation; tool-035-remove-issue-watcher must be
reviewed without rewriting prior evidence. Testing and any live rehearsal
require separate user authorization. The exact build remains an execution
blocker where 7.1 behavior is needed.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Check the complete Redmine 7.1 catalog and release evidence. |
| REQ-002 | Audit 11 preserved operations, two extensions, twenty additions, all task acceptance, reader/writer isolation, permission matrix, Gantt client recipe, documentation, backup and recovery. |
| REQ-003 | Scope and existing capability compatibility are preserved; evidence is dated and redacted. |

In scope: Release ledger, documentation, configuration, and final diff; no new MCP operation. Out of scope: unrelated Redmine APIs, an administrator
production credential, and claims based on unrun checks.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP name / operation ID / REST route | N/A - shared prerequisite |
| Inputs | Existing configuration, bounded client, and reviewed prior task contract |
| Outputs | Every required task has passing evidence and user acceptance; no operation is duplicated or silently exposed; release and recovery instructions are reviewable. |
| Access | No new public permission |
| Version support | Pinned 7.1 build required; exact target evidence is required before completion. |
| Errors | Record failed prerequisite or recovery as blocked; never fabricate a successful result. |

Write semantics: N/A - no Redmine mutation belongs to this planning task.

Specification exit check: the prerequisite's procedure and expected evidence
are assigned. Exact version and execution evidence remain pending.

## 5. Implementation plan

1. Inspect the predecessor's accepted evidence and current configuration.
2. Review authoritative versioned source or repository contracts relevant to this prerequisite.
3. Audit 11 preserved operations, two extensions, twenty additions, all task acceptance, reader/writer isolation, permission matrix, Gantt client recipe, documentation, backup and recovery.
4. Update only the owned implementation or operations documentation; preserve unrelated edits.
5. Run applicable static checks during a separately assigned coding stage.
6. Hand off exact offline and synthetic scenarios; run them only with separate testing authorization.
7. Update this task and the dashboard from actual results, then request user acceptance.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Check the complete Redmine 7.1 catalog and release evidence. | Pending |
| AC-002 | REQ-002 | Every required task has passing evidence and user acceptance; no operation is duplicated or silently exposed; release and recovery instructions are reviewable. | Pending |
| AC-003 | REQ-003 | Existing tools and unrelated state remain compatible; failures are reported. | Pending |

Each criterion requires a dated procedure and redacted actual result. A draft
or static check alone does not pass acceptance.

## 7. Test plan and execution record

Testing is planned, not authorized or run. For prep-009-release-acceptance, verify:
- Success: Every required task has passing evidence and user acceptance; no operation is duplicated or silently exposed; release and recovery instructions are reviewable.
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
- Remaining blocker: Wait for tool-035 acceptance; consolidate evidence and request final release review.

## 9. Completion and handoff

- [ ] Required prerequisite implemented or performed.
- [ ] Acceptance criteria have passing evidence.
- [ ] Authorized verification and applicable static checks pass.
- [ ] Compatibility and recovery/state checks pass where relevant.
- [ ] Dashboard and documentation match actual evidence.
- [ ] User accepts this task before the next task starts.

Final status: blocked. Next action: Wait for tool-035 acceptance; consolidate evidence and request final release review.
