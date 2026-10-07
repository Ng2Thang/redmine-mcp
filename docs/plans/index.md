# MCP tool roadmap

## Tool quality follow-up plan

The user requested five technical task plans on 2026-10-07, covering review items 1, 3, 4, 5
and 6: input-schema parity, membership batch budgets, request-body admission, declared upstream
field validation, and private SDK integration. These extend existing tools and runtime boundaries;
they do not add public operations. Review item 2 (unknown input/filter handling) and the separate
output-context/`extra_fields` discussion are outside these five tasks. Input unknown-property
policy and output field preservation must not be conflated.

The user subsequently authorized testing for all five tasks on 2026-10-07; current results
are in [Preparation regression testing](../testing/evidence/prep-022-026-testing.md).

The original planning assignment generated documents only. Subsequent explicitly assigned coding
stages and subsequent verification results are recorded below. The plan itself authorizes no
tests, fixtures, startup, Inspector, native mutations or deployment. Existing task histories,
waivers and current catalog acceptance remain intact.

| Preferred order | Review item | Task | Client outcome | Dependencies | Status | Blocker / next action |
|---|---|---|---|---|---|---|
| 1 | 1 / P1 | [prep-022-mcp-schema-parity](tasks/prep-022-mcp-schema-parity.md) | Invoke existing REST-valid null and union inputs through MCP without adapter restrictions | Accepted prep-020 contracts; existing prep-016/017 infrastructure | complete | Accepted 2026-10-07: 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed; owned cleanup passed; [verification](../testing/evidence/prep-022-026-testing.md) |
| 2 | 3 / P2 | [prep-023-membership-batch-budgets](tasks/prep-023-membership-batch-budgets.md) | Complete documented small ten-item membership fixtures with a dedicated bounded batch policy and accurate receipts | tool-033 current acceptance; prep-019 receipts; prep-020 baseline | complete | Accepted 2026-10-07: 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed; owned cleanup passed; [verification](../testing/evidence/prep-022-026-testing.md) |
| 3 | 4 / P2 | [prep-024-bounded-request-bodies](tasks/prep-024-bounded-request-bodies.md) | Reject oversized REST/MCP bodies before parsing while preserving ordinary uploads | Existing upload/middleware contracts; prep-020 baseline | complete | Accepted 2026-10-07: 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed; owned cleanup passed; [verification](../testing/evidence/prep-022-026-testing.md) |
| 4 | 5 / P2 | [prep-025-strict-upstream-fields](tasks/prep-025-strict-upstream-fields.md) | Receive trustworthy declared IDs, counts, flags and progress without coercion or receipt corruption | prep-020 resource contracts; prep-019 observation boundaries | complete | Accepted 2026-10-07: 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed; owned cleanup passed; [verification](../testing/evidence/prep-022-026-testing.md) |
| 5 | 6 / maintenance | [prep-026-mcp-sdk-compatibility-boundary](tasks/prep-026-mcp-sdk-compatibility-boundary.md) | Maintain pinned SDK hooks through one typed boundary with stable dispatch/discovery/lifecycle | prep-022 accepted; existing session/discovery/receipt baseline | complete | Accepted 2026-10-07: 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed; owned cleanup passed; [verification](../testing/evidence/prep-022-026-testing.md) |

Tasks prep-022 through prep-025 are independent correction tracks. Preferred order is priority
and integration guidance, not permission to execute a task range. prep-026 has a new hard
dependency on accepted prep-022 behavior and should normally run last to consolidate final hooks.
On 2026-10-07, the user explicitly authorized prep-026 coding before prep-022 acceptance,
keeping both tasks' testing pending. This waives coding order only; it does not establish
prep-022 acceptance or authorize SDK/runtime testing. The subsequent testing assignment
now accepts prep-022 and prep-026 as recorded above.
On 2026-10-07, the user explicitly requested numbering these five tasks from `prep-022`.
The former pilot task's number is reused with this authorization; filenames, task IDs,
dependencies and scenario/evidence IDs were renumbered together. This does not restore the
removed pilot workstream. Operational readiness, recovery, CI and production deployment remain
outside this plan.

## Sequential stabilization plan

