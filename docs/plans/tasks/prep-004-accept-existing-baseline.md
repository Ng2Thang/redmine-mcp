# prep-004-accept-existing-baseline: Accept existing reader baseline

Historical acceptance record: the live samples below predate the 7.0.2 pin.
They do not establish runtime acceptance for the current target.

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-004-accept-existing-baseline |
| Assigned capability | Reconcile acceptance of prep-003 and tool-002 through tool-013 without altering their historical evidence. |
| Type / access / destructive effects | Shared prerequisite / planning or infrastructure / None in this documentation task |
| Status | complete - revised offline scope accepted |
| Dependencies | [prep-002-offline-tests](prep-002-offline-tests.md); predecessor acceptance required |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2 target; repository pins 7.0.2 |
| Last updated | 2026-10-02, Codex |
| Progress summary | 356 offline tests, static checks, and source/wheel builds pass. Authorized MCP startup race fix verified. User waived remaining prep-004 live checks on 2026-10-02; prior partial evidence retained. |
| Blocker / next action | User accepted the revised offline baseline by directing continuation to prep-005 on 2026-10-02. Proceed under prep-005's independent release and verification requirements. |

## 2. Discovery and evidence

Current evidence is in [the 2026-10-02 verification ledger](../../testing/evidence/prep-004-verification.md).
The inventory and execution rows dated 2026-10-01 below remain historical evidence.
On 2026-10-02 the user requested skipping live checks. Remaining live procedures and their
fixture requirements are waived for prep-004. Acceptance now uses the passing offline suite,
static checks, builds, preserved evidence, and verified runtime fix. This waiver does not apply
to later tasks or establish live permission, data completeness, or Redmine 7.0.2 compatibility.

Reconcile acceptance of prep-003 and tool-002 through tool-013 without altering their historical evidence. Inventory unfinished criteria and exact blockers; obtain separate testing authorization; run only authorized offline and synthetic cases; update each existing task and the dashboard from actual evidence.

| Source | Checked | Evidence and limitation |
|---|---|---|
| [Current roadmap](../index.md) | 2026-10-01 | Existing task status and architecture; no pending acceptance is treated as passed. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | Redmine 7.0.2 is now pinned; prior live samples do not establish its behavior. |
| [Tool reference](../../tool-reference.md) | 2026-10-01 | Existing public catalog is the compatibility baseline. |

### Existing acceptance inventory (2026-10-01)

The linked task records are the source of truth for procedures and historical results. This
inventory does not change their status or count static checks as runtime acceptance.

