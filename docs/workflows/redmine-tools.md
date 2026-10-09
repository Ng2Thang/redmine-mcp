# MCP tool implementation workflow

Use this workflow for one user-facing MCP capability or a shared prerequisite. Start with the
client outcome and existing tool catalog, not an inventory of Redmine REST endpoints. Redmine
documentation and versioned source establish implementation facts; they do not expand the tool
scope. The common dashboard is [docs/plans/index.md](../plans/index.md). Each assigned task lives
at `docs/plans/tasks/<task-id>.md` and follows the [task template](../templates/redmine-tool-task.md).
Keep all Markdown in English and all suggested commands in Git Bash.

## Inputs and ownership

An assignment can provide a tool brief, an existing task document, or both. A tool brief states
who calls the tool, the outcome, intended inputs/outputs, and read/write boundary. If no task
exists, inspect current MCP operations, code, and relevant user requirements before proposing
one. Reuse or extend an existing tool when it already serves the outcome. One task owns one
public tool behavior; shared prerequisites get separate tasks. Do not turn every Redmine
endpoint or parameter into a tool.

Read repository instructions, contributor guidance, architecture, tool reference, configuration,
the task template, current code, the target pin in `deploy/compose.test.yaml`, and task
dependencies. Preserve unrelated working-tree changes and retired task IDs unless the user
explicitly requests renumbering. For renumbering, update filenames, task IDs, dependencies,
links, and scenario IDs together and record the revision in the dashboard. Record authoritative
Redmine URLs, date checked, target-version evidence, and unresolved claims inside the task.
Confirm behavior against the pinned 7.0.2 source and runtime evidence.

Update the task's status, blocker, and next action together with the dashboard. `planned` means
the public contract is decision-complete, even when implementation dependencies remain.
`blocked` means an unresolved decision or missing evidence prevents a reliable contract or
acceptance. A ready plan is not implemented behavior.

## Assignment stages

| Stage | Output | Exit condition |
|---|---|---|
| Discovery | Current catalog, code, permissions, versioned Redmine evidence | Existing coverage and uncertainty identified |
| Requirements | User outcome, scope, numbered requirements | Each requirement has observable acceptance |
| Specification | MCP/REST contract, upstream mapping, errors, compatibility | No material public-contract decision unresolved |
| Planning | Ordered edits, dependencies, tests, live checks | Another agent can implement without choosing behavior |
| Implementation | Code, registration, documentation, execution record | Assigned behavior is present |
| Verification | Static, automated, and required synthetic evidence | Acceptance passes or an exact blocker is recorded |
| Handoff | Task and dashboard status, next action | `complete` only with all required evidence |

Plan-only and review-only assignments stop at their stated stage. A coding-only assignment using
`$redmine-implement-task` implements code/docs and runs Ruff and mypy, but does not write or run
tests or perform startup/Inspector/live checks; hand those off explicitly. A testing-only task
is a separate assignment or a distinct stage in an explicitly authorized full-roadmap run.
Do not bypass dependent prerequisites or mark acceptance passed from static checks.

## Sequential roadmap agent

The project-scoped `redmine_feature_agent` in `.codex/agents/` can execute an explicitly assigned
task range in dashboard order, one task at a time and without spawning more agents. It reads the
analysis, planning, review, and coding skills only when their stages apply. Coding ends before
the separate verification stage begins. The agent records evidence and synchronizes task and
dashboard status after each stage. It may continue past a blocked task only to an independent
selected task with completed dependencies; it does not treat a blocked prerequisite as complete.

Example Codex request: “Spawn one `redmine_feature_agent` to implement the reader roadmap in
`docs/plans/index.md` from `prep-001-ruff-checks` through `tool-008-list-project-issue-categories`.
Run each task's planned verification in a separate stage, update evidence and dashboard status,
and report any remaining blockers. Do not implement write tools.” A narrower task ID or stage
limits the assignment accordingly.

## Runtime architecture and access

Keep router → service → Protocol port → Redmine gateway. Services do not import FastAPI APIs or
HTTPX; the narrow exception is `from fastapi import status as http_status` for HTTP status
constants. Register REST routes before MCP creation and add each stable `operation_id` explicitly to
the MCP allowlist. MCP reuses REST routes; it never queries PostgreSQL. Use typed models,
validated inputs, async HTTP, lifespan-managed clients, sanitized errors, and per-user Redmine
key authentication. Keep existing names/defaults compatible unless a task explicitly changes them.
Avoid a generic CRUD proxy and never log API keys, tokens, or complete issue bodies.

The default reader remains read-only; implemented writes use a separate opt-in writer with
configured operation gates and native permissions. New writes require a task defining exact
side effects, least Redmine permissions, application permission rules and disposable synthetic
verification. Current functional evidence and remaining variants are recorded in the
[acceptance ledger](../testing/evidence/current-catalog-acceptance.md). Administrative seeding stays
separate. For each write, define success status/body, duplicates, retries, timeout uncertainty,
partial success, concurrency, state reconciliation, and cleanup; do not invent upstream
idempotency or rollback. A failed read-back cannot prove a preceding write failed.

## Verification

The offline test baseline is [prep-002](../plans/tasks/prep-002-offline-tests.md). Once complete,
use pytest/pytest-asyncio, HTTPX MockTransport, ASGI transport with explicit lifespan, fake
settings that do not load `.env`, and MCP SDK client checks. Default tests need no Docker,
network, or real credentials. Select meaningful success, validation, pagination, empty/malformed
response, auth, permission, timeout, MCP discovery/invocation/error, and compatibility scenarios.
Opt-in live verification uses the marked synthetic Redmine environment; never seed, reset, or
restore merely to validate a reader tool.

Run from Git Bash when the task's execution scope permits:

```bash
bash scripts/check.sh
uv run --frozen pytest
```

Update Inspector scenarios and the documented tool catalog when adding operations. Record actual
commands/results and distinguish mocks from live evidence. Build when packaging or dependencies
change. A task is `complete` only when required behavior, documentation, repository checks,
automated tests, and required synthetic verification have passing evidence. If code is finished
but verification cannot run, use `blocked`, explain the missing evidence, and give the exact next
action. Keep the dashboard synchronized with the task.

## Example handoffs

Planning: “Plan a tool that lets clients find versions available for a visible project. Use
`docs/plans/index.md` and the tool task template; stop after planning.”

Coding: “Use `$redmine-implement-task` for
`docs/plans/tasks/tool-003-get-project.md`. Implement its code and documentation, run static
checks, and hand off tests.”
