# Redmine tool implementation workflow

Use this workflow for one assigned Redmine capability, including extensions to existing tools.
Create or resume `docs/plans/<feature>/<task-id>.md` (for example,
`docs/plans/issues/<task-id>.md`) using the
[task template](../templates/redmine-tool-task.md). Paths written in code spans are relative to
the repository root. Keep completed task documents as implementation and verification records.

## Invocation

Requirement-based implementation assignments to `redmine_feature_agent` automatically run
these stages in order within the same sub-agent:

1. Analysis with `$redmine-analyze-spec`.
2. Task decomposition with `$redmine-plan-tasks`.
3. Task-plan review with `$redmine-review-tasks`.
4. Coding without tests with `$redmine-implement-task`.

For example:

> Spawn a sub-agent of type redmine_feature_agent to implement the requirements in
> docs/rest_api_redmine/issues.md. Wait for completion and report changes and static checks.

This assignment authorizes all four stages within the requested requirement scope. Save
`analysis.md`, `index.md`, individual task documents, and `review.md` under
`docs/plans/<feature>/`, preserving existing IDs, user edits, and execution evidence. If task
documents are missing, analyze and decompose the requirement first. Conversation-only output
requests override file output. In Plan mode, explore and plan in the conversation without
writing artifacts or implementing code.

Review the task plans before coding. Automatically correct actionable planning defects and
review again, with at most two correction/review cycles after the initial review. Record
unresolved findings and material decisions; do not treat blocked or unreviewed tasks as ready.
Review assesses planning readiness, not code correctness or runtime behavior.

After review, explicitly assign the generated or resumed in-scope coding tasks to the coding
skill in dependency order without requiring another routine approval. Honor unresolved review
findings, contract blockers, and runtime/policy prerequisites. Continue independent tasks whose
contracts and prerequisites are resolved. Testing-only tasks and testing prerequisites excluded
by the coding skill remain a separate assignment; do not bypass dependent implementation blockers.
Run Ruff lint, Ruff formatting checks, mypy, and final diff inspection, recording actual results.
Report **implementation finished; testing pending** only when all assigned coding is finished;
otherwise identify unfinished scope and exact next actions. Required acceptance remains blocked
until verification, and static-check success does not establish acceptance.

Explicit single-stage and limited multi-stage requests override the automatic workflow. The
individual skills retain their stage boundaries; the agent orchestrates transitions only for
the stages authorized by the assignment. No further subagents are spawned.

For analysis-only requests, use `$redmine-analyze-spec`. For task-generation requests, use
`$redmine-plan-tasks`; it stops after preparing the backlog and task documents. These skills run
in the same `redmine_feature_agent` without subagents. Use `$redmine-review-tasks` for source-based
self-review of generated tasks. Review-only requests return findings without editing tasks;
explicit generate-and-review workflows may save `review.md`. When revisions are requested, allow
at most two correction/review cycles after the initial review and report unresolved findings.
For coding-only assignments, use `$redmine-implement-task` with a specific task document. It
implements code and relevant documentation and runs static checks; it does not write, modify,
or run tests or perform startup/Inspector/live verification. Missing testing prerequisites remain
handoff work. Report **implementation finished; testing pending**, using status `blocked` for
outstanding acceptance work. Planned tests and eventual completion criteria remain required.

Planning and review requests do not authorize implementation, and a ready plan is not a completed
implementation. These four skills do not include a testing executor; testing is a separate later
assignment. The coding-only scope takes precedence over the full-workflow execution steps below
when that skill is assigned.

> Use $redmine-implement-task for docs/plans/issues/<task-id>.md. Implement code and documentation,
> run static checks, and hand off testing without writing or running tests.

The following invocation is for an explicitly assigned full implementation task:

> Implement `<capability>` using `docs/workflows/redmine-tools.md`. Create or resume its task
> document from `docs/templates/redmine-tool-task.md`. Complete discovery, requirements,
> specification, planning, implementation, and verification in order. Resolve discoverable
> questions independently. Continue without routine approval requests, and report concrete
> evidence or blockers.

One task covers one cohesive capability; it may update an existing tool instead of adding one.
If assigned "all issue tools", first inventory the requested capabilities in the task document.
Record existing coverage, read/write behavior, version support, dependencies, and a task ID for
each capability. Order shared prerequisites before dependent tasks. Do not treat an API reference
page as authorization to implement every related resource or operation.