| Existing task | Recorded status and passing evidence | Pending acceptance scenarios |
|---|---|---|
| [prep-003](prep-003-runtime-foundation.md) | Blocked; static checks and unauthenticated startup/shutdown smoke pass | FOUNDATION-001 through FOUNDATION-012; FOUNDATION-007 includes synthetic Inspector and ordinary-key visibility |
| [tool-002](tool-002-get-issue-context.md) | Blocked; implementation finished | DETAIL-001 through DETAIL-005; DETAIL-005 requires synthetic private-journal and allowed-status checks |
| [tool-003](tool-003-get-project.md) | Blocked; implementation finished | PROJECT-001 through PROJECT-004; PROJECT-004 requires visible/hidden synthetic projects |
| [tool-004](tool-004-list-issue-statuses.md) | Blocked; implementation finished | STATUS-001 through STATUS-003; STATUS-003 compares synthetic allowed statuses |
| [tool-005](tool-005-list-trackers.md) | Blocked; implementation finished | TRACKER-001 through TRACKER-003; TRACKER-003 compares project tracker settings |
| [tool-006](tool-006-list-issue-priorities.md) | Blocked; implementation finished | PRIORITY-001 through PRIORITY-003; PRIORITY-003 checks synthetic default priority |
| [tool-007](tool-007-list-project-versions.md) | Blocked; implementation finished | VERSION-001 through VERSION-004; VERSION-004 checks shared/private synthetic visibility |
| [tool-008](tool-008-list-project-issue-categories.md) | Blocked; implementation finished | CATEGORY-001 through CATEGORY-004; CATEGORY-004 checks private-project visibility |
| [tool-009](tool-009-list-issues-by-category.md) | Blocked; static checks pass | CATISSUE-001 through CATISSUE-005; CATISSUE-005 requires synthetic membership/count/permission checks |
| [tool-010](tool-010-list-issues-by-target-version.md) | Blocked; static checks pass | TARGETISSUE-001 through TARGETISSUE-006; TARGETISSUE-006 requires synthetic exact/descendant queries |
| [tool-011](tool-011-expose-issue-schedule-and-spent-hours.md) | Blocked; static checks pass | DATE-001 through DATE-003, HOURS-001 through HOURS-003, AGG-001 through AGG-002, COMPAT-001, MCP-001, LIVE-001 |
| [tool-012](tool-012-list-issue-time-entries.md) | Blocked; static checks pass | ENTRY-001 through ENTRY-004, PAGE-001, AGG-001, AUTH-001, VIS-001, COMPAT-001, MCP-001, LIVE-001 |
| [tool-013](tool-013-get-current-user.md) | Blocked; static checks pass | USER-001 through USER-010; USER-010 requires two ordinary synthetic accounts |

The pending set contains 81 named scenarios across 13 task records. Existing static evidence
varies by task and must be read in each linked record before accepting that task. The current
prior live samples can inform the reader baseline only; they cannot establish Redmine 7.0.2 behavior.
The original offline files covered the earlier generic baseline and issue search. The added
reader cases partially cover lookup mapping, project detail, current-user selection, and
time-entry mapping, but do not complete these 81 scenario groups. Several older task contracts
still say bearer token, while the accepted runtime implementation requires a per-user
`X-Redmine-API-Key`; reconcile those
forward-looking contracts before full acceptance without rewriting historical execution notes.

Decisions: this prerequisite owns no public MCP operation; prep-003 and tool-002..tool-013 must be
reviewed without rewriting prior evidence. The user authorized this prep-004 verification stage
on 2026-10-01. Redmine 7.0.2 runtime acceptance remains a later prerequisite for prep-005.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Reconcile acceptance of prep-003 and tool-002 through tool-013 without altering their historical evidence. |
| REQ-002 | Inventory unfinished criteria and exact blockers; obtain separate testing authorization; run only authorized offline and synthetic cases; update each existing task and the dashboard from actual evidence. |
| REQ-003 | Scope and existing capability compatibility are preserved; evidence is dated and redacted. |

In scope: Existing task records, dashboard links, and authorized offline/read-only acceptance.
The original scope excluded runtime code changes; on 2026-10-02 the user explicitly authorized
the focused MCP startup race fix and its verification. No public API contract changes were made.
Out of scope: unrelated Redmine APIs, an administrator
production credential, and claims based on unrun checks.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP name / operation ID / REST route | N/A - shared prerequisite |
| Inputs | Existing task criteria, evidence records, and separately authorized verification procedures |
| Outputs | Verified offline reader baseline, static/build results, dated scenario coverage and limitations; remaining live checks explicitly waived and earlier evidence preserved. |
| Access | No new public permission |
| Version support | 7.0.2 target; exact target evidence is required before completion. |
| Errors | Record failed prerequisite or recovery as blocked; never fabricate a successful result. |

Write semantics: N/A - no Redmine mutation belongs to this planning task.

Specification exit check: the prerequisite's procedure and expected evidence
are assigned. Exact version and execution evidence remain pending.

## 5. Implementation plan

1. Audit the existing task records and preserve their historical evidence. Completed above.
2. Obtain separate authorization for the prep-004 verification stage. Completed 2026-10-01.
3. Run the linked offline scenario groups against fake settings, MockTransport, ASGI lifespan,
   and MCP SDK sessions; use no real credentials. The expanded 356-case suite passes;
   named-scenario coverage and remaining variants are recorded in the verification ledger.
