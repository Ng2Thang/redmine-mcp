# MCP tool roadmap

This dashboard tracks user-facing MCP capabilities. A Redmine REST endpoint is implementation
evidence inside a task, not the unit of planning. The task document owns its detailed status;
update this table in the same change when that status, blocker, or next action changes. All IDs
below are new. The deleted `issues-000` through `issues-008` IDs remain retired.

The next strictly sequential capability roadmap is specified in
[Redmine 7.1 documents, files, and issues](redmine-7-1-capabilities.md).
Its documentation tasks are listed below; none has implementation or test acceptance.

Target for synthetic verification: Redmine `6.0.5-bookworm` in `deploy/compose.test.yaml`.
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
| 4 | [tool-002-get-issue-context](tasks/tool-002-get-issue-context.md) | Request the related context needed for one issue. | prep-002 | blocked | Implementation finished; run DETAIL-001 through DETAIL-005 and synthetic acceptance separately. |
| 5 | [tool-003-get-project](tasks/tool-003-get-project.md) | Read one visible project's details. | prep-002 | blocked | Implementation finished; run PROJECT-001 through PROJECT-004 and synthetic acceptance separately. |
| 6 | [tool-004-list-issue-statuses](tasks/tool-004-list-issue-statuses.md) | Resolve status IDs and closed flags. | prep-002 | blocked | Implementation finished; run STATUS-001 through STATUS-003 and synthetic acceptance separately. |
| 7 | [tool-005-list-trackers](tasks/tool-005-list-trackers.md) | Resolve tracker IDs and supported fields. | prep-002 | blocked | Implementation finished; run TRACKER-001 through TRACKER-003 and synthetic acceptance separately. |
| 8 | [tool-006-list-issue-priorities](tasks/tool-006-list-issue-priorities.md) | Resolve priority IDs and the default. | prep-002 | blocked | Implementation finished; run PRIORITY-001 through PRIORITY-003 and synthetic acceptance separately. |
| 9 | [tool-007-list-project-versions](tasks/tool-007-list-project-versions.md) | Discover versions available to a project. | prep-002 | blocked | Implementation finished; run VERSION-001 through VERSION-004 and synthetic sharing acceptance separately. |
| 10 | [tool-008-list-project-issue-categories](tasks/tool-008-list-project-issue-categories.md) | Discover categories available to a project. | prep-002 | blocked | Implementation finished; run CATEGORY-001 through CATEGORY-004 and synthetic visibility acceptance separately. |
| 11 | [tool-009-list-issues-by-category](tasks/tool-009-list-issues-by-category.md) | Find all visible issues in a selected project category. | prep-002; tool-008 for category ID discovery | blocked | Implementation finished; run CATISSUE-001 through CATISSUE-005 and marked synthetic Inspector acceptance separately. |
| 12 | [tool-010-list-issues-by-target-version](tasks/tool-010-list-issues-by-target-version.md) | Find visible issues in a Target version and optionally exclude subprojects. | prep-002; tool-007 for Target version ID discovery | blocked | Implementation finished; run TARGETISSUE-001 through TARGETISSUE-005 and marked synthetic Inspector acceptance separately. |
| 13 | [tool-011-expose-issue-schedule-and-spent-hours](tasks/tool-011-expose-issue-schedule-and-spent-hours.md) | Read issue start/due dates and visible direct spent hours so clients can identify dated Bugs and sum their hours. | prep-002; tool-001 issue search; tool-010 exact-project scoping | blocked | Implementation finished; static checks pass. Run DATE/HOURS/AGG/COMPAT/MCP scenarios and marked synthetic Inspector acceptance in a separate authorized testing stage. |
| 14 | [tool-012-list-issue-time-entries](tasks/tool-012-list-issue-time-entries.md) | Identify the users credited with visible spent hours on selected issues. | prep-002; tool-011 issue selection and direct-hours context | blocked | Implementation finished; run planned offline scenarios and marked synthetic Inspector acceptance in a separate authorized testing stage. |
| 15 | [tool-013-get-current-user](tasks/tool-013-get-current-user.md) | Identify the caller and their visible project memberships and roles. | prep-002; prep-003 identity foundation (runtime acceptance pending) | blocked | Implementation finished; static checks pass. Run USER-001 through USER-010 and foundation acceptance in a separately authorized testing stage. |

