# tool-006-list-issue-priorities: Resolve issue priorities

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-006-list-issue-priorities` |
| Capability | Let clients interpret priority IDs and the default priority. |
| Type / access / destructive effects | Add tool / read / none |
| Status | blocked; implementation finished, testing pending |
| Last updated | 2026-09-30 |
| Dependencies | [prep-002](prep-002-offline-tests.md) |
| Target | Redmine 6.0.5-bookworm |
| Next action | Add and run PRIORITY-001 through PRIORITY-003 in a separate testing assignment. |

## 2. Discovery and evidence

Issues expose priority references, but no priority lookup tool exists. [Redmine Enumerations](https://www.redmine.org/projects/redmine/wiki/Rest_Enumerations)
documents `GET enumerations/issue_priorities.json` with ID, name, and `is_default` (reviewed
2026-09-30).

## 3. Requirements

| ID | Client need | Observable behavior |
|---|---|---|
| REQ-001 | Decode and choose priority IDs. | Return priority ID, name, and default flag. |
| REQ-002 | Use only the intended enumeration. | No time-entry activity or document category data appears in this tool. |

## 4. Public contract and technical specification

Add no-input `list_issue_priorities` at `GET /api/v1/issue-priorities`, explicitly allowlisted
for MCP. Return `list[IssuePriority]` with positive `id`, nonempty `name`, and boolean
`is_default`. Map the `issue_priorities` array from `GET enumerations/issue_priorities.json`.
Empty array is valid; absent/malformed array or item yields sanitized `upstream_response` 502.
Use the shared bearer token and existing upstream 403/404/502/504 mapping. No pagination,
other enumeration exposure, or write behavior.

## 5. Implementation plan

Add typed reference-data layers and bootstrap wiring, register the operation explicitly, update
tool reference/changelog, and add offline and opt-in synthetic checks.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given an upstream priority array, when called, then every ID/name/default flag is returned. | REQ-001 | Pending |
| AC-002 | Given an upstream enumeration response, when called, then only issue priorities are requested and exposed. | REQ-002 | Pending |

## 7. Test plan and execution record

PRIORITY-001: populated/empty/malformed priority arrays. PRIORITY-002: exact upstream path,
auth, errors, MCP discovery/call. PRIORITY-003: opt-in synthetic default priority. Static,
offline, and Inspector checks pending.

## 8. Implementation and review record

Implementation finished; testing pending. Added typed priority model, reference reader/service,
Redmine gateway, authenticated REST route, explicit MCP registration, tool reference, and
changelog. The gateway requests only `enumerations/issue_priorities.json` and maps the
`issue_priorities` root through the shared validation helper. No tests, startup, Inspector, or
live calls ran; target shape and default priority need synthetic confirmation.
Static checks passed: `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
--check .` (77 files), `.venv/Scripts/python.exe -m mypy src` (38 files), and staged/unstaged
`git diff --check`. Git Bash launch was denied, so existing executables were used. Diff review
found only scoped changes beyond the preserved baseline.

## 9. Completion and handoff

- [ ] AC-001 and AC-002 pass with recorded evidence.
- [x] Documentation and dashboard match the implementation.

Final status: blocked. Next action: add and run PRIORITY-001 through PRIORITY-003, including
Inspector and synthetic default comparison, in a separate testing assignment.
