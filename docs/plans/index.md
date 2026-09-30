# MCP tool roadmap

This dashboard tracks user-facing MCP capabilities. A Redmine REST endpoint is implementation
evidence inside a task, not the unit of planning. The task document owns its detailed status;
update this table in the same change when that status, blocker, or next action changes. All IDs
below are new. The deleted `issues-000` through `issues-008` IDs remain retired.

Target for synthetic verification: Redmine `6.0.5-bookworm` in `deploy/compose.test.yaml`.
Planning baseline: 2026-09-30. Task records below contain the implementation and acceptance
evidence completed since that baseline. Existing runtime configuration already has a
false-default write gate, but this release adds no write operation.

## Current MCP catalog

| Tool | What a client can do today | Status |
|---|---|---|
| `list_projects` | Page through projects visible to the shared Redmine account. | Implemented; runtime acceptance not established by this plan |
| `list_issues` | Page through issues by project, status, and assignee. | Implemented; extension task below |
| `get_issue` | Read one visible issue with journals and attachment metadata. | Implemented; extension task below |

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

Tasks 3, 4, and 11 extend existing tools. Tasks 5 through 10 add six operations. Each task has one
contract owner; supporting model, service, gateway, route, and registration edits belong to that
owner. The issue extensions and lookup tasks may be implemented in any order after prep-002;
the table gives the preferred release order, not a code dependency.

## Future ideas, not assigned tasks

Issue creation, updates, deletion, and watcher changes may be planned later from client workflows.
They require a separate restricted writer deployment, verified permissions, synthetic disposable
data, and write-specific acceptance evidence. Do not restore the deleted endpoint backlog or add
write operations merely because Redmine exposes them. Other reader ideas, such as time entries,
wiki content, and search, need a new client outcome and task before implementation.

## Status and handoff rules

Use `discovery`, `specified`, `planned`, `implementing`, `verifying`, `complete`, or `blocked` as
defined in the task template. `planned` means the public contract is decision-complete, even if a
dependency is pending. `blocked` names missing evidence or an unresolved decision. `complete`
requires implemented behavior and passing acceptance evidence, not a finished document or static
checks alone. Before handing a task to an implementation agent, read its dependencies, exact next
action, and latest evidence; update both the task and this dashboard after the handoff.
