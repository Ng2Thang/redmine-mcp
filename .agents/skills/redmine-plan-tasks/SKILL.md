---
name: redmine-plan-tasks
description: Decompose requested Redmine MCP tool outcomes into task documents with contracts, dependencies, acceptance criteria, and test plans. Planning only.
---

# Plan MCP tool tasks

Use one agent without subagents. Accept a tool brief, existing task, or user request describing
client outcomes. Read `docs/plans/index.md`, `docs/workflows/redmine-tools.md`,
`docs/templates/redmine-tool-task.md`, repository instructions, current code/tool reference, and
the Redmine pin. If analysis is missing or stale, apply `redmine-analyze-spec` first; an analysis
in the conversation is enough. Do not require a standalone endpoint specification or expand
scope from an API reference page. Use English Markdown and Git Bash commands.

## Decomposition

1. Inventory requested client outcomes and the current MCP catalog. Extend an existing tool
   when it already serves an outcome; do not create a tool per endpoint or parameter.
2. Give each public behavior one task owner. Create separate tasks only for real prerequisites,
   permission boundaries, or independently useful tools. Preserve existing task IDs and evidence;
   never reuse retired IDs.
3. For each tool, resolve MCP name, purpose, inputs/defaults/validation, output, auth,
   REST adapter route, upstream mapping, errors, version support, compatibility, and tests.
   Use authoritative Redmine evidence with URL/date/version. Do not invent permissions or
   pagination. If a material contract remains uncertain, mark `blocked` with an exact next action.
4. Order dependencies without cycles. Reuse the offline testing baseline and, for future writes,
   require separate writer access and disposable state verification.
5. Populate all nine template sections. Requirements link to observable acceptance criteria and
   meaningful offline, REST/MCP, and opt-in synthetic scenarios. Sections 8-9 retain pending
   execution evidence and unchecked completion items.

## Deliverables and consistency

For an explicit document-generation request, create or update `docs/plans/index.md` and
`docs/plans/tasks/<task-id>.md`. Conversation-only requests and Plan mode prohibit file writes.
The dashboard contains task links, client outcome, dependencies, status, blocker, and next action;
update it in the same change as task status. Current implemented tools appear as baseline, not
new planning tasks. Future ideas remain visibly unassigned.

Check every selected outcome has one contract owner, every task links back to an outcome or
justified prerequisite, dependency links resolve, IDs are unique, and status matches evidence.
`planned` means decision-complete even if an implementation dependency is pending; `blocked`
means contract evidence or a product decision is missing. Never call a planned task implemented
or accepted. Return generated files, dependency order, blockers, and verification limitations.
Stop at planning; review and coding are separate assignments.

Example: “Use `$redmine-plan-tasks` to plan a `list_project_versions` MCP tool from its client
outcome. Update the dashboard and one task document; do not implement code.”
