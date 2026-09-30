---
name: redmine-implement-task
description: Implement an explicitly assigned Redmine task document's code and documentation, run Ruff and mypy static checks, and hand off testing. Excludes writing, modifying, or running tests and live tool verification.
---

# Implement a Redmine task without testing

Implement only the assigned task's coding scope. Use one agent without subagents. Paths below
are repository-relative. Planning or reviewing a backlog does not authorize implementation.
Follow active execution-mode restrictions; Plan mode permits planning, not file changes.

## Establish the assignment

Read the assigned `docs/plans/tasks/<task-id>.md`, the matching row in `docs/plans/index.md`, applicable repository instructions,
`docs/workflows/redmine-tools.md`, and `docs/templates/redmine-tool-task.md`. Inspect relevant
source references, current code, dependencies, and existing review findings. If no task was
identified unambiguously, ask which task to implement. If the task file is missing, report that
blocker rather than generating or selecting a backlog automatically.

Record the working-tree baseline and preserve unrelated changes. Check whether the specification
matches current code and public contracts. Resolve discoverable implementation details yourself;
ask only about material unresolved product decisions or work outside the assignment. A review
report is useful input, not a mandatory new approval gate. Do not bypass unresolved review findings
that affect the assigned contract.

Confirm required runtime and policy prerequisites before dependent edits. The owner authorized
future reads, writes, and automated testing, but this skill's assignment excludes testing work.
Do not install test dependencies or implement prerequisite tests to unblock yourself. Implement
independent coding work where possible and record the remaining dependency. Do not automatically
execute unrelated prerequisite tasks. If the assigned task consists entirely of testing work,
explain that it requires a separate testing assignment and stop without pretending it was coded.

## Coding scope

Implement the agreed behavior through the existing router -> service -> port -> gateway flow:

- Add or update models, Protocol interfaces, Redmine gateways, and services as specified.
- Add REST validation, routes, and bootstrap wiring; keep FastAPI and HTTPX out of services.
- Register MCP operations explicitly, preserve stable names, and supply agreed metadata.
- Make necessary runtime configuration and runtime dependency changes within the task scope.
  Use `uv` for dependency changes and include `pyproject.toml` and `uv.lock` together.
- Update public documentation, the changelog when applicable, and the task's implementation record.

Preserve existing contracts except for explicitly specified changes. Use Python 3.13, explicit
types, asynchronous HTTP, and lifespan-managed clients. Do not add database access to MCP, generic
CRUD frameworks, unrelated refactors, or deferred review fixes that do not block this task.

For writes, implement specified authorization and least privilege. Do not replace the shared
reader credential with an administrator key. Handle empty success bodies and uncertain outcomes
as specified; do not invent retries or idempotency. Record contract changes before dependent edits
and resolve material ambiguity rather than silently choosing new public behavior.

## Testing exclusions

Do not create, modify, delete, or execute tests, unit tests, fixtures, snapshots, test harnesses,
coverage configuration, test infrastructure, or test dependencies. Preserve existing test files.
Reading existing tests for contract context is allowed. Do not weaken or delete tests because the
new code may require future test updates; record those updates in the handoff.

Do not run pytest, unittest, test-bearing check scripts, pre-commit hooks, MCP Inspector, startup
smoke checks, live tool calls, or ad hoc scripts that exercise runtime behavior, even with mocks.
Do not seed, reset, restore, or mutate a live Redmine environment. Disposable data creation and
runtime verification belong to the later testing assignment.

Do not use build/package commands as a workaround for this static-check-only scope. If packaging
or dependency changes require a build for eventual acceptance, hand it off explicitly.

The full workflow still requires testing for acceptance. Its test execution instructions are
deferred for this coding-only assignment; never remove the test plan to make the task look complete.

## Static checks

Allowed verification is Ruff lint, Ruff formatting checks, mypy type checks, and final diff
inspection. Use the installed tools from Git Bash. Prefer commands that do not automatically
install development or testing dependencies:

```bash
uv run --frozen --no-sync ruff check .
uv run --frozen --no-sync ruff format --check .
uv run --frozen --no-sync mypy src
git diff --check
```

If `uv` is unavailable, use existing environment executables, such as `.venv/Scripts/ruff.exe`
and `.venv/Scripts/python.exe -m mypy src` on Windows. If required tools are missing, report the
static check as blocked instead of installing testing dependencies or calling the check passed.
Inspect wrapper scripts before using them; execute only commands within this skill's scope.

Formatting may be applied only to files changed for this task. Do not run repository-wide format
fixes, install hooks, disable checks, or introduce suppressions merely to obtain a green result.
Distinguish pre-existing failures from regressions; fix introduced failures and report unrelated
ones without silently expanding scope. Repeat checks only when edits or failures justify it.

## Task record and handoff

Update the task's implementation record with changes, deviations, affected contracts/configuration,
static-check commands and actual results, and final diff findings. Preserve IDs, user decisions,
and valid prior evidence. Do not overwrite an existing completed task's history; record new work
or changed assumptions explicitly.

Keep planned test scenarios and runtime acceptance evidence pending. List the exact later testing
work: scenario/criterion IDs, test additions or updates, required environment, and relevant
startup/Inspector/live-state checks. For writes, include resulting Redmine state verification and
cleanup. Identify builds or additional prerequisite work deferred by this scope.

If all coding work is done, report **implementation finished; testing pending**. In the existing
template, use status `blocked` with testing as the outstanding acceptance prerequisite and an
exact next action. Check only completion items supported by actual evidence; do not mark all
acceptance criteria or the feature complete because static checks pass. If coding itself remains
blocked, describe the unfinished behavior rather than claiming implementation is finished.

The final response states code changes, static-check outcomes, compatibility implications, and
remaining verification. Stop this coding stage without starting tests. An orchestrator with an
explicit broader assignment may begin a separate verification stage afterward; this skill never
writes or runs those tests. Do not publish, commit, deploy, or implement another task implicitly.

Example invocation:

> Use $redmine-implement-task for docs/plans/tasks/tool-003-get-project.md. Implement code and
> relevant documentation, run static checks, and hand off testing without writing or running tests.