The user requested task documents for the project-review priorities on 2026-10-07.
The original planning stage created documents only. Subsequent explicitly assigned implementation
and verification results are recorded below; CI activation, deployment and recovery remain separate.
The user subsequently removed the pilot-deployment workstream from the current roadmap.
Existing capability task IDs, contracts, waivers, and execution evidence are preserved.

Execute the following tasks one at a time. Write-outcome consistency comes first so the later
acceptance work verifies the corrected behavior. Each task separates implementation from
separately authorized verification. A finished coding stage does not satisfy a verification
dependency. The current stabilization sequence ends with the documentation task.

| Order | Review priority | Task | Client outcome | Depends on | Status | Blocker / next action |
|---|---|---|---|---|---|---|
| 1 | Inconsistent write outcomes | [prep-019-write-outcome-consistency](tasks/prep-019-write-outcome-consistency.md) | Treat mutation HTTP 5xx as uncertain while preserving individual/batch schemas, GET errors, and reconciliation | Existing writer/auth implementations; prep-016/017 baseline; prep-018 owned live infrastructure | complete | Accepted on 2026-10-07: full offline suite 1035 passed; transport/admission tests 22 passed; all 15 writers covered through REST/MCP; owned 7.0.2 real commit/HTTP-500 reconciliation and cleanup plus Inspector compatibility pass. Ruff/format/mypy and diff checks pass; proceed to prep-020 in its own assignment |
| 2 | Outstanding acceptance | [prep-020-current-catalog-acceptance](tasks/prep-020-current-catalog-acceptance.md) | Map current capabilities to actual evidence and close version, membership, allowed_all, and relevant historical gaps | prep-019 accepted; existing prep-018 isolated environment guidance | complete | Accepted 2026-10-07: [32-operation ledger](../testing/evidence/current-catalog-acceptance.md) audited; 1086 offline and 21 owned 7.0.2 live cases pass; TOOL-032-008/033-011, allowed_all and Inspector pass; broader original variants remain explicitly open in H1..H5; proceed to prep-021 without a release-readiness claim |
| 3 | Stale documentation | [prep-021-current-catalog-documentation](tasks/prep-021-current-catalog-documentation.md) | Make setup, writer configuration, security guidance, and release limitations match current behavior | prep-020 accepted | complete | Accepted 2026-10-07: current guides aligned with the 17-read/15-write ledger, pinned/personal writer modes and allowed_all; STAB-021-001..005 manual source/prose/example/link review and diff check pass. No tests or operational commands run; historical gaps and Unreleased status retained. Stabilization complete for local development; future feature or coverage work requires its own assignment |

These are shared stabilization prerequisites, not new Redmine tools. prep-020 coordinates
evidence without taking contract ownership from tool-032, tool-033, or the allowed_all follow-up.
prep-021 owns correction of existing guidance. Operational readiness, CI and recovery work
remain deferred outside the current local-development roadmap.
The original prep-009 final release review remains separate; completing
this plan does not publish a release or silently close its historical prerequisites.

Active task IDs are `prep-001` through `prep-026` and `tool-001` through `tool-035`.

## Issue estimates and general spent-time reporting

The user assigned both independent coding tasks on 2026-10-06. Test implementation, execution,
startup, Inspector and live verification require a separate testing assignment. Existing task
evidence and unrelated work remain intact.

| Task | Client outcome | Depends on | Status | Blocker / next action |
|---|---|---|---|---|
| [tool-034-list-issue-estimates](tasks/tool-034-list-issue-estimates.md) | Preserve issue-list estimates and missing-field evidence for truthful client totals | Existing issue reader, tool-015 detail models, prep-015 read budgets | complete | TOOL-034-001..005 passed: full offline suite 883 cases, owned 7.0.2 estimate parity/96-hour fixture, Inspector and static checks |
| [tool-035-list-time-entries](tasks/tool-035-list-time-entries.md) | Read caller-visible spent-time logs across projects, users and dates, including logs without issues | Existing time-entry reader, prep-015 budgets, tool-031 capability discovery | complete | TOOL-035-001..007 passed: full offline suite 883 cases, owned 7.0.2 scopes/date bounds/own-log visibility, Inspector numeric/me calls and static checks |

The [writer `allowed_all` configuration follow-up](writer-operations-allowed-all.md) implements
the user-requested option for every registered write operation. Testing remains pending.

