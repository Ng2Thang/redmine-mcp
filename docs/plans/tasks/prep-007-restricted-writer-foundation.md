# prep-007-restricted-writer-foundation: Create restricted writer foundation

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../../configuration.md#separate-writer-deployment).

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-007-restricted-writer-foundation |
| Assigned capability | Establish an opt-in writer deployment before any write tool. |
| Type / access / destructive effects | Shared prerequisite / planning or infrastructure / None in this documentation task |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-019-download-attachment](tool-019-download-attachment.md); predecessor acceptance required |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Restricted writer configuration, catalog selection, authorization, Compose profile, and bounded single-attempt write transport implemented. |
| Blocker / next action | User review, then separately authorized offline and synthetic verification; no write operation is public yet. |

## 2. Discovery and evidence

Establish an opt-in writer deployment before any write tool. Separate reader/writer operation catalogs; false-default enablement; restricted caller identities and per-operation policy; bounded JSON/binary writes; 201/204 handling; accepted/uncertain receipts; sanitized logs; no retries.

| Source | Checked | Evidence and limitation |
|---|---|---|
| [Current roadmap](../index.md) | 2026-10-01 | Existing task status and architecture; no pending acceptance is treated as passed. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | Redmine 7.0.2 is pinned; runtime acceptance remains pending. |
| [Tool reference](../../tool-reference.md) | 2026-10-01 | Existing public catalog is the compatibility baseline. |

Decisions: this prerequisite owns no public MCP operation. The owner approved tool-019 and its
shared binary-limit correction on 2026-10-02. Testing and any live rehearsal require separate
user authorization. Exact 7.0.2 runtime behavior remains unverified.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Establish an opt-in writer deployment before any write tool. |
| REQ-002 | Separate reader/writer operation catalogs; false-default enablement; restricted caller identities and per-operation policy; bounded JSON/binary writes; 201/204 handling; accepted/uncertain receipts; sanitized logs; no retries. |
| REQ-003 | Scope and existing capability compatibility are preserved; evidence is dated and redacted. |

In scope: Deployment, auth/policy, transport, errors, models, and catalog validation; no user-facing write operation yet. Out of scope: unrelated Redmine APIs, an administrator
production credential, and claims based on unrun checks.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP name / operation ID / REST route | N/A - shared prerequisite |
| Inputs | Existing configuration, bounded client, and reviewed prior task contract |
| Outputs | Reader never exposes writes; writer rejects missing/unauthorized keys; no-body success and post-dispatch uncertainty are represented truthfully; old readers still work. |
| Access | Restricted writer configuration; preserve reader-only catalog |
| Version support | 7.0.2 image pinned; exact target behavior remains unverified. |
| Errors | Record failed prerequisite or recovery as blocked; never fabricate a successful result. |

Write semantics: The foundation reports accepted writes and uncertain outcomes separately, does not retry after an unknown result, and never treats failed read-back as a failed write.

Specification exit check: the prerequisite's procedure and expected evidence
are assigned. Exact version and execution evidence remain pending.

## 5. Implementation plan

1. Inspect the predecessor's accepted evidence and current configuration.
2. Review authoritative versioned source or repository contracts relevant to this prerequisite.
3. Separate reader/writer operation catalogs; false-default enablement; restricted caller identities and per-operation policy; bounded JSON/binary writes; 201/204 handling; accepted/uncertain receipts; sanitized logs; no retries.
4. Update only the owned implementation or operations documentation; preserve unrelated edits.
5. Run applicable static checks during a separately assigned coding stage.
6. Hand off exact offline and synthetic scenarios; run them only with separate testing authorization.
7. Update this task and the dashboard from actual results, then request user acceptance.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Establish an opt-in writer deployment before any write tool. | Pending |
| AC-002 | REQ-002 | Reader never exposes writes; writer rejects missing/unauthorized keys; no-body success and post-dispatch uncertainty are represented truthfully; old readers still work. | Pending |
| AC-003 | REQ-003 | Existing tools and unrelated state remain compatible; failures are reported. | Pending |

Each criterion requires a dated procedure and redacted actual result. A draft
or static check alone does not pass acceptance.

## 7. Test plan and execution record

Testing is planned, not authorized or run. For prep-007-restricted-writer-foundation, verify:
- Success: Reader never exposes writes; writer rejects missing/unauthorized keys; no-body success and post-dispatch uncertainty are represented truthfully; old readers still work.
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

- Changes made: reader/writer catalog selection, restricted key and user identity, per-operation
  write policy, separate writer Compose profile, bounded single-attempt JSON/binary transport,
  accepted/uncertain receipt, configuration and operations documentation.
- Contract: writer requires one personal key digest and permitted user IDs. Empty operation list
  exposes no write tools. Unknown operation IDs prevent startup. Reader Compose forces writes off.
- Static checks (2026-10-02): `.venv/Scripts/ruff.exe check .`,
  `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, and
  `git diff --check` passed. Git reported only line-ending conversion warnings.
- Automated tests: not run.
- Startup, Inspector, and live state checks: not run.
- Remaining blocker: User review and separate authorization for offline writer boundary tests,
  synthetic startup, missing/incorrect key, role and operation denial, 201/204, oversized body,
  timeout/uncertain receipt, and state inspection/cleanup. No live writes were attempted.

## 9. Completion and handoff

- [ ] Required prerequisite implemented or performed.
- [ ] Acceptance criteria have passing evidence.
- [ ] Authorized verification and applicable static checks pass.
- [ ] Compatibility and recovery/state checks pass where relevant.
- [ ] Dashboard and documentation match actual evidence.
- [ ] User accepts this task before the next task starts.

Final status: blocked. Next action: Review this foundation, then separately authorize the planned
verification before acceptance. Coding finished; testing remains pending.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
