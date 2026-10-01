# prep-005-upgrade-redmine-7-1: Pin and rehearse Redmine 7.1

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-005-upgrade-redmine-7-1 |
| Assigned capability | Prepare an exact 7.1 target and an isolated, recoverable upgrade rehearsal. |
| Type / access / destructive effects | Shared prerequisite / isolated migration rehearsal / Database migration in isolated copy |
| Status | blocked - documentation only |
| Dependencies | [prep-004-accept-existing-baseline](prep-004-accept-existing-baseline.md); predecessor acceptance required |
| Related tasks | [Master plan](../redmine-7-1-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.1 released build required; repository currently pins 6.0.5-bookworm |
| Last updated | 2026-10-01, Codex |
| Progress summary | Prerequisite defined; no code, tests, migration, or live check performed. |
| Blocker / next action | Wait for a released 7.1 artifact, then freeze its digest and request approval for isolated upgrade rehearsal. |

## 2. Discovery and evidence

Prepare an exact 7.1 target and an isolated, recoverable upgrade rehearsal. Select a released artifact and immutable image digest; check runtime/plugin requirements; back up database and files; migrate an isolated copy; verify existing MCP tools, Documents REST, API-key auth, and recovery from backup.

| Source | Checked | Evidence and limitation |
|---|---|---|
| [Redmine upgrade guide](https://www.redmine.org/projects/redmine/wiki/RedmineUpgrade) | 2026-10-01 | Backup, requirements, migrations, and recovery are required; exact released 7.1 artifact remains unverified. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-01 | Current synthetic Redmine is 6.0.5, so it cannot establish 7.1 behavior. |
| [Tool reference](../../tool-reference.md) | 2026-10-01 | Existing public catalog is the compatibility baseline. |

Decisions: this prerequisite owns no public MCP operation; prep-004-accept-existing-baseline must be
reviewed without rewriting prior evidence. Testing and any live rehearsal
require separate user authorization. The exact build remains an execution
blocker where 7.1 behavior is needed.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Prepare an exact 7.1 target and an isolated, recoverable upgrade rehearsal. |
| REQ-002 | Select a released artifact and immutable image digest; check runtime/plugin requirements; back up database and files; migrate an isolated copy; verify existing MCP tools, Documents REST, API-key auth, and recovery from backup. |
| REQ-003 | Scope and existing capability compatibility are preserved; evidence is dated and redacted. |

In scope: Deployment/test configuration and migration runbook; no public MCP operation. Out of scope: unrelated Redmine APIs, an administrator
production credential, and claims based on unrun checks.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP name / operation ID / REST route | N/A - shared prerequisite |
| Inputs | Released 7.1 artifact and digest, backup manifest, isolated database and file volumes |
| Outputs | Pinned digest and versioned source; backup and restore logs; migration and old-tool evidence; no damage to the original 6.0.5 environment. |
| Access | Synthetic environment only; never overwrite the original instance |
| Version support | 7.1 released build required; exact target evidence is required before completion. |
| Errors | Record failed prerequisite or recovery as blocked; never fabricate a successful result. |

Write semantics: Migration may be irreversible on the migrated copy. Restore from the pre-upgrade database and attachment backups; never claim image downgrade reverses migrations.

Specification exit check: the prerequisite's procedure and expected evidence
are assigned. Exact version and execution evidence remain pending.

## 5. Implementation plan

1. Inspect the predecessor's accepted evidence and current configuration.
2. Review authoritative versioned source or repository contracts relevant to this prerequisite.
3. Select a released artifact and immutable image digest; check runtime/plugin requirements; back up database and files; migrate an isolated copy; verify existing MCP tools, Documents REST, API-key auth, and recovery from backup.
4. Update only the owned implementation or operations documentation; preserve unrelated edits.
5. Run applicable static checks during a separately assigned coding stage.
6. Hand off exact offline and synthetic scenarios; run them only with separate testing authorization.
7. Update this task and the dashboard from actual results, then request user acceptance.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Prepare an exact 7.1 target and an isolated, recoverable upgrade rehearsal. | Pending |
| AC-002 | REQ-002 | Pinned digest and versioned source; backup and restore logs; migration and old-tool evidence; no damage to the original 6.0.5 environment. | Pending |
| AC-003 | REQ-003 | Existing tools and unrelated state remain compatible; failures are reported. | Pending |

Each criterion requires a dated procedure and redacted actual result. A draft
or static check alone does not pass acceptance.

## 7. Test plan and execution record

Testing is planned, not authorized or run. For prep-005-upgrade-redmine-7-1, verify:
- Success: Pinned digest and versioned source; backup and restore logs; migration and old-tool evidence; no damage to the original 6.0.5 environment.
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
- Remaining blocker: Wait for a released 7.1 artifact, then freeze its digest and request approval for isolated upgrade rehearsal.

## 9. Completion and handoff

- [ ] Required prerequisite implemented or performed.
- [ ] Acceptance criteria have passing evidence.
- [ ] Authorized verification and applicable static checks pass.
- [ ] Compatibility and recovery/state checks pass where relevant.
- [ ] Dashboard and documentation match actual evidence.
- [ ] User accepts this task before the next task starts.

Final status: blocked. Next action: Wait for a released 7.1 artifact, then freeze its digest and request approval for isolated upgrade rehearsal.