The user-authorized [caller project capabilities](tasks/tool-031-list-my-project-capabilities.md) tool is
implemented: `list_my_project_capabilities` returns paginated unique project roles, merged
permissions and conditional/unknown candidate tools, with global tools separate. Centralized
read rules cover projects, issues, versions, categories, files, time entries and attachment
containers using the project permission union and visible-project/admin evidence.
Tool entries default to `operation_id` and `state`; `include_reasons=true` adds explanations.
Optional `project_id` and `operation_id` filters scope destination/action lookups; operation
matches default to conditional evidence, with `include_unknown=true` retaining unknowns.
The merged permission, read-rule and optional explanation follow-ups were inspected in source
only in the earlier implementation assignment. The subsequently authorized three-phase
testing record below establishes selected offline/live scenarios, including merged and
inherited roles and scoped permission revocation. Earlier static checks are recorded in its implementation record.

This dashboard tracks user-facing MCP capabilities. A Redmine REST endpoint is implementation
evidence inside a task, not the unit of planning. The task document owns its detailed status;
update this table in the same change when that status, blocker, or next action changes.
Active task IDs are `tool-001` through `tool-035` and `prep-001` through `prep-026`.
The retained stabilization follow-up consists of prep-019 through prep-021. The five
tool-quality plans are prep-022 through prep-026, added and renumbered at the user's request
on 2026-10-07.
On 2026-10-02, the user requested compact numbering after document tasks
were removed. Task filenames, dependencies, links, and scenario IDs were renumbered
together; earlier IDs remain available in Git history. The deleted `issues-000` through
`issues-008` IDs remain retired.

The next strictly sequential capability roadmap is specified in
[Redmine 7.0.2 files and issues](redmine-7-0-2-capabilities.md).
Its tasks are listed below. The 7.0.2 deployment target is configured and accepted;
the user waived actual runtime verification on 2026-10-02. Selected runtime scenarios now pass under prep-018; older broader acceptance criteria remain
tracked in their original task records.

Synthetic deployment: Redmine `7.0.2-bookworm` is pinned in `deploy/compose.test.yaml`.
Planning baseline: 2026-09-30. Task records below contain the implementation and acceptance
evidence completed since that baseline. Existing runtime configuration already has a
false-default write gate, but the currently deployed catalog remains read-only.

The original capability dashboards below retain historical task status and pending variants.
Current selected testing evidence is the [coverage matrix](testing-coverage.md) and the
prep-016 through prep-018 records dated 2026-10-06. Implementation-time statements about
unexecuted verification describe the earlier assignments.

## Earlier reader catalog and historical task status

| Tool | What a client can do today | Status |
|---|---|---|
| `list_projects` | Page through projects visible to the requesting Redmine user. | Implemented; runtime acceptance not established by this plan |
| `list_issues` | Page through issues by project, status, and assignee. | Implemented; extension task below |
| `get_issue` | Read one visible issue with journals and attachment metadata. | Implemented; extension task below |
| `get_current_user` | Identify the caller and read visible project memberships with roles. | Implementation finished; acceptance pending in tool-013 |
| `list_my_project_capabilities` | Read unique caller project roles, merged permissions and conditional/unknown tool candidates. | Aggregation implemented; follow-up checks and runtime acceptance pending separately authorized verification |

## Ordered task dashboard