4. In the authorized live stage, inspect all existing tools under ordinary keys on
   the previously marked synthetic environment. Resolve fixture IDs at runtime; do not seed, reset,
   restore, or mutate Redmine for a reader check. Record unavailable fixtures as limitations.
5. Record dated commands, redacted actual results, failures, and recovery in each original task;
   synchronize its dashboard row. Preserve any existing passing static evidence.
6. Compare the public reader catalog, defaults, and ordinary-user visibility with the current
   tool reference. Mark prep-004 complete only when its criteria pass, then request user acceptance
   before prep-005 begins.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Pending baseline scenarios and prior passing evidence are inventoried without altering original records. | Inventory and 2026-10-02 ledger; pass |
| AC-002 | REQ-002 | Approved offline baseline has dated results, catalog/startup checks, and disclosed scenario limits; remaining live procedures are explicitly waived. | 356 tests pass; remaining live checks waived by user, 2026-10-02 |
| AC-003 | REQ-003 | Existing tools and unrelated state remain compatible in the approved verification scope; failures and unverified live behavior are reported. | Offline/static/build pass; historical live comparisons partial and retained |

Each criterion requires a dated procedure and redacted actual result. A draft
or static check alone does not pass acceptance.

## 7. Test plan and execution record

The user authorized this verification stage on 2026-10-01 and requested continuation on
2026-10-02. The original 81-scenario inventory is retained; current executed coverage and
remaining gaps are in the dated ledger. For prep-004-accept-existing-baseline, verify:
- Success: All required old baseline scenarios have dated, redacted results; current catalog and startup work under ordinary caller keys; unresolved original tasks remain blocked.
- Failure: unavailable artifact, rejected permission, malformed response,
  timeout, or failed recovery as applicable; record a blocker.
- Compatibility: compare existing reader catalog and outcomes before/after.
- Synthetic: use the marked isolated environment only after separate authorization.