## Authorized scope and first implementation prerequisite

The owner has explicitly selected these scope changes for future issue-tool implementation:
**read and write tools are permitted, and automated testing is required**. The initial task-pack
delivery adds documentation only; it does not enable writes or install a test framework.

The first future implementation task must establish a shared prerequisite before implementing
dependent tools. Reuse an existing completed prerequisite rather than repeating it:

1. Reconcile the read-only and deferred-testing statements in `AGENTS.md`, `CONTRIBUTING.md`,
   `docs/development.md`, `docs/testing-roadmap.md`, and affected security, architecture, and
   configuration documentation. Describe actual implemented capabilities, not prospective ones.
   This owner-approved scope change does not require another routine approval request.
2. Add `pytest` and `pytest-asyncio` through `uv`; include `pyproject.toml` and `uv.lock` changes
   together. Establish offline test fixtures and a documented test command. Testing CI and
   coverage thresholds are separate decisions, not implied requirements of this workflow.
3. Before implementing writes, specify how runtime write access is configured and authorized,
   how existing reader deployments behave, and the least Redmine permissions each task needs.
   Establish separate synthetic writer credentials and disposable data for verification.
   Never substitute an administrator key for the shared reader key. Keep seed administration
   separate from runtime tools.

If the prerequisite is absent, include it in the assigned task's dependency plan and complete
the necessary shared work first. Ask only if a material product or access-policy decision remains
unresolved after inspection. Record that decision before exposing a write tool.

## Repository constraints

- Read applicable `AGENTS.md` instructions, contributor guidance, architecture, tool reference,
  configuration, and manual verification documentation before editing.
- Preserve router -> service -> port -> gateway dependencies. Services import neither FastAPI
  nor HTTPX. MCP reuses REST routes and never accesses PostgreSQL directly.
- Keep feature behavior under `src/redmine_mcp/features/`; Redmine adapters belong under
  `src/redmine_mcp/integrations/redmine/`. Use bootstrap for concrete dependency wiring.
- Preserve public tool names and explicitly allowlist operations. Register REST routes before
  MCP creation. Do not introduce a generic CRUD framework or expose all routes automatically.
- Use Python 3.13, explicit types, asynchronous HTTP, lifespan-managed clients, Ruff, and strict
  mypy. Preserve unrelated changes. Include dependency metadata and its lockfile together.
- All Markdown is English. Shell commands are Git Bash commands; do not supply PowerShell.
- Never record credentials, tokens, real issue contents, or full upstream response bodies in
  task documents or logs. Use synthetic examples and redacted evidence.
- Do not install hooks, publish changes, commit changes, or operate on production data implicitly.
  Do not seed, reset, or restore an environment merely to validate a tool.
- Avoid unrelated refactoring and deferred review findings unless they block this capability.

## Execution sequence

Phase checks are internal completeness checks, not repeated user-approval requests. Follow the
active execution mode: an instruction to plan only does not authorize coding. Otherwise, once
a capability is assigned, continue through all phases within its authorized scope.

| Phase | Agent action | Exit condition |
|---|---|---|
| Discovery | Inspect code, policies, current contracts, and version-specific upstream evidence. | Existing behavior, prerequisites, and unknowns are recorded. |
| Requirements | Define observable outcomes, scope, examples, and numbered requirements. | Every requirement has an intended acceptance scenario. |
| Specification | Decide inputs, outputs, mappings, errors, compatibility, and write semantics. | No unresolved public-contract decision remains. Mark status `specified`. |
| Planning | Order concrete edits, dependencies, tests, documentation, and live checks. | Steps are actionable and prerequisites resolved or scheduled first. Mark `planned`. |
| Implementation | Implement the agreed contract through the existing layers. Update the record. | Required behavior, tests, registration, and documentation are present. |
| Verification | Run relevant checks, inspect the diff, and gather acceptance evidence. | Every required criterion passes, or a precise blocker is recorded. |
| Handoff | Summarize results and remaining work with an exact next action. | Mark `complete` only if the completion rules below hold. |