| Order | Task | Client outcome | Depends on | Status | Blocker / next action |
|---|---|---|---|---|---|
| 1 | [prep-001-ruff-checks](tasks/prep-001-ruff-checks.md) | Repository static checks can assess later tool changes. | None | complete | `bash scripts/check.sh`, whitespace, and router contract checks pass. |
| 2 | [prep-002-offline-tests](tasks/prep-002-offline-tests.md) | Tool changes have credential-free automated verification. | prep-001 | complete | Locked offline REST/MCP suite, static checks, and package build pass. |
| 3 | [tool-001-list-issues-search](tasks/tool-001-list-issues-search.md) | Find issues by useful work filters and ordering. | prep-002 | complete | Offline, static, and marked synthetic Inspector checks pass. |
| 4 | [tool-002-get-issue-context](tasks/tool-002-get-issue-context.md) | Request the related context needed for one issue. | prep-002 | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). DETAIL-001 through DETAIL-004 pass offline. Same-reader journal IDs/private flags and empty allowed statuses match Redmine; contrasting ordinary-role visibility and nonempty transitions remain pending. |
| 5 | [tool-003-get-project](tasks/tool-003-get-project.md) | Read one visible project's details. | prep-002 | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). PROJECT-001 through PROJECT-003 pass offline. Visible-project mapping and marked restricted-project rejection pass for the existing live fixture; complete baseline acceptance remains pending. |
| 6 | [tool-004-list-issue-statuses](tasks/tool-004-list-issue-statuses.md) | Resolve status IDs and closed flags. | prep-002 | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). STATUS-001/002 pass offline. Six live statuses and closed flags match Redmine; the sampled issue has an empty allowed-status set, so the nonempty workflow comparison remains pending. |
| 7 | [tool-005-list-trackers](tasks/tool-005-list-trackers.md) | Resolve tracker IDs and supported fields. | prep-002 | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). TRACKER-001/002 pass offline. Three registry tracker IDs/names match Redmine; full comparison against visible project tracker settings and a clean live rerun remain pending. |
| 8 | [tool-006-list-issue-priorities](tasks/tool-006-list-issue-priorities.md) | Resolve priority IDs and the default. | prep-002 | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). PRIORITY-001/002 pass offline. Five registry priorities and default flags match Redmine; complete clean baseline acceptance remains pending. |
| 9 | [tool-007-list-project-versions](tasks/tool-007-list-project-versions.md) | Discover versions available to a project. | prep-002 | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). VERSION-002/003 pass offline, including strict collection counts. The sampled base project's empty version set matches Redmine; populated shared/private visibility under contrasting ordinary roles remains pending. |
| 10 | [tool-008-list-project-issue-categories](tasks/tool-008-list-project-issue-categories.md) | Discover categories available to a project. | prep-002 | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). CATEGORY-002/003 pass offline, including strict collection counts. Inspector and Redmine return 403 for the reader; a permitted populated-category/private-project fixture remains missing for CATEGORY-001/004. |
| 11 | [tool-009-list-issues-by-category](tasks/tool-009-list-issues-by-category.md) | Find all visible issues in a selected project category. | prep-002; tool-008 for category ID discovery | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). CATISSUE-001 through CATISSUE-004 pass offline. CATISSUE-005 remains blocked: the fixture records no categories and the reader lacks category-list permission. |
| 12 | [tool-010-list-issues-by-target-version](tasks/tool-010-list-issues-by-target-version.md) | Find visible issues in a Target version and optionally exclude subprojects. | prep-002; tool-007 for Target version ID discovery | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). TARGETISSUE-001 through TARGETISSUE-005 pass offline. Inspector and same-key Redmine return zero exact-project and seven descendant-inclusive History Alpha/Sprint 02 Bug matches with matching IDs/count/version membership. Full visibility acceptance and clean live rerun remain pending. |
| 13 | [tool-011-expose-issue-schedule-and-spent-hours](tasks/tool-011-expose-issue-schedule-and-spent-hours.md) | Read issue start/due dates and visible direct spent hours so clients can identify dated Bugs and sum their hours. | prep-002; tool-001 issue search; tool-010 exact-project scoping | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). DATE, HOURS, AGG, COMPAT, and MCP offline cases pass. Thirteen Operations Bugs have matching list date/hour fields and sampled detail fields. No issue qualifies for September 2026, so LIVE-001's nonempty hours aggregate remains pending. |
| 14 | [tool-012-list-issue-time-entries](tasks/tool-012-list-issue-time-entries.md) | Identify the users credited with visible spent hours on selected issues. | prep-002; tool-011 issue selection and direct-hours context | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). ENTRY, PAGE, AGG, AUTH, VIS, COMPAT, and MCP offline cases pass. Three live entries match Redmine by ID, issue, credited user, hours, date, and count. All-user completeness and the contrasting-role visibility matrix remain pending. |
| 15 | [tool-013-get-current-user](tasks/tool-013-get-current-user.md) | Identify the caller and their visible project memberships and roles. | prep-002; prep-003 identity foundation (runtime acceptance pending) | blocked | Offline acceptance expanded in prep-004 (356-case full suite passes). USER-001 through USER-009 executed variants pass offline. The live ordinary profile's public fields, ten memberships, and roles match Redmine. USER-010 remains blocked by the missing second ordinary personal key and other account/role variants. |

