# prep-020-current-catalog-acceptance: Close current capability acceptance gaps

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-020-current-catalog-acceptance |
| Assigned capability | Give maintainers a truthful, current evidence ledger for every registered capability |
| Type / access | Shared verification prerequisite; existing reads and writes |
| Destructive effects | Later testing may create/delete disposable resources and alter owned fixture roles; no production or shared-data mutation |
| Status | complete - current functional acceptance and evidence reconciliation |
| Dependencies | [prep-019](prep-019-write-outcome-consistency.md) accepted; existing prep-016/017/018 infrastructure |
| Related tasks | [Dashboard](../index.md); tool-032/033; allowed_all follow-up; original prep-009 release review |
| Target Redmine version | Pinned isolated 7.0.2; operation-specific gaps remain pending |
| Last updated | 2026-10-07, Codex |
| Progress summary | All 32 operation rows audited; 1086 offline and 21 owned live cases pass; version/membership/allowed_all accepted; broader original variants explicitly retained |
| Next action | Proceed to prep-021 documentation with the current ledger and explicit historical limitations; final release stays with prep-009/022 |

## 2. Discovery and evidence

`auth/policy.py` and `mcp/catalog.py` define 17 read and 15 write operations. Reader catalogs
exclude mutations; writer configuration and caller evidence can further limit discovery.
The coverage matrix records 883 offline cases and selected live evidence. Counts and prior
waivers are dated records, not proof of every current role combination or latest configuration.

| Source / version evidence | Reviewed | Finding / limitation |
|---|---|---|
| [Coverage matrix](../testing-coverage.md) | 2026-10-07 | Existing reporting and selected runtime evidence, with explicit follow-up gaps |
| [tool-032](tool-032-create-project-version.md) | 2026-10-07 | Native state/permission scenario TOOL-032-008 pending |
| [tool-033](tool-033-project-members-management.md) | 2026-10-07 | Native membership restrictions/side effects scenario TOOL-033-011 pending |
| [allowed_all follow-up](../writer-operations-allowed-all.md) | 2026-10-07 | Implementation recorded; configuration/catalog/admission testing pending |
| `deploy/compose.test.yaml` and [testing roadmap](../../testing-roadmap.md) | 2026-10-07 | Pin is 7.0.2; use isolated owned E2E environment, not the older shared deployment |

Existing feature task documents retain ownership of endpoint/permission contracts and their
versioned upstream evidence. This task inherits those contracts without claiming a fresh native
source review. Refresh target source evidence if a native discrepancy appears; stop that scenario
until its feature owner resolves the contract. Preserve unrelated working-tree changes.

| Decision | Resolution | Blocking? |
|---|---|---|
| DEC-001 | Inventory all current operations; retired download and unrelated APIs are excluded | No |
| DEC-002 | Require current functional acceptance for the full catalog; report explicit gaps rather than silently shrinking scope | No |
| DEC-003 | Keep historical acceptance/waivers separate from current functional evidence and final operational release approval | No |
| DEC-004 | The original feature tasks own contracts; this task owns cross-catalog evidence reconciliation and selected missing verification | No |

## 3. Requirements

In scope: evidence ledger, gap mapping, missing acceptance, and synchronized task/coverage status.
Out of scope: new features, blanket task closure, CI activation, production rollout, or final
release publication. Defects discovered during verification need a reviewed fix and re-verification.

| ID | Required observable behavior | Constraint |
|---|---|---|
| REQ-001 | Every one of the 32 current operations has a contract owner and dated evidence/gap row | Distinguish offline, live, waived, and missing evidence |
| REQ-002 | TOOL-032-008 and TOOL-033-011 are executed against owned 7.0.2 and actual state | Native roles, inheritance, visibility, and cleanup must be observed |
| REQ-003 | allowed_all is verified through settings, discovery, REST admission, and capabilities | Never bypass writer enablement, user admission, or project permissions |
| REQ-004 | Relevant historical pending variants and the prep-019 correction have explicit coverage or remaining blockers | Prior selected tests do not silently close broader matrices |
| REQ-005 | Actual results and limitations are reflected in the ledger, coverage matrix, task owners, and dashboard | No passing result inferred from static checks or suite count |

## 4. Public contract and technical specification

| Area | Decision |
|---|---|
| MCP / REST changes | None; invoke existing contracts, names, schemas, auth, and pagination |
| Inputs | Current operation lists, original task criteria, dated artifacts, owned private fixture manifest |
| Output | New `docs/testing/evidence/current-catalog-acceptance.md` with one row per operation and shared-policy sections |
| Ledger fields | Operation, contract owner, source revision/date, offline scenarios, live scenarios, limitations, status, exact next action |
| Configuration | Ordinary caller keys; reader and restricted writer separate; secrets stay ignored |
| Native mapping | Inherited unchanged from feature tasks; no new Redmine endpoint or permission |
| Errors | Failed/missing/contradictory evidence remains failed or blocked, with a concrete next action |

The ledger must map original criteria, not only tool names. Link later evidence to earlier
pending variants only when inputs, roles, target version, and assertions actually match.
Keep historical task records intact; append reconciliation notes rather than rewriting past results.