Check progress against requirements throughout implementation. If evidence changes a contract,
update the specification, acceptance criteria, and plan before dependent edits. Ask about material
ambiguity or actions outside scope; resolve repository facts independently. Continue independent
work while awaiting a necessary answer. Never infer approval from elapsed time.

On resume, inspect the working tree, read the task's last evidence and next action, and confirm
whether recorded assumptions still hold. Preserve completed work; do not restart discovery or
rerun unrelated checks without a reason.

## Redmine evidence and write behavior

The default verification target is the synthetic version pinned in `deploy/compose.test.yaml`,
currently Redmine `6.0.5`. Confirm the pin during discovery. Treat
`docs/rest_api_redmine/issues.md` as a starting reference, not proof that every documented feature
exists in the target version. Consult authoritative Redmine documentation or versioned source;
record source URLs, date checked, supported version, and any uncertainty.

Specify exact query/body mappings and distinguish omitted values, explicit nulls, empty strings,
and empty arrays where relevant. Preserve existing defaults unless an intentional change is
recorded. Do not invent upstream idempotency, rollback, pagination, or concurrency guarantees.

For each write, define permissions, side effects, upstream success status/body, caller-visible
result, and verification of resulting Redmine state. Specify duplicate invocation and retry
behavior, partial success, and concurrent edits where relevant. A timeout may leave the result
unknown: do not report definite failure or retry automatically without an established guarantee.
Record how the caller can reconcile an uncertain outcome. A write followed by a failed read-back
must not be represented as proof that the write failed.

Live write verification uses explicitly identified disposable synthetic resources and a cleanup
procedure scoped to those resources. Do not delete pre-existing seed fixtures or reuse production
IDs. Record safe resource references and outcomes without copying issue bodies or credentials.

## Verification baseline

Use focused tests that establish behavior rather than mirror forwarding implementations:

- `pytest` and `pytest-asyncio` for automated execution.
- HTTPX `MockTransport` for upstream response mapping, payloads, and failure scenarios.
- HTTPX ASGI transport with explicit application lifespan management for REST integration.
- MCP SDK client checks for tool discovery, authentication, invocation, and error envelopes.
  Use in-process transport or an injected ASGI HTTP client so normal tests need no network.
- Explicitly opt-in live checks against the synthetic environment, separate from the default
  offline suite. Missing live prerequisites are reported as blocked, not silently passed.

Normal automated tests require no Docker, real credentials, external service, or network access.
Configure fake settings explicitly and prevent implicit loading of local `.env` secrets. Replace
the upstream HTTP boundary in fixtures. Close clients and MCP sessions through their lifecycles.

For each task, select scenarios for defaults, filters, encoding, pagination, optional fields,
rejected input before upstream access, correct payloads, empty/malformed/upstream error responses,
authentication, permissions, and compatibility. Add write-specific scenarios where applicable.
Record justified `N/A` decisions rather than inventing irrelevant tests.

After the prerequisite establishes the suite, the standard commands are:

```bash
bash scripts/check.sh
uv run --frozen pytest
```

Run focused tests during implementation, then the full offline suite and repository checks before
completion. Build when packaging or dependencies change. Follow
[manual verification](../manual-verification.md) for startup and Inspector checks, extending the
documented expected tool catalog and scenarios when adding tools. Record commands and results;
do not print secret-bearing environment or Compose configuration.

Use [the testing roadmap](../testing-roadmap.md) to guide the prerequisite and relevant coverage.
Its deferred status describes the old baseline until that prerequisite updates it.

## Completion and reporting

A task is complete only when required behavior is implemented, acceptance criteria have passing
evidence, relevant automated tests and repository checks pass, required live verification is
completed, documentation is current, and no unresolved decision changes specified behavior.

Each requirement must link to an acceptance criterion and concrete verification evidence. For
writes, evidence must establish both the response and resulting upstream state. Mocked evidence
does not establish real Redmine permission or workflow behavior.

If code is implemented but required verification cannot run, set status `blocked` and report
**implemented, verification blocked**, with the missing prerequisite and exact next action.
Record pre-existing check failures separately from introduced failures; neither may be called a
pass. Do not broaden the task silently to fix unrelated failures.

The final handoff states what changed, which checks ran and their results, contract/configuration
implications, and remaining blockers. Keep the task document synchronized with that report.