Tasks 3, 4, 11, 12, and 13 extend existing tools. Tasks 5 through 10, 14, and 15 add eight operations. Each task has one
contract owner; supporting model, service, gateway, route, and registration edits belong to that
owner. The issue extensions and lookup tasks may be implemented in any order after prep-002;
the table gives the preferred release order, not a code dependency.

## Runtime infrastructure work

| Task | Outcome | Status | Blocker / next action |
|---|---|---|---|
| [prep-003-runtime-foundation](tasks/prep-003-runtime-foundation.md) | Bound auth identity, strict service queries, bounded HTTP reads, exception/logging boundaries, lifecycle ownership, validated MCP exposure, and static architecture gate | blocked | Implementation accepted with testing pending. Expanded offline foundation checks and MCP startup fix pass under prep-004; remaining ordinary-account/live matrix pending. |

## Redmine 7.0.2 sequential capability roadmap

This roadmap plans fifteen operations and extends `list_issues` and `get_issue`.
The 7.0.2 image is pinned in the synthetic Compose deployment. Each active row
depends on accepted evidence and explicit user acceptance of its listed predecessor.
Unit testing requires separate user authorization for each task. The user waived
actual runtime verification on 2026-10-02; planned checks are not passing evidence.

| Order | Task | Client outcome | Depends on | Status | Blocker / next action |
|---|---|---|---|---|---|
| 1 | [prep-004-accept-existing-baseline](tasks/prep-004-accept-existing-baseline.md) | Accept the existing reader baseline | prep-002-offline-tests accepted | complete | User accepted the revised offline baseline by directing continuation to prep-005 on 2026-10-02. Live waiver and prior limitations retained; see [dated evidence](../testing/evidence/prep-004-verification.md). |
| 2 | [prep-005-redmine-7-0-2](tasks/prep-005-redmine-7-0-2.md) | Pin Redmine 7.0.2 | prep-004-accept-existing-baseline accepted | complete | User accepted the final 7.0.2 pin and waived actual runtime verification on 2026-10-02; live behavior remains unverified. |
| 3 | [tool-014-list-issues-associations](tasks/tool-014-list-issues-associations.md) | Extend issue lists with associations | prep-005-redmine-7-0-2 accepted | complete | User directed continuation without verification on 2026-10-02; static checks pass, but unit and live behavior remain unverified. |
| 4 | [tool-015-get-issue-write-context](tasks/tool-015-get-issue-write-context.md) | Expose issue write and file context | tool-014-list-issues-associations accepted | blocked | Implementation and static checks finished; user directed continuation to tool-016 with unit tests unexecuted and live verification waived. |
| 5 | [tool-016-list-document-categories](tasks/tool-016-list-document-categories.md) | List document categories | tool-015-get-issue-write-context continuation directed | blocked | Implementation finished; exact 7.0.2 source, Ruff, mypy, and final diff reviewed. TOOL-016-001 through TOOL-016-005 unexecuted; live verification waived. |
| 6 | [tool-017-list-project-files](tasks/tool-017-list-project-files.md) | List project files | tool-016-list-document-categories continuation directed | blocked | Implementation, static checks, and user review approved on 2026-10-02; TOOL-017-001 through TOOL-017-005 remain unexecuted. User directed continuation to tool-018. |
| 7 | [tool-018-get-attachment](tasks/tool-018-get-attachment.md) | Read attachment metadata | tool-017-list-project-files approved | blocked | Implementation, static checks, and user review approved on 2026-10-02; TOOL-018-001 through TOOL-018-005 remain unexecuted. User directed continuation to prep-006. |
| 8 | [prep-006-bounded-binary-downloads](tasks/prep-006-bounded-binary-downloads.md) | Bound binary download transport | tool-018-get-attachment approved | blocked | Implementation, static checks, and user review approved on 2026-10-02; offline/live verification remains unexecuted. User directed continuation to tool-019. |
| 9 | [tool-019-download-attachment](tasks/tool-019-download-attachment.md) | Download bounded attachment content | prep-006-bounded-binary-downloads approved | blocked | Implementation, static checks, and user review approved on 2026-10-02; TOOL-019-001 through TOOL-019-005 remain unexecuted. User directed continuation to prep-007. |
| 10 | [prep-007-restricted-writer-foundation](tasks/prep-007-restricted-writer-foundation.md) | Establish restricted writer runtime | tool-019-download-attachment approved | blocked | Implementation and static checks finished; user review and separately authorized offline/synthetic verification pending. |
| 11 | [prep-008-synthetic-writer-verification](tasks/prep-008-synthetic-writer-verification.md) | Prepare disposable writer verification | prep-007-restricted-writer-foundation approved | blocked | Controlled fixture and evidence plan prepared; review and separately authorized execution pending. |
| 12 | [tool-020-upload-attachment](tasks/tool-020-upload-attachment.md) | Upload bounded attachment bytes | prep-008 plan committed; execution pending | blocked | Implementation and static checks approved by user on 2026-10-02; offline/synthetic permission and state evidence pending. Continue to tool-021. |
| 13 | [tool-021-add-project-file](tasks/tool-021-add-project-file.md) | Attach upload as project file | tool-020 coding approved; tests pending | blocked | Implementation and static checks approved by user on 2026-10-02; offline/synthetic permission and state evidence pending. Continue to tool-022. |
| 14 | [tool-022-update-attachment](tasks/tool-022-update-attachment.md) | Edit attachment metadata | tool-021 coding approved; tests pending | blocked | Implementation and static checks approved by user on 2026-10-05 (commit `e248644`). Requested tool-017 through tool-022 coding range finished; separately authorized offline/synthetic container permission and state checks remain pending. |
| 15 | [tool-023-delete-attachment](tasks/tool-023-delete-attachment.md) | Delete one attachment | tool-022 coding approved; tests pending | blocked | User approved commit `c6ef155` on 2026-10-05 and directed tool-024 continuation; separately authorized TOOL-023-001 through TOOL-023-005 verification pending. |
| 16 | [tool-024-create-issue](tasks/tool-024-create-issue.md) | Create or natively copy an issue | tool-023 coding approved; tests pending | blocked | User approved commit `d600fda` on 2026-10-05 and directed tool-025; separately authorized TOOL-024-001 through TOOL-024-005/native copy state verification pending. |
| 17 | [tool-025-update-issue](tasks/tool-025-update-issue.md) | Update issue fields or add a note | tool-024 coding approved; tests pending | blocked | User approved commit `27cae75` on 2026-10-05 and directed tool-026; separately authorized TOOL-025-001 through TOOL-025-005/permission and state verification pending. |
| 18 | [tool-026-update-issue-note](tasks/tool-026-update-issue-note.md) | Edit a journal note | tool-025 coding approved; tests pending | blocked | User approved commit `6aef9de` on 2026-10-05 and directed tool-027; separately authorized TOOL-026-001 through TOOL-026-005/journal permission and state verification pending. |
| 19 | [tool-027-create-issue-relation](tasks/tool-027-create-issue-relation.md) | Create one issue relation | tool-026 coding approved; tests pending | blocked | User approved commit `a7f89f8` on 2026-10-05 and assigned tools 028-030; separately authorized TOOL-027-001 through TOOL-027-005/permission, scheduling, and state verification pending. |
| 20 | [tool-028-delete-issue-relation](tasks/tool-028-delete-issue-relation.md) | Delete one issue relation | tool-027 coding approved; tests pending | blocked | User approved commit `f21140d` on 2026-10-05 and requested continuation; separately authorized TOOL-028-001 through TOOL-028-005/permissions, journals, and state verification pending. |
| 21 | [tool-029-add-issue-watcher](tasks/tool-029-add-issue-watcher.md) | Add one watcher | tool-028 coding approved; tests pending | blocked | User approved commit `b930d8c` on 2026-10-05 and directed tool-030; separately authorized TOOL-029-001 through TOOL-029-005/watcher eligibility, permissions, and membership verification pending. |
| 22 | [tool-030-remove-issue-watcher](tasks/tool-030-remove-issue-watcher.md) | Remove one watcher | tool-029 coding approved; tests pending | blocked | Implementation and static checks finished on 2026-10-05; user review and separately authorized TOOL-030-001 through TOOL-030-005/removal permissions, no-op behavior, and membership verification pending. |
| 23 | [prep-009-release-acceptance](tasks/prep-009-release-acceptance.md) | Review complete Redmine 7.0.2 release | tool-030-remove-issue-watcher accepted | blocked | Await tool-030-remove-issue-watcher acceptance and exact 7.0.2 evidence. |

