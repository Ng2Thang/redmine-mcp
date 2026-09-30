---
name: redmine-analyze-spec
description: Analyze a proposed Redmine MCP tool or tool brief against existing code, client outcomes, permissions, and target-version evidence before task planning. Analysis only.
---

# Analyze an MCP tool proposal

Work in one agent without subagents. Begin with the requested client outcome, an existing task
document, or a concise tool brief. Do not require an endpoint inventory or a standalone REST
specification. If no tool or outcome is identifiable, ask for that missing product
intent. A Redmine REST page is evidence for implementation, not authority to add every endpoint.

Read repository instructions, `docs/plans/index.md` if present,
`docs/workflows/redmine-tools.md`, `docs/templates/redmine-tool-task.md`, current MCP operations,
public tool reference, relevant router/service/port/gateway code, and the Redmine pin in
`deploy/compose.test.yaml`. Use English Markdown and Git Bash commands. Do not change code,
dependencies, tests, policies, or live Redmine state in an analysis-only assignment.

## Procedure

1. State who needs the tool, the question it answers, expected inputs/outputs, read/write
   boundary, and why current tools do not already meet the need. Identify a matching existing
   tool to extend before proposing a new name.
2. Trace existing coverage through the route, service, Protocol, gateway, model, bootstrap,
   and MCP allowlist. Separate static code evidence from runtime verification.
3. Identify the smallest upstream Redmine calls needed for that tool. Verify target-version
   behavior using authoritative Redmine documentation or versioned source. Record URL, date,
   version, permission evidence, and uncertainty; latest docs alone do not prove 6.0.5 support.
4. Record compatibility constraints, missing prerequisites, unsupported behavior, and material
   contract questions. Do not fill gaps with invented permissions, pagination, or write guarantees.
5. For writes, identify separate restricted writer, side effects, timeout uncertainty, and
   disposable synthetic verification needs without performing them.

## Output

Return a concise analysis with: client outcome; existing tool coverage; proposed MCP contract
boundary; implementation evidence; version/permission constraints; unresolved questions; and
the next planning action. Use source links near claims. Do not create task IDs, mark acceptance,
or implement code. Save analysis only when explicitly requested, at a path under `docs/plans/`
that does not overwrite an existing task. Preserve working-tree edits and secrets.

Example: “Analyze a proposed `get_project` MCP tool that lets a client inspect one project
selected from `list_projects`; return coverage and contract questions only.”
