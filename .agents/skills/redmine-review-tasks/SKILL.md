---
name: redmine-review-tasks
description: Review MCP tool task documents against client outcomes, current code, workflow, template, and target Redmine evidence without implementing tools.
---

# Review MCP tool plans

Use one agent without subagents. Read the requested tool brief or task, `docs/plans/index.md`,
`docs/workflows/redmine-tools.md`, `docs/templates/redmine-tool-task.md`, repository instructions,
current code/tool reference, and the Redmine pin. Do not require a deleted endpoint specification
or treat Redmine's full REST catalog as the scope. Review planning artifacts, not runtime
correctness. Use English Markdown and Git Bash commands; do not run live calls or edit code/tests.

## Checks

1. Trace every selected client outcome to exactly one tool/task contract or a justified deferral.
   Check whether an existing operation should be extended instead of creating a duplicate.
2. Compare each task's inputs, defaults, outputs, validation, auth, errors, MCP exposure, and
   compatibility with current code. Check all nine template sections and meaningful acceptance
   scenarios. Task requirements must map to criteria and planned verification.
3. Verify Redmine claims against cited authoritative documentation or versioned source and the
   target pin. Flag unverified permissions, pagination, availability, or write semantics.
4. Check unique IDs, dependency targets, ordering, cycles, shared-model ownership, links, and
   dashboard/task status synchronization. Planned work must not be labeled implemented or passed.
5. For writes, check separate restricted access, side effects, empty success, duplicate/retry and
   timeout uncertainty, state reconciliation, disposable data, and cleanup.

## Findings and boundaries

Return findings with stable IDs, severity (`blocking`, `major`, `minor`), task/evidence,
impact, required correction, and current resolution. Give an overall `ready`,
`changes required`, or `blocked` verdict for the reviewed scope. A ready plan is not completed
implementation. Name unresolved evidence and exact next action; do not invent passing results.

For review-only requests, report in the conversation. Save `docs/plans/review.md` only when
explicitly requested or as part of an assigned generate-and-review workflow. When asked to
revise, use the planning skill to correct affected docs, then re-review; permit at most two
correction/review cycles after the initial review. Preserve existing findings and valid evidence.
Do not implement tasks from a review assignment.

Example: “Use `$redmine-review-tasks` to review the `get_project` task and dashboard against
the current MCP catalog and Redmine 6.0.5 evidence; return planning findings only.”