## Multi-user writer authorization roadmap

The user requested this plan on 2026-10-05. The
[multi-user writer design](multi-user-writer-authorization.md) extends the existing writer;
it adds no new public operation and preserves all earlier task IDs and evidence.
Phase 1 permits explicitly configured personal-key authentication with the existing common
catalog. Phase 2 adds project/resource capability checks and caller-specific candidate discovery.
Reader isolation and the deployment operation ceiling remain required. Planning authorizes no
implementation, unit tests, startup, Inspector, or synthetic mutations.

| Order | Task | Client outcome | Depends on | Status | Blocker / next action |
|---|---|---|---|---|---|
| 1 | [prep-010-permission-session-contract](tasks/prep-010-permission-session-contract.md) | Resolve permission evidence, resource context, and session integration | Existing prep-003/005/007 implementations; prior acceptance limitations retained | complete | [Dated contract review](../reviews/prep-010-contract-review.md) resolves all eleven operations, partial evidence, raw discovery handler and SDK session binding. Implement prep-011 next. |
| 2 | [prep-011-multi-user-writer-auth](tasks/prep-011-multi-user-writer-auth.md) | Authenticate personal keys and restrict writes independently of reads | prep-010 session contract; existing prep-007 implementation | blocked | Implementation and Ruff/mypy/diff checks pass. AUTH-001 through AUTH-008 and metadata packaging checks assigned to prep-014; continue prep-012 coding under the full-range assignment. |
| 3 | [prep-012-project-resource-authorization](tasks/prep-012-project-resource-authorization.md) | Check caller capabilities in the actual target context | prep-010 resolved permission matrix; prep-011 implementation | blocked | All eleven service checks, typed evidence and same-key target/role gateway implemented; Ruff/mypy/AST/diff checks pass. PERM-001 through PERM-009 pending in prep-014; continue prep-013 coding. |
| 4 | [prep-013-caller-tool-discovery](tasks/prep-013-caller-tool-discovery.md) | Discover tools relevant to the caller without changing shared registry | prep-010 adapter contract; prep-011/012 implementations | blocked | Raw SDK discovery handler and immutable schema superset implemented; Ruff/mypy/AST/diff checks pass. DISC-001 through DISC-007 and runtime acceptance assigned to prep-014. |
| 5 | [prep-014-multi-user-writer-acceptance](tasks/prep-014-multi-user-writer-acceptance.md) | Verify caller isolation, permissions, discovery, and resulting write state | prep-011/012/013 implemented; prep-002 baseline; prep-008 fixture guidance; separate testing authorization | blocked | User clarified that the implementation request did not authorize tests. Agent-created tests/tooling removed and existing test edits restored. No further unit tests, Inspector, synthetic seeding or live verification without explicit separate approval. |

