# prep-008-synthetic-writer-verification: Prepare disposable writer verification

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-008-synthetic-writer-verification |
| Assigned capability | Build a controlled fixture and state-inspection plan for write-tool acceptance. |
| Type / access / destructive effects | Shared prerequisite / planning or infrastructure / None in this documentation task |
| Status | blocked - verification plan prepared; execution pending |
| Dependencies | [prep-007-restricted-writer-foundation](prep-007-restricted-writer-foundation.md); predecessor acceptance required |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Task-owned fixture and state-inspection procedure specified; no fixtures, tests, or live checks created. |
| Blocker / next action | Review the plan; obtain separate authorization before fixture creation, tests, or live mutations. |

## 2. Discovery and evidence

Build a controlled fixture and state-inspection plan for write-tool acceptance. Specify marker checks, restricted users and roles, task-owned project/issues/files, mutation state comparisons, duplicate/timeout scenarios, and cleanup; do not run seeding or mutations in this planning stage.

| Source | Checked | Evidence and limitation |
|---|---|---|
| [Current roadmap](../index.md) | 2026-10-01 | Existing task status and architecture; no pending acceptance is treated as passed. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | Redmine 7.0.2 is pinned; runtime acceptance remains pending. |
| [Tool reference](../../tool-reference.md) | 2026-10-01 | Existing public catalog is the compatibility baseline. |

Decisions: this prerequisite owns no public MCP operation. Prep-007 implementation was approved
and committed as `106f00a` on 2026-10-02; its runtime acceptance remains pending. Testing and
any live rehearsal require separate user authorization. Target runtime verification remains
pending.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Build a controlled fixture and state-inspection plan for write-tool acceptance. |
| REQ-002 | Specify marker checks, restricted users and roles, task-owned project/issues/files, mutation state comparisons, duplicate/timeout scenarios, and cleanup; do not run seeding or mutations in this planning stage. |
| REQ-003 | Scope and existing capability compatibility are preserved; evidence is dated and redacted. |

In scope: Synthetic fixture inventory and verification procedure; no public MCP operation. Out of scope: unrelated Redmine APIs, an administrator
production credential, and claims based on unrun checks.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP name / operation ID / REST route | N/A - shared prerequisite |
| Inputs | Marked isolated 7.0.2 environment and task-owned fixture namespace |
| Outputs | Every write tool can demonstrate allowed/denied behavior and resulting state on disposable data; cleanup changes only owned fixtures. |
| Access | No new public permission |
| Version support | 7.0.2 isolated instance required; exact target evidence is required before completion. |
| Errors | Record failed prerequisite or recovery as blocked; never fabricate a successful result. |

Write semantics: N/A - no Redmine mutation belongs to this planning task.

Specification exit check: the prerequisite's procedure and expected evidence
are assigned. Exact version and execution evidence remain pending.

### Controlled fixture and state-inspection procedure

1. Verify the target is the dedicated `redmine-mcp-test` Compose project, pinned image digest,
   `REDMINE_TEST_MARKER=redmine-mcp-synthetic-v1`, `.local/environment.json` kind/version,
   completed `.local/manifest.json` kind/status, and expected synthetic Docker volume labels.
   Abort on any mismatch. Read credentials only from ignored `.local/credentials.json`; do not
   print keys or commit generated manifests. Do not run this procedure against external Redmine.
2. In an authorized fixture stage, create a new private project with a unique
   `mcp-writer-<run-id>` identifier and the Files and Issue tracking modules. Give one ordinary
   synthetic user the minimum role that actually permits the intended upload, file, attachment,
   issue, and later relation/watch operations; verify each permission with the pinned 7.0.2
   instance before relying on it. Give a second ordinary user read-only membership and leave
   another user outside the project. Keep synthetic administrator credentials in the separate
   fixture/setup process; never configure them in `mcp-writer`.
