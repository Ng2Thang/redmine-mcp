# Issues implementation backlog

## Scope and provenance

Full issues.md assignment: seven endpoints and all source groups SRC-ISSUES-001 through
SRC-ISSUES-020 in [analysis](analysis.md). Source SHA256:
C3CB6636CFB8E5E548D934ACC790BE87B8FAFF562DB5A270A5977832BD9EB382.
Planning date: 2026-09-29. Target: Redmine 6.0.5-bookworm.
Existing IDs/evidence: no prior docs/plans directory existed; baseline unrelated changes preserved.

## Dependency order

| Order | Task | Outcome | Source/prerequisite | Dependencies | Planning status | Coding blocker |
|---|---|---|---|---|---|---|
| 1 | [issues-000-policy](issues-000-policy.md) | Reconcile current capabilities and authorized future scope | Workflow: Authorized scope and first implementation prerequisite | None | blocked: coding portion finished | Python 3.13/static checks and acceptance pending |
| 2 | [issues-001-testing-baseline](issues-001-testing-baseline.md) | Establish mandatory offline issue-tool testing foundation | Workflow: Authorized scope and first implementation prerequisite, items 1-2 | issues-000-policy | planned | Separate testing assignment required |
| 3 | [issues-002-write-access](issues-002-write-access.md) | Configure an opt-in separate writer deployment | Workflow item 3; owner decision 2026-09-29: separate writer deployment | issues-000-policy | blocked: coding portion finished | Python 3.13/static checks and acceptance pending |
| 4 | [issues-003-list](issues-003-list.md) | Extend issue listing filters, sorting, includes, and response fields | SRC-ISSUES-001 through SRC-ISSUES-007; SRC-ISSUES-020 | issues-000-policy, issues-001-testing-baseline | planned | Mandatory testing foundation absent |
| 5 | [issues-004-detail](issues-004-detail.md) | Expose supported issue detail expansions | SRC-ISSUES-008 through SRC-ISSUES-012; SRC-ISSUES-020 | issues-000-policy, issues-001-testing-baseline, issues-003-list | planned | Mandatory testing foundation absent |
| 6 | [issues-005-create](issues-005-create.md) | Create an issue using a restricted writer deployment | SRC-ISSUES-013; SRC-ISSUES-014 attachment boundary; SRC-ISSUES-020 | issues-001-testing-baseline, issues-002-write-access, issues-004-detail | blocked | Named target evidence plus prerequisite completion |
| 7 | [issues-006-update](issues-006-update.md) | Update issue attributes and journal notes | SRC-ISSUES-015; SRC-ISSUES-016; SRC-ISSUES-014 attachment boundary | issues-001-testing-baseline, issues-002-write-access, issues-005-create | blocked | Named target evidence plus prerequisite completion |
| 8 | [issues-007-delete](issues-007-delete.md) | Delete an issue with explicit destructive semantics | SRC-ISSUES-017 | issues-001-testing-baseline, issues-002-write-access, issues-005-create | blocked | Named target evidence plus prerequisite completion |
| 9 | [issues-008-watchers](issues-008-watchers.md) | Add and remove issue watcher membership | SRC-ISSUES-018; SRC-ISSUES-019 | issues-001-testing-baseline, issues-002-write-access, issues-005-create | blocked | Named target evidence plus prerequisite completion |

## Source coverage

| Source IDs | Capability | Disposition | Contract owner/existing evidence | Limitation |
|---|---|---|---|---|
| 001-002 | Existing pagination/filters | already implemented | router/service/port/adapter list_issues | Static coverage; regression scenarios planned |
| 003-007 | Expanded search/includes/common fields | covered by plan | [list](issues-003-list.md) | Foundation dependency; default preserved |
| 008 | Existing issue read | already implemented | get_issue end-to-end and allowlist | Static coverage only |
| 009-011 | Configurable supported detail includes | covered by plan | [detail](issues-004-detail.md) | Workflow and visibility upstream-owned |
| 012 | Reactions and journal reactions | deferred | [detail](issues-004-detail.md) | Requires 7.1.0; target 6.0.5 unchanged |
| 013 | Create fields/watchers/privacy/effort | blocked | [create](issues-005-create.md) | Target safe attributes and testing/access prerequisites |
| 014 | Issue attachments on create/update | blocked | [create](issues-005-create.md), [update](issues-006-update.md) | Token-consumption contract evidence missing; uploading files is linked-resource API, deferred |
| 015-016 | Editable fields/notes/privacy | blocked | [update](issues-006-update.md) | Null/clearing, success and private-note evidence needed |
| 017 | Issue deletion | blocked | [delete](issues-007-delete.md) | Exact success/cascade evidence needed |
| 018-019 | Add/remove watcher | blocked | [watchers](issues-008-watchers.md) | Target watcher-controller permission/status evidence unavailable |
| 020 | JSON/XML | covered by plan | JSON upstream adapter retained | XML is an alternative Redmine representation, no MCP/XML tool needed |

## Decisions and execution boundaries

Owner explicitly chose separate opt-in restricted writer deployment on 2026-09-29.
REDMINE_WRITE_ENABLED defaults false; each deployment retains one shared credential/token;
writer uses distinct restricted key/token. Current reader behavior/catalog is preserved.

Policy reconciliation and the runtime write gate are independent non-testing prerequisite
portions. Coding those does not complete the entire shared prerequisite. Feature tool edits
depend on the required pytest/pytest-asyncio/offline baseline, which cannot be created in
this coding-without-tests assignment. Synthetic writer credentials/fixtures and live permission
verification likewise require a separate testing assignment.

Dependency graph is acyclic; shared Issue model extensions belong to list then detail.
All tasks preserve source/runtime evidence and planned tests. Review occurs before coding;
readiness is a plan verdict, not acceptance. No tests or live calls are authorized here.

## Future verification and next actions

Execution update 2026-09-29: source-based self-review and one correction/re-review cycle complete.
Policy documentation and runtime write-gate/configuration portions coded; statuses blocked for
missing Python 3.13/static tooling and acceptance. The overall feature is partially implemented;
no expanded reads or mutation tools were coded. Ruff lint/format and mypy attempted with offline,
no-sync, download-disabled uv: all stopped before execution due to absent Python 3.13.
git diff --check passed. Testing and live verification remain pending; no shared baseline was
installed. Readiness/details/history are in review.md and task implementation records.

Perform source-based task review; correct actionable defects in at most two cycles.
Assign ready policy and runtime-gate prerequisite tasks to coding skill, without installing
test dependencies. Record actual static results. Separately assign issues-001-testing-baseline
and synthetic writer setup, resolve remaining version-specific contracts, then resume dependent
feature tasks. Acceptance remains pending until planned offline/live scenarios pass.