The old prep-009 release acceptance remains scoped to its existing roadmap. prep-014 owns
acceptance of the multi-user change; old waivers and passing checks are not new runtime evidence.

Execution assignment (2026-10-05): the user requested implementation of prep-010 through prep-014,
quality checks and one commit per prep named `feat: prep_0xx <context>`. Coding stages remain
separate from prep-014's explicit verification scope. No production rollout is included.

## Caller project capabilities

| Order | Task | Client outcome | Depends on | Status | Blocker / next action |
|---|---|---|---|---|---|
| 1 | [tool-031-list-my-project-capabilities](tasks/tool-031-list-my-project-capabilities.md) | Inspect caller roles, permissions and candidate tools per visible project | Existing project reader and prep-010/011/012/013 implementations | blocked | Implementation, review fix and static checks finished; runtime acceptance awaits separately authorized verification. |

## Bounded Redmine reads

The user authorized prep-015 coding on 2026-10-05. No user quotas, query state, count/statistics
tool or generated export is included. The physical-request semaphore is shared per process;
large query previews require narrowing before continuation, and attachments return links only.

| Order | Task | Client outcome | Depends on | Status | Blocker / next action |
|---|---|---|---|---|---|
| 1 | [prep-015-bounded-redmine-reads](tasks/prep-015-bounded-redmine-reads.md) | Bound pagination scans, upstream concurrency and logical read work; retrieve browser attachment links | Existing prep-003/005/010-013 and tool-031 implementations; prep-002 for testing | blocked | Implementation finished; timeout-boundary, shared proxy-admission and pagination-guidance review fixes applied; user-approved defaults are concurrency 50, admission 30s, read attempts 30 and aggregate deadline 90s. Ruff lint/format, mypy and diff whitespace checks pass. TEST-001 through TEST-006, updated old paging/download expectations and synthetic acceptance require separate verification authorization. |