| Evidence ID | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-001 | `bash scripts/check.sh` in Git Bash after test-fixture repair and new reader cases | Ruff, format (158 files), mypy (79 source files), architecture gate pass | Pass, 2026-10-01 |
| EVID-002 | `uv run --frozen pytest -q --tb=short` in Git Bash | 46 cases pass; one Pydantic deprecation warning. Initial run had 30 authentication-fixture failures; the old bearer fixture was updated to the current personal-key contract. New cases cover populated/empty/malformed lookups, project detail/count, current-user selected fields, and time-entry mapping/cross-issue rejection. The 81 named scenario groups are not fully covered. | Partial, 2026-10-01 |
| EVID-003 | Inspector 2.8.0 against previously marked synthetic fixture via local app on port 18080 and restricted reader key | 11 tools discovered. Ten sample calls succeeded; category lookup returned 403 for reader and succeeded for admin. Read-only REST health/projects/issues returned 200; visible issue count was 391. No second ordinary key or complete permission matrix checked. | Partial, 2026-10-01 |
| EVID-004 | Read-only audit of prep-003 and tool-002 through tool-013 task records; compare scenario IDs and statuses with dashboard | 13 records blocked; pending groups listed above; no execution claimed | Audit complete |
| EVID-005 | Inspect the controller and permission mapping in the previously observed synthetic container; compare category GET under reader and admin keys | Controller calls `authorize`; `lib/redmine/preparation.rb` maps issue-category index to `manage_categories`. Reader received 403 on 11 visible projects; admin received 200 on a sampled project. This is expected for the restricted reader role, not category-content acceptance for that role. | Permission boundary observed, 2026-10-01 |
| EVID-006 | Read-only comparison of one marked history issue's time-entry page through app REST and Redmine REST under the same reader key | Issue 151 had three visible entries; IDs and count matched. Inspector invoked the tool separately on another visible issue. Credited-user/hours/date comparison and complete visibility remain pending. | Partial, 2026-10-01 |
| EVID-007 | Inspect only synthetic credential artifact field names; do not print values | The local artifact exposes a restricted reader key and an administrator key. Other named ordinary accounts are recorded by user ID without personal keys; the two-ordinary-account Inspector scenarios cannot be completed from the current artifact alone. | Fixture gap, 2026-10-01 |
| EVID-008 | `uv run --frozen pytest -q --tb=short -p no:cacheprovider` in Git Bash | 356 tests pass in 43.32 seconds; one existing Pydantic deprecation warning. Runtime/reader cases and limitations are mapped in the dated ledger. | Pass for executed offline suite, 2026-10-02 |
| EVID-009 | `bash scripts/check.sh`, `uv build`, `git diff --check` | Ruff lint/format, mypy (79 source files), architecture gate (79 runtime modules), source/wheel build, and whitespace checks pass. | Pass, 2026-10-02 |
| EVID-010 | Concurrent first MCP connections; authorized runtime correction and deterministic readiness/cleanup checks | Reproduced an SDK startup race producing 500; lifespan now waits for manager readiness. Concurrent identities, failed/cancelled startup, and open-session shutdown pass. | Fixed and verified, 2026-10-02 |
| EVID-011 | Inspector 2.8.0 and same-key Redmine REST on previously marked synthetic fixture; temporary localhost app | Catalog, profile, projects, registries, time-entry fields, and exact/descendant version comparisons recorded. Category access is 403; only one ordinary key and no qualifying September Bugs. Full matrix and clean rerun remain pending. | Partial, 2026-10-02 |
| EVID-012 | User decision to skip prep-004 live checks | Remaining live matrix, fixture acquisition, and clean Inspector rerun waived. Passing offline/static/build evidence is the revised acceptance scope; no unrun check is recorded as passed. | Scope revised, 2026-10-02 |

## 8. Implementation and review record

The bullets below describe the earlier 2026-10-01 stage. The 2026-10-02 continuation added
310 offline cases, retained the prior 46, reconciled future personal-key contracts, and fixed
the startup race with explicit user authorization. See the ledger for current results and
exact gaps. No Redmine writes, dependency changes, staging, or commits were performed.

- Changes made: audited existing task records, repaired test fixtures for per-user keys, recorded
  partial verification, and synchronized dashboard status. The local application was started for
  read-only synthetic checks; no seed, reset, restore, or Redmine write occurred.
- Static checks and baseline automated tests: pass as EVID-001/002; the named scenario suite is
  absent and therefore cannot be inferred from the baseline pass.
- Startup, Inspector, and live state checks: partial as EVID-003/005/006.
- Remaining blocker: implement and run the 81 named scenarios, finish synthetic account and
  fixture comparisons (including a second ordinary personal key), reconcile stale auth wording,
  then obtain user acceptance.

## 9. Completion and handoff

- [x] Required prerequisite implemented or performed within the revised offline scope.
- [x] Revised acceptance criteria have passing evidence and an explicit live-check waiver.
- [x] Authorized offline verification and applicable static checks pass.
- [x] Offline compatibility and lifecycle recovery checks pass.
- [x] Dashboard and documentation match actual evidence.
- [x] User accepts this task before the next task starts (2026-10-02 instruction to continue implementation of prep-005).

Final status: **complete - revised offline scope accepted on 2026-10-02**.
The remaining live procedures are waived for this task. Earlier fixture-file questions are
superseded by that waiver. Original reader records retain their historical live limitations.
Acceptance continuation (2026-10-02): the user directed implementation of prep-005, accepting
this task's revised offline scope. Prior evidence and live limitations remain unchanged.

Next action: proceed to prep-005 under its own requirements. The sequential acceptance gate
remains in effect for later tasks.
