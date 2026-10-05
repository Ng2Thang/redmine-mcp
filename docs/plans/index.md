# MCP tool roadmap

This dashboard tracks user-facing MCP capabilities. A Redmine REST endpoint is implementation
evidence inside a task, not the unit of planning. The task document owns its detailed status;
update this table in the same change when that status, blocker, or next action changes.
Active task IDs are continuous: `tool-001` through `tool-030` and `prep-001` through
`prep-014`. On 2026-10-02, the user requested compact numbering after document tasks
were removed. Task filenames, dependencies, links, and scenario IDs were renumbered
together; earlier IDs remain available in Git history. The deleted `issues-000` through
`issues-008` IDs remain retired.

The next strictly sequential capability roadmap is specified in
[Redmine 7.0.2 files and issues](redmine-7-0-2-capabilities.md).
Its tasks are listed below. The 7.0.2 deployment target is configured and accepted;
the user waived actual runtime verification on 2026-10-02. Runtime tool behavior
remains unverified.

Synthetic deployment: Redmine `7.0.2-bookworm` is pinned in `deploy/compose.test.yaml`.
Planning baseline: 2026-09-30. Task records below contain the implementation and acceptance
evidence completed since that baseline. Existing runtime configuration already has a
false-default write gate, but the currently deployed catalog remains read-only.

## Current MCP catalog

| Tool | What a client can do today | Status |
|---|---|---|
| `list_projects` | Page through projects visible to the requesting Redmine user. | Implemented; runtime acceptance not established by this plan |
| `list_issues` | Page through issues by project, status, and assignee. | Implemented; extension task below |
| `get_issue` | Read one visible issue with journals and attachment metadata. | Implemented; extension task below |
| `get_current_user` | Identify the caller and read visible project memberships with roles. | Implementation finished; acceptance pending in tool-013 |

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
| 1 | [prep-004-accept-existing-baseline](tasks/prep-004-accept-existing-baseline.md) | Accept the existing reader baseline | prep-002-offline-tests accepted | complete | User accepted the revised offline baseline by directing continuation to prep-005 on 2026-10-02. Live waiver and prior limitations retained; see [dated evidence](prep-004-verification.md). |
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
| 1 | [prep-010-permission-session-contract](tasks/prep-010-permission-session-contract.md) | Resolve permission evidence, resource context, and session integration | Existing prep-003/005/007 implementations; prior acceptance limitations retained | complete | [Dated contract review](prep-010-contract-review.md) resolves all eleven operations, partial evidence, raw discovery handler and SDK session binding. Implement prep-011 next. |
| 2 | [prep-011-multi-user-writer-auth](tasks/prep-011-multi-user-writer-auth.md) | Authenticate personal keys and restrict writes independently of reads | prep-010 session contract; existing prep-007 implementation | blocked | Implementation and Ruff/mypy/diff checks pass. AUTH-001 through AUTH-008 and metadata packaging checks assigned to prep-014; continue prep-012 coding under the full-range assignment. |
| 3 | [prep-012-project-resource-authorization](tasks/prep-012-project-resource-authorization.md) | Check caller capabilities in the actual target context | prep-010 resolved permission matrix; prep-011 implementation | blocked | All eleven service checks, typed evidence and same-key target/role gateway implemented; Ruff/mypy/AST/diff checks pass. PERM-001 through PERM-009 pending in prep-014; continue prep-013 coding. |
| 4 | [prep-013-caller-tool-discovery](tasks/prep-013-caller-tool-discovery.md) | Discover tools relevant to the caller without changing shared registry | prep-010 adapter contract; prep-011/012 implementations | planned | Raw SDK handler, immutable schema cache and authenticated request context resolved by prep-010. Implement after prep-012. |
| 5 | [prep-014-multi-user-writer-acceptance](tasks/prep-014-multi-user-writer-acceptance.md) | Verify caller isolation, permissions, discovery, and resulting write state | prep-011/012/013 implemented; prep-002 baseline; prep-008 fixture guidance; separate testing authorization | planned | Finish predecessor contracts/implementation; fixtures, tests, and live checks are a separate assignment. |

The old prep-009 release acceptance remains scoped to its existing roadmap. prep-014 owns
acceptance of the multi-user change; old waivers and passing checks are not new runtime evidence.

Execution assignment (2026-10-05): the user requested implementation of prep-010 through prep-014,
quality checks and one commit per prep named `feat: prep_0xx <context>`. Coding stages remain
separate from prep-014's explicit verification scope. No production rollout is included.

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