## Three-phase application testing

The user explicitly authorized implementation and execution on 2026-10-05. The three directories
are unit, offline integration and opt-in live E2E. [Coverage matrix](testing-coverage.md) maps all
15 reader tools, eleven writers and shared runtime scenarios. Historical evidence is preserved.

| Order | Task | Outcome | Depends on | Status | Next action |
|---|---|---|---|---|---|
| 1 | [prep-016-unit-testing](tasks/prep-016-unit-testing.md) | Validate service/model/policy logic using fake ports | Existing prep-002 baseline | complete | 102 unit cases and static checks pass; see task evidence. |
| 2 | [prep-017-offline-integration-testing](tasks/prep-017-offline-integration-testing.md) | Verify current REST/MCP tools against mocked Redmine | prep-016 | complete | 395 integration cases and live opt-in gate pass. |
| 3 | [prep-018-live-e2e-testing](tasks/prep-018-live-e2e-testing.md) | Verify real permissions, write state and owned cleanup | prep-017 | complete | 14 live cases, Inspector, browser and owned cleanup pass. |

The existing shared synthetic environment runs 6.0.5. New live acceptance uses a separate
`redmine-mcp-e2e` Compose project on localhost port 3001, with its own labeled database/files
volumes and guarded fixture scripts. Existing containers, credentials and data are preserved.

## Target version creation

| Task | Client outcome | Dependencies | Status | Blocker / next action |
|---|---|---|---|---|
| [tool-032-create-project-version](tasks/tool-032-create-project-version.md) | Create an open, unshared Target version; return readable existing versions with an explicit duplicate error | Existing project reader; prep-007/010-013 writer implementations; prep-016-018 testing infrastructure | complete | Current acceptance reconciled in prep-020 on 2026-10-07: 1086 offline/21 owned live cases pass; operation-specific 7.0.2 native state/roles/side effects, Inspector and disposable cleanup pass. Historical records remain in the task; current source-linked evidence is in the [ledger](../testing/evidence/current-catalog-acceptance.md) |

## Project membership management

The user selected one combined task for four separate MCP tools. Shared models, batch preflight,
permission integration, and receipts belong to that task; no separate preparation task is assigned.
List remains available on the reader; user-only writes require the restricted enabled writer.

| Task | Client outcome | Dependencies | Status | Blocker / next action |
|---|---|---|---|---|
| [tool-033-project-members-management](tasks/tool-033-project-members-management.md) | List project memberships and add, update, or delete user memberships across selected projects with whole-batch preflight and individual results | Existing project reader; prep-007/010-013 writer/auth/discovery implementations; prep-015 read budgets; prep-016-018 testing infrastructure | complete | Current acceptance reconciled in prep-020 on 2026-10-07: 1086 offline/21 owned live cases pass; operation-specific 7.0.2 native state/roles/side effects, Inspector and disposable cleanup pass. Historical records remain in the task; current source-linked evidence is in the [ledger](../testing/evidence/current-catalog-acceptance.md) |

## Future ideas, not assigned tasks

Issue deletion, administration, native Gantt API support, wiki content, and
search remain outside this roadmap. Do not restore the deleted endpoint
backlog or add operations solely because Redmine exposes them.

## Status and handoff rules

Use `discovery`, `specified`, `planned`, `implementing`, `verifying`, `complete`, or `blocked` as
defined in the task template. `planned` means the public contract is decision-complete, even if a
dependency is pending. `blocked` names missing evidence or an unresolved decision. `complete`
requires implemented behavior and passing acceptance evidence, not a finished document or static
checks alone. Before handing a task to an implementation agent, read its dependencies, exact next
action, and latest evidence; update both the task and this dashboard after the handoff.