Specific acceptance groups:

- Version creation: native project/name/open/unshared state, supplied fields, duplicate recovery,
  ordinary manage_versions authorization, and unavailable read-back, per TOOL-032-008.
- Membership: public/private visibility, native managed/protected/inherited roles, descendant
  effects, assignments, batch outcomes and isolated cleanup, per TOOL-033-011.
- allowed_all: standalone/whitespace accepted, mixed/unknown values rejected, empty/explicit CSV
  compatibility, all configured writers discoverable where applicable, REST/capability consistency,
  reader denial and personal/pinned-key admission boundaries.
- Shared behavior: corrected 5xx receipts, concurrent caller/session isolation, scoped permission
  revocation, pagination limits, and truthful incomplete reporting. Reuse sufficient existing evidence.

Writes retain single dispatch, uncertainty, independent read-back, and no automatic rollback.
Preflight owned environment/version labels before fixture mutation. Restore task-owned grants
and remove created resources; record journals or other retained side effects. Never reset shared
volumes or inspect private production data to obtain acceptance evidence.

Specification exit: original scenarios and missing coverage are assigned; live results are pending.

## 5. Implementation plan

| Step | Work | Files / owner | Stage |
|---|---|---|---|
| 1 | Map all current operations and shared criteria to dated evidence | New current acceptance ledger; original tasks read-only initially | Evidence reconciliation |
| 2 | Identify exact missing variants and confirm isolated environment prerequisites | Ledger; existing fixture guidance | Verification preparation |
| 3 | Add/run missing allowed_all offline scenarios and focused regressions | Existing test layers, under explicit testing assignment | Testing |
| 4 | Execute version/membership native acceptance and required shared gaps | Owned 7.0.2 fixtures and existing E2E helpers | Authorized live testing |
| 5 | Record actual results and cleanup; update only supported criteria/statuses | Original tasks, coverage matrix, ledger, dashboard | Evidence handoff |

No dependency upgrade is planned. If a fixture or test dependency change becomes necessary,
record it in the authorized testing stage and update `uv.lock` with dependency metadata.
Do not run tests during a documentation-only or coding-only assignment.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | Current catalog is reconciled | All 32 operations and relevant shared criteria have one owner and explicit evidence/gaps |
| AC-002 | Version/membership scenarios run on owned 7.0.2 | Native permission and resulting-state assertions pass; cleanup is recorded |
| AC-003 | allowed_all modes and callers are exercised | Discovery, REST, capabilities, and denial agree with the existing contract |
| AC-004 | Earlier gaps and new correction are assessed | Each required criterion is supported or remains explicitly blocked |
| AC-005 | Final record is reviewed | Current status is consistent without erasing historical evidence or claiming operational release readiness |

| Requirement | Criteria | Verification | Result |
|---|---|---|---|
| REQ-001 | AC-001 | STAB-020-001 | Passed |
| REQ-002 | AC-002 | TOOL-032-008, TOOL-033-011 | Passed |
| REQ-003 | AC-003 | STAB-020-002/003 | Passed |
| REQ-004 | AC-004 | STAB-020-004 and prep-019 evidence | Passed |
| REQ-005 | AC-005 | Ledger/task/dashboard document review | Passed |

## 7. Test plan and execution record

| Scenario | Method | Expected result |
|---|---|---|
| STAB-020-001 | Read-only evidence audit | Current catalog count, owner links, revisions, and criterion coverage agree |
| STAB-020-002 | Offline settings + REST/MCP SDK | allowed_all valid/invalid forms and all 15 configured writer paths covered; reader/auth/project denials preserved |
| STAB-020-003 | Owned 7.0.2, Inspector + SDK | Ordinary callers have candidate discovery and actual admission consistent with native grants; selected mutations match state |
| TOOL-032-008 | Original feature live plan | Version fields, duplicates, roles, and independent observations verified |
| TOOL-033-011 | Original feature live plan | Membership visibility, role restrictions, inheritance, side effects, and cleanup verified |
| STAB-020-004 | Evidence mapping, focused missing scenarios | Historical pending variants and prep-019 are accounted for without blanket closure |

Future authorized commands include `uv run --frozen pytest` and
`uv run --frozen pytest tests/e2e --run-e2e`. Inspect fixture/preparation side effects before
running existing helpers; do not automatically reseed or reset an environment.

| Evidence | Planned procedure | Actual result | Status |
|---|---|---|---|
| EVID-020-001 | `uv run --frozen --no-sync python scripts/audit-catalog-acceptance.py` and original criterion audit | 32 unique rows, 17 reads/15 writes, owner links, matching registry, dated revision/source digests and H1..H6 limitations | Passed, 2026-10-07 |
| EVID-020-002 | `uv run --frozen --no-sync pytest -q` | 1086 passed, 1 existing dependency warning, 335.59 seconds; includes 49 new sentinel cases and every current writer through REST/MCP | Passed, 2026-10-07 |
| EVID-020-003 | `uv run --frozen --no-sync pytest tests/e2e --run-e2e -q --tb=short`; Inspector script invoked by the owned test | 21 passed, 1 existing dependency warning, 115.61 seconds; all four prep-020 scenarios, native state/role/side-effect assertions, Inspector catalog and three native-parity reads, cleanup and restored grants | Passed, 2026-10-07 |

