# prep-021-current-catalog-documentation: Align contributor and operator guidance

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-021-current-catalog-documentation |
| Assigned capability | Let a new user configure reader/writer access and understand the actual support level |
| Type / access / destructive effects | Shared documentation prerequisite; read-only inspection; none |
| Status | planned |
| Dependencies | [prep-020](prep-020-current-catalog-acceptance.md) accepted |
| Related tasks | [Dashboard](../index.md); [prep-022](prep-022-operational-readiness.md); original prep-009 |
| Target Redmine version | 7.0.2; describe only evidence supported by the accepted ledger |
| Last updated | 2026-10-07, Codex |
| Progress summary | Documentation discrepancies identified; no existing guidance updated yet |
| Next action | After prep-020 acceptance, assign this documentation-only task |

## 2. Discovery and evidence

README describes the older read-only implementation and says authentication testing is deferred.
Operations says no write operations are registered; architecture/security/contributor guidance
also retain earlier future-write descriptions. Current code implements reader and opt-in writer
catalogs, personal-key authorization, scoped capabilities, and reporting. Some changelog entries
still say acceptance is pending despite later evidence. These documents mix historical and current
statements and need consistent context rather than blanket replacement of every pending label.

| Source | Reviewed | Finding / limitation |
|---|---|---|
| `README.md`, `docs/operations.md`, `docs/architecture.md` | 2026-10-07 | Current instructions still describe earlier catalogs |
| `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` | 2026-10-07 | Several support/testing/write statements require evidence-based reconciliation |
| `auth/policy.py`, `config.py`, `mcp/catalog.py`, `deploy/compose.yaml` | 2026-10-07 | Current names, gates, defaults, and localhost deployment boundary |
| `deploy/compose.test.yaml` | 2026-10-07 | Pinned 7.0.2 target; configuration is not runtime acceptance |
| [Coverage matrix](../testing-coverage.md) and prep-020 ledger | Existing / dependency | Dated evidence; do not extrapolate broader support |

No new native endpoint, permission, or upstream compatibility claim is planned. Reference
existing feature contracts and source evidence. Preserve unrelated working-tree edits.

| Decision | Resolution | Blocking? |
|---|---|---|
| DEC-001 | README summarizes current capabilities and links the maintained tool reference instead of duplicating every schema | No |
| DEC-002 | Correct current instructions; preserve dated task records, prior waivers, and genuine verification gaps | No |
| DEC-003 | Do not edit AGENTS.md or skill instructions as part of this documentation correction | No |
| DEC-004 | prep-022 owns guidance for new readiness/audit/CI/recovery behavior; this task documents only existing accepted behavior | No |

## 3. Requirements

In scope: current user, contributor, architecture, security, testing, operations, and changelog
guidance. Out of scope: runtime changes, new tools, policy relaxation, release publication,
running documented commands, or resolving future hosting/OAuth choices.

| ID | Required observable behavior | Constraint |
|---|---|---|
| REQ-001 | README accurately describes current readers, configured writers, authentication, and support limitations | No claim that every caller discovers all 32 operations |
| REQ-002 | Writer setup explains pinned/personal-key mode, operation lists, allowed_all, and native permissions | Reader remains read-only; examples do not enable a live deployment |
| REQ-003 | Testing/support statements match dated acceptance and remaining limitations | Historical records are retained |
| REQ-004 | All operational examples are Git Bash, use localhost/private configuration, and separate synthetic/external environments | No embedded credentials or unsafe reset/restore examples |
| REQ-005 | Contributor/architecture/security/changelog guidance is consistent with public contracts | No invented supported versions, release, SLA, or recovery guarantee |

## 4. Public contract and technical specification

| Area | Decision |
|---|---|
| MCP / REST interface | Unchanged; authoritative schemas and operation IDs remain in code/tool reference |
| Inputs | Current code/configuration plus accepted prep-020 ledger |
| Output | Updated existing English Markdown; explanatory links instead of redundant schema copies |
| Authentication / permissions | Describe current gates and caller-owned keys, without changing policy |
| Configuration | Preserve defaults; explain allowed_all includes future registered writes after upgrade |
| Errors / write semantics | Document uncertainty/reconciliation and acceptance versus verification from prep-019 |
| Version / pagination | Only evidenced 7.0.2 support; preserve incomplete/partial reporting guidance |

Required document ownership:

- `README.md`: scope, development/pilot status, setup links, readers and opt-in writers, current testing.
- `docs/operations.md`: valid writer startup guidance and private configuration, existing recovery limits.
- `docs/architecture.md`: actual catalog validation, authorization/discovery, dependency flow.
- `SECURITY.md`: current authentication/session/permission controls and remaining limitations.
- `CONTRIBUTING.md`, `docs/development.md`, `docs/manual-verification.md`: actual workflow and
  explicit test-authorization boundaries.
- `CHANGELOG.md`, `docs/testing-roadmap.md`: reconcile stale current summaries with dated results;
  preserve unreleased status and historical evidence.
- `docs/configuration.md` and `docs/tool-reference.md`: correct discrepancies only; no contract redesign.

Illustrative commands must use ignored env-files and placeholders. Do not reproduce real values,
run `docker compose config`, or execute setup/reset/verification instructions during this task.
Specification exit: documentation scope and factual sources are fixed by the predecessor ledger.

## 5. Implementation plan

| Step | Work | Files / verification |
|---|---|---|
| 1 | Build a discrepancy list against code and the accepted ledger | Owned documents; read-only inspection |
| 2 | Correct user setup, writer scope, and testing summaries | README, operations, configuration, reference |
| 3 | Correct architecture, security, and contributor descriptions | Remaining owned current guides |
| 4 | Reconcile unreleased notes without erasing dated evidence | Changelog, testing roadmap, links to ledger |
| 5 | Read the resulting guidance as a new reader/writer user | Manual Markdown/link review; no commands executed |
| 6 | Record changes and synchronize this task/dashboard | Documentation handoff |

No runtime, dependency, lockfile, test, CI, or deployment changes are planned.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | New user reads README | Actual scope, caller auth, writer opt-in, and support level are clear |
| AC-002 | Operator follows writer configuration guidance conceptually | Reader isolation, caller restrictions, operation ceiling, and allowed_all semantics agree with code |
| AC-003 | Reviewer compares testing/support statements to evidence | Dated passing results and unresolved gaps are distinguished |
| AC-004 | Reviewer reads all commands and environment examples | Bash-only, private placeholders, localhost, and environment boundaries are preserved |
| AC-005 | Reviewer compares related documents and historical records | Current guidance is consistent; contracts, history, and unreleased status remain accurate |

| Requirement | Criterion | Verification | Result |
|---|---|---|---|
| REQ-001 | AC-001 | STAB-021-001 | Pending |
| REQ-002 | AC-002 | STAB-021-002 | Pending |
| REQ-003 | AC-003 | STAB-021-003 | Pending |
| REQ-004 | AC-004 | STAB-021-004 | Pending |
| REQ-005 | AC-005 | STAB-021-005 | Pending |

## 7. Test plan and execution record

Automated/runtime tests are N/A for this documentation-only task. Do not add or run tests,
Markdown test tooling, startup, Inspector, build, or Docker commands merely to review prose.

| Scenario | Method | Expected result |
|---|---|---|
| STAB-021-001 | Manual source/README comparison | Capability summary agrees with catalog and accepted support level |
| STAB-021-002 | Manual config/setup comparison | Modes, gates, defaults, and allowed_all implications agree |
| STAB-021-003 | Manual ledger comparison | Claims have correct dates/scopes and retain limitations |
| STAB-021-004 | Manual example review | All examples satisfy language, privacy, and environment constraints |
| STAB-021-005 | Manual document/link/diff review | Local links resolve; no contradictory current statements or altered historical evidence |

| Evidence | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-021-001 | Future manual review of STAB-021-001..005 | Not performed | Pending |

## 8. Implementation and review record

- Changes made: this planning document and dashboard only.
- Runtime/tooling verification: not performed and not required for prose-only changes.
- Future review must distinguish stale current summaries from genuine pending criteria.
- Additional operational claims remain owned by prep-022 and cannot be marked complete here.

## 9. Completion and handoff

- [ ] All required current guides corrected against accepted evidence.
- [ ] Bash-only commands, private examples, and links manually reviewed.
- [ ] Contracts, historical records, and genuine gaps preserved.
- [ ] Task/dashboard synchronized with an accurate documentation result.

Final status: planned. Next action: complete prep-020 acceptance, then assign documentation work.
No automated tests are required for this task. Proceed to prep-022 decision resolution afterward.