Tasks 3, 4, 11, 12, and 13 extend existing tools. Tasks 5 through 10, 14, and 15 add eight operations. Each task has one
contract owner; supporting model, service, gateway, route, and registration edits belong to that
owner. The issue extensions and lookup tasks may be implemented in any order after prep-002;
the table gives the preferred release order, not a code dependency.

## Runtime infrastructure work

| Task | Outcome | Status | Blocker / next action |
|---|---|---|---|
| [prep-003-runtime-foundation](tasks/prep-003-runtime-foundation.md) | Bound auth identity, strict service queries, bounded HTTP reads, exception/logging boundaries, lifecycle ownership, validated MCP exposure, and static architecture gate | blocked | Implementation/static checks finished; startup/shutdown and missing-key smoke pass. Run FOUNDATION-001 through FOUNDATION-012 and synthetic Inspector acceptance in a separate authorized testing stage. |

## Redmine 7.1 sequential capability roadmap

This roadmap adds twenty operations and extends `list_issues` and `get_issue`.
The target build is not yet pinned: `deploy/compose.test.yaml` remains at 6.0.5.
Every row depends on accepted evidence and explicit user acceptance of the
previous row. A blocked row stops the chain. Testing requires separate user
authorization for each task; planned checks are not passing evidence.

| Order | Task | Client outcome | Depends on | Status | Blocker / next action |
|---|---|---|---|---|---|
+| 1 | [prep-004-accept-existing-baseline](tasks/prep-004-accept-existing-baseline.md) | Accept the existing reader baseline | prep-002-offline-tests accepted | planned | Review existing pending acceptance and seek separate testing authorization. |
| 2 | [prep-005-upgrade-redmine-7-1](tasks/prep-005-upgrade-redmine-7-1.md) | Pin and rehearse Redmine 7.1 | prep-004-accept-existing-baseline accepted | blocked | Pin exact released 7.1 artifact and rehearse isolated upgrade after prep-004 acceptance. |
| 3 | [tool-014-list-issues-associations](tasks/tool-014-list-issues-associations.md) | Extend issue lists with associations | prep-005-upgrade-redmine-7-1 accepted | blocked | Await prep-005-upgrade-redmine-7-1 acceptance and exact 7.1 evidence. |
| 4 | [tool-015-get-issue-write-context](tasks/tool-015-get-issue-write-context.md) | Expose issue write and file context | tool-014-list-issues-associations accepted | blocked | Await tool-014-list-issues-associations acceptance and exact 7.1 evidence. |
| 5 | [tool-016-list-document-categories](tasks/tool-016-list-document-categories.md) | List document categories | tool-015-get-issue-write-context accepted | blocked | Await tool-015-get-issue-write-context acceptance and exact 7.1 evidence. |
| 6 | [tool-017-list-project-documents](tasks/tool-017-list-project-documents.md) | List project documents | tool-016-list-document-categories accepted | blocked | Await tool-016-list-document-categories acceptance and exact 7.1 evidence. |
| 7 | [tool-018-get-document](tasks/tool-018-get-document.md) | Read one document | tool-017-list-project-documents accepted | blocked | Await tool-017-list-project-documents acceptance and exact 7.1 evidence. |
| 8 | [tool-019-list-project-files](tasks/tool-019-list-project-files.md) | List project files | tool-018-get-document accepted | blocked | Await tool-018-get-document acceptance and exact 7.1 evidence. |
| 9 | [tool-020-get-attachment](tasks/tool-020-get-attachment.md) | Read attachment metadata | tool-019-list-project-files accepted | blocked | Await tool-019-list-project-files acceptance and exact 7.1 evidence. |
| 10 | [prep-006-bounded-binary-downloads](tasks/prep-006-bounded-binary-downloads.md) | Bound binary download transport | tool-020-get-attachment accepted | blocked | Await tool-020-get-attachment acceptance and exact 7.1 evidence. |
| 11 | [tool-021-download-attachment](tasks/tool-021-download-attachment.md) | Download bounded attachment content | prep-006-bounded-binary-downloads accepted | blocked | Await prep-006-bounded-binary-downloads acceptance and exact 7.1 evidence. |
| 12 | [prep-007-restricted-writer-foundation](tasks/prep-007-restricted-writer-foundation.md) | Establish restricted writer runtime | tool-021-download-attachment accepted | blocked | Await tool-021-download-attachment acceptance and exact 7.1 evidence. |
| 13 | [prep-008-synthetic-writer-verification](tasks/prep-008-synthetic-writer-verification.md) | Prepare disposable writer verification | prep-007-restricted-writer-foundation accepted | blocked | Await prep-007-restricted-writer-foundation acceptance and exact 7.1 evidence. |
| 14 | [tool-022-upload-attachment](tasks/tool-022-upload-attachment.md) | Upload bounded attachment bytes | prep-008-synthetic-writer-verification accepted | blocked | Await prep-008-synthetic-writer-verification acceptance and exact 7.1 evidence. |
| 15 | [tool-023-add-project-file](tasks/tool-023-add-project-file.md) | Attach upload as project file | tool-022-upload-attachment accepted | blocked | Await tool-022-upload-attachment acceptance and exact 7.1 evidence. |
| 16 | [tool-024-update-attachment](tasks/tool-024-update-attachment.md) | Edit attachment metadata | tool-023-add-project-file accepted | blocked | Await tool-023-add-project-file acceptance and exact 7.1 evidence. |
| 17 | [tool-025-delete-attachment](tasks/tool-025-delete-attachment.md) | Delete one attachment | tool-024-update-attachment accepted | blocked | Await tool-024-update-attachment acceptance and exact 7.1 evidence. |
| 18 | [tool-026-create-document](tasks/tool-026-create-document.md) | Create a project document | tool-025-delete-attachment accepted | blocked | Await tool-025-delete-attachment acceptance and exact 7.1 evidence. |
| 19 | [tool-027-update-document](tasks/tool-027-update-document.md) | Update document fields or attachments | tool-026-create-document accepted | blocked | Await tool-026-create-document acceptance and exact 7.1 evidence. |
| 20 | [tool-028-delete-document](tasks/tool-028-delete-document.md) | Delete a document | tool-027-update-document accepted | blocked | Await tool-027-update-document acceptance and exact 7.1 evidence. |
| 21 | [tool-029-create-issue](tasks/tool-029-create-issue.md) | Create or natively copy an issue | tool-028-delete-document accepted | blocked | Await tool-028-delete-document acceptance and exact 7.1 evidence. |
| 22 | [tool-030-update-issue](tasks/tool-030-update-issue.md) | Update issue fields or add a note | tool-029-create-issue accepted | blocked | Await tool-029-create-issue acceptance and exact 7.1 evidence. |
| 23 | [tool-031-update-issue-note](tasks/tool-031-update-issue-note.md) | Edit a journal note | tool-030-update-issue accepted | blocked | Await tool-030-update-issue acceptance and exact 7.1 evidence. |
| 24 | [tool-032-create-issue-relation](tasks/tool-032-create-issue-relation.md) | Create one issue relation | tool-031-update-issue-note accepted | blocked | Await tool-031-update-issue-note acceptance and exact 7.1 evidence. |
| 25 | [tool-033-delete-issue-relation](tasks/tool-033-delete-issue-relation.md) | Delete one issue relation | tool-032-create-issue-relation accepted | blocked | Await tool-032-create-issue-relation acceptance and exact 7.1 evidence. |
| 26 | [tool-034-add-issue-watcher](tasks/tool-034-add-issue-watcher.md) | Add one watcher | tool-033-delete-issue-relation accepted | blocked | Await tool-033-delete-issue-relation acceptance and exact 7.1 evidence. |
| 27 | [tool-035-remove-issue-watcher](tasks/tool-035-remove-issue-watcher.md) | Remove one watcher | tool-034-add-issue-watcher accepted | blocked | Await tool-034-add-issue-watcher acceptance and exact 7.1 evidence. |
| 28 | [prep-009-release-acceptance](tasks/prep-009-release-acceptance.md) | Review complete Redmine 7.1 release | tool-035-remove-issue-watcher accepted | blocked | Await tool-035-remove-issue-watcher acceptance and exact 7.1 evidence. |

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
