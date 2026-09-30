# tool-003-get-project: Understand one visible project

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-003-get-project` |
| Capability | Give a client details for a project found by `list_projects`. |
| Type / access / destructive effects | Add tool / read / none |
| Status | blocked; implementation finished, testing pending |
| Last updated | 2026-09-30 |
| Dependencies | [prep-002](prep-002-offline-tests.md) |
| Target | Redmine 6.0.5-bookworm |
| Next action | Add and run PROJECT-001 through PROJECT-004 in a separate testing assignment. |

## 2. Discovery and evidence

`list_projects` is the only project tool. Its model includes ID, identifier, name, description,
status, and parent. The [Redmine Projects API](https://www.redmine.org/projects/redmine/wiki/Rest_Projects)
documents lookup by ID or identifier (reviewed 2026-09-30). Use numeric IDs initially to match current public inputs;
visibility follows the shared Redmine account.

## 3. Requirements

| ID | Client need | Observable behavior |
|---|---|---|
| REQ-001 | Inspect a project selected from a list. | `get_project` returns one visible project's identity, description, parent, status, public flag, and timestamps when provided. |
| REQ-002 | Respect existing access boundaries. | Invalid ID, invisible project, and failed upstream calls have safe results. |

## 4. Public contract and technical specification

Add `get_project(project_id: positive int)` at `GET /api/v1/projects/{project_id}`; explicitly
allowlist operation ID `get_project`. Return `ProjectDetail`, extending current `Project` fields
with nullable `is_public`, `created_on`, and `updated_on` so absent optional Redmine fields do not
invalidate a visible project. Do not request association includes; separate lookup tools own
versions and categories. Map to `GET projects/{project_id}.json`, validate the `project` object,
and return no fabricated defaults for optional metadata. Require bearer auth; preserve existing
403/404/502/504 sanitized errors and adapter MCP envelope. Write semantics: N/A.

## 5. Implementation plan

Extend project model/port/service/gateway/router, wire through existing project container, add
the operation to the explicit MCP allowlist, and update tool reference/changelog. Keep
`list_projects` behavior untouched. Add focused offline and opt-in synthetic checks.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given a visible project ID, when calling REST/MCP, then the typed project detail is returned. | REQ-001 | Pending |
| AC-002 | Given invalid, hidden, or malformed upstream data, when calling, then validation or sanitized errors occur without data leakage. | REQ-002 | Pending |

## 7. Test plan and execution record

PROJECT-001: complete/optional fields and existing list regression. PROJECT-002: invalid ID,
403/404/timeout/malformed data. PROJECT-003: MCP discovery/auth/call. PROJECT-004: opt-in
synthetic visible and hidden projects. Static, offline, and Inspector results are pending.

## 8. Implementation and review record

Implementation finished; testing pending. Added `ProjectDetail`, reader/service/gateway lookup,
validated REST route, explicit MCP registration, tool reference, and changelog. The gateway
requests `projects/{project_id}.json` and validates the `project` root. Existing shared account
visibility and sanitized error mapping apply. No tests, Inspector, startup, or live calls ran.
Target response and permission behavior still need synthetic verification.
Static checks passed: `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
--check .` (71 files), `.venv/Scripts/python.exe -m mypy src` (32 files), `git diff --check`,
and `git diff --cached --check`. Git Bash launch was denied, so existing executables were used.
Diff review found only scoped changes beyond the preserved baseline.

## 9. Completion and handoff

- [ ] AC-001 and AC-002 pass with recorded evidence.
- [x] Documentation and dashboard are synchronized.

Final status: blocked. Next action: add and run PROJECT-001 through PROJECT-004, including
synthetic visibility and Inspector acceptance, in a separate testing assignment.