## 8. Implementation and review record

- Changes made: this planning document and dashboard only.
- Prior counts/results are inherited dated evidence, not fresh execution.
- No test files, fixtures, native grants, or deployment configuration changed.
- Unavailable role/fixture evidence must block the affected criterion, not produce a waiver.

### Authorized execution and reconciliation, 2026-10-07

The user assigned prep-020 after prep-019 testing. This authorizes evidence reconciliation,
missing offline scenarios, owned native verification and Inspector within this task. No task
delegation, dependency installation, shared reset, production deployment or commit was performed.

- Added `docs/testing/evidence/current-catalog-acceptance.md`: one row for every operation, original owner,
  source revision/date, original/offline/live scenario mapping, status, limitations and next action.
  H1..H6 distinguish executed selected criteria, unexecuted broader matrices and historical waivers.
- Added `scripts/audit-catalog-acceptance.py`: verifies 32 unique rows, registry agreement and
  owner links, with ignored per-file source digests for the uncommitted working tree.
- Added settings and integration sentinel tests and reused the exact existing success/payload
  assertions for all 15 writers through REST/MCP. Reader/personal/restricted/pinned/wrong-key
  and project-permission boundaries, filtered capabilities, empty/CSV compatibility and invalid
  sentinel/unknown operation handling pass. Unknown operation rejection occurs in catalog
  validation; denied/disabled filtered candidates are omitted, not reported as grants.
- Added `tools/testing/e2e_catalog.rb` and `tests/e2e/test_catalog_acceptance.py`: four disposable
  projects and five task-owned roles; no modifications to existing native grants. Ordinary
  manager/readers, managed-role filtering, protected retention and native deletion rejection,
  public/private visibility, inheritance, child effects, assignments, native version fields,
  duplicate state/count, create without view_issues, and REST/SDK paths are asserted.
- `scripts/verify-catalog-inspector.py` runs Inspector 2.8.0 against a separate allowed_all
  localhost application, checks the full catalog and writer schemas/annotations, compares three
  reads with native versions/memberships/grants, and stops the server in `finally`. No Inspector
  mutations are performed. E2E factories now accept an explicit operation ceiling for testing.
- Populated historical fixtures verify nonempty workflow/native parity, parent/child shared
  versions, category and Target version filters, exact/descendant issue scope, September direct
  hours, registry/project trackers, native issue-log IDs and two ordinary profiles. Broader
  original matrices remain named follow-ups, not silently accepted.
- Updated the older all-reader lifecycle test with `list_project_members.project_ids` required
  by the current contract. Initial failures were test assumptions/fixture output/inheritance
  setup; no new production runtime defect or runtime change was required.
- Teardown checks zero task-owned projects/roles, external role-membership protection and owned
  tree boundaries. Deletion clears project/category default assignees; existing issue assignment
  remains. Existing baseline resources use prep-018 cleanup, and temporary permission revocation
  is restored. Journals can remain as documented; no history rollback is claimed.
- Current offline: 1086 passed. Current live: 21 passed. Ruff lint/format: passed (256 files);
  mypy: passed (120 runtime files); diff review/whitespace and catalog audit pass. The sole warning
  is the existing installed-dependency Pydantic schema-hook deprecation.

AC-001: all 32 rows/owners audited. AC-002: TOOL-032-008 and TOOL-033-011 accepted with native
state and cleanup. AC-003: allowed_all modes, discovery, admission and capabilities pass.
AC-004: prep-019 and historical variants reconciled explicitly, with remaining broader
original-owner blockers named H1..H5. AC-005: source tasks, ledger, coverage and dashboard agree;
historical records preserved and no operational release claim. Original tool-032/033 are now
complete; other task matrices are not blanket closed. The completion checklist below describes
evidence reconciliation, as AC-004 permits explicit remaining blockers rather than invented passes.

Exact artifacts and reproduction commands are in the current ledger. Git base
`533202519485ac1510e72e688fd40d6a695ac968` includes prep-019; prep-020 remains uncommitted.

## 9. Completion and handoff

- [x] All current operations and shared criteria mapped to evidence.
- [x] Version, membership and allowed_all accepted; historical variants executed or explicitly mapped to remaining original-owner blockers.
- [x] State verification and cleanup actually recorded.
- [x] Ledger, source task records, coverage matrix, and dashboard synchronized.
- [x] No unsupported completion or publication claim.

Final status: **complete for current functional acceptance and evidence reconciliation**.
Next action: prep-021 must document the accepted 32-operation catalog and the ledger's explicit
limits. Broader original-owner variants H1..H5 remain open before unsupported release claims;
their acceptance is not inferred. Final release review stays with prep-009;
operational/recovery work remains deferred outside the current local-development roadmap.
No production rollout or publication was performed.