3. Record task-owned project, user, issue, version, file, upload, attachment, and relation IDs
   in a new ignored `.local/writer-<run-id>.json` manifest. Record initial project file IDs,
   issue attachment IDs, relevant issue field values, memberships, and attachment metadata.
   Store no binary body or key in the manifest. Create only the fixture objects needed by the
   current tool; later tool tasks extend the same run namespace explicitly.
4. Start `mcp-writer` only with its own ignored env-file, restricted personal key digest, allowed
   user ID, and current operation ID. Confirm the reader service still lists no write tools and
   rejects direct REST mutations. Confirm wrong key, wrong user, unlisted operation, and an
   upstream role denial produce safe errors without state change.
5. For each writer tool, compare its response and a separate same-key Redmine read-back against
   the initial manifest. Record exact changed IDs and fields, plus unchanged neighboring records.
   If read-back fails, report accepted upstream response and unavailable verification separately;
   never turn a successful write into a claimed failure. For uncertain transport outcomes, inspect
   task-owned state before considering a repeat. Do not automatically retry an upload or mutation.
6. Exercise duplicate calls only on disposable fixture objects after recording the first ID and
   state. Inject timeout or connection interruption with an offline transport first; a live
   uncertainty experiment requires separate approval and a known reconciliation path. Compare
   the reader catalog and an existing read outcome before/after the writer run.
7. Clean up only IDs listed in the writer manifest, in reverse dependency order, after confirming
   the synthetic marker again. Inspect remaining project/file/issue state before deleting the
   task-owned project. Record anything that cannot be deleted, including unattached temporary
   uploads, as residue. Never use a broad reset or restore as routine cleanup. Keep the writer
   stopped if the marker, manifest, or resulting state is ambiguous.

### Evidence matrix for later execution

| Scenario | Required observation | Status |
|---|---|---|
| WRITER-001 | Marker, image digest, fixture namespace, and restricted non-admin identity recorded without secrets | Pending |
| WRITER-002 | Reader catalog and direct REST write rejection; writer wrong-key, wrong-user, unlisted-operation rejection | Pending |
| WRITER-003 | 201 JSON and 204 empty success receipts; bounded JSON/binary request and response handling | Pending |
| WRITER-004 | Pre-dispatch pool failure versus post-dispatch timeout/transport uncertainty; no automatic retry | Pending |
| WRITER-005 | Per-tool before/after state, denied-role no-change result, duplicate behavior, and unrelated state comparison | Pending |
| WRITER-006 | Marker-checked cleanup of only task-owned IDs, residue report, and reader compatibility | Pending |

## 5. Implementation plan

1. Inspect the predecessor's accepted evidence and current configuration.
2. Review authoritative versioned source or repository contracts relevant to this prerequisite.
3. Specify marker checks, restricted users and roles, task-owned project/issues/files, mutation state comparisons, duplicate/timeout scenarios, and cleanup; do not run seeding or mutations in this planning stage.
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

- Changes made: this task document and dashboard; controlled fixture and evidence matrix prepared.
- Static checks: documentation-only `git diff --check` and final diff inspection passed
  on 2026-10-02; no code checks apply to this documentation change.
- Automated tests: not run.
- Startup, Inspector, and live state checks: not run.
- Remaining blocker: User review and separate authorization before creating or mutating fixtures;
  prep-007 runtime evidence is still pending.

## 9. Completion and handoff

- [ ] Required prerequisite implemented or performed.
- [ ] Acceptance criteria have passing evidence.
- [ ] Authorized verification and applicable static checks pass.
- [ ] Compatibility and recovery/state checks pass where relevant.
- [ ] Dashboard and documentation match actual evidence.
- [ ] User accepts this task before the next task starts.

Final status: blocked. Next action: Review this plan, then separately authorize fixture creation,
offline tests, and marked synthetic verification before treating the prerequisite as accepted.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release.
Prior runtime observations do not establish acceptance for the pinned target.
Document mutation fixtures and cases are outside this target.
