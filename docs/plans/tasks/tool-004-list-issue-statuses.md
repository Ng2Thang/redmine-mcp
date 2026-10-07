# tool-004-list-issue-statuses: Resolve status IDs

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-004-list-issue-statuses` |
| Capability | Let clients interpret status IDs and open/closed meaning. |
| Type / access / destructive effects | Add tool / read / none |
| Status | blocked; implementation finished, testing pending |
| Last updated | 2026-10-02, Codex |
| Dependencies | [prep-002](prep-002-offline-tests.md) |
| Target | Redmine 7.0.2; runtime acceptance pending |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

No status lookup tool exists. [Redmine Issue Statuses](https://www.redmine.org/projects/redmine/wiki/Rest_IssueStatuses)
documents `GET issue_statuses.json` with status ID, name, and `is_closed` (reviewed 2026-09-30). This is a global list,
not the allowed transitions for a specific issue; `get_issue` owns `allowed_statuses`.

## 3. Requirements

| ID | Client need | Observable behavior |
|---|---|---|
| REQ-001 | Decode statuses returned by issue tools. | Return status ID, name, and closed flag. |
| REQ-002 | Avoid confusing catalog and workflow. | Tool description states that global statuses are not issue-specific allowed transitions. |

## 4. Public contract and technical specification

Add no-input `list_issue_statuses` at `GET /api/v1/issue-statuses` and explicitly allowlist that
operation. Return `list[IssueStatus]` with required positive `id`, nonempty `name`, and boolean
`is_closed`. Map `issue_statuses` from `GET issue_statuses.json`; an absent/non-array root or
invalid item is sanitized `upstream_response` 502. Empty array is valid. Use personal `X-Redmine-API-Key` authentication
and existing 403/404/502/504 mapping; no pagination is promised for this global endpoint.
No local transition logic or mutation. MCP error shape belongs to the adapter.

## 5. Implementation plan

Add a small reference-data model/port/service/gateway/router, wire in bootstrap, register the
operation explicitly, and update tool reference/changelog. Reuse shared HTTPX client and error
mapping; keep services free of HTTPX/FastAPI.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given a valid Redmine status array, when called, then all IDs, names, and closed flags are returned unchanged. | REQ-001 | Pending |
| AC-002 | Given the tool description and one issue's allowed statuses, when inspected, then clients can distinguish the global catalog from workflow-specific choices. | REQ-002 | Pending |

## 7. Test plan and execution record

STATUS-001: populated/empty/malformed arrays. STATUS-002: auth, upstream failures, MCP catalog
and call. STATUS-003: opt-in synthetic comparison with a visible issue's allowed statuses.
Run static, offline, and Inspector checks. All results pending.

## 8. Implementation and review record

Implementation finished; testing pending. Added typed global status model, reader/service,
Redmine gateway, authenticated REST route, bootstrap wiring, explicit MCP registration, tool
reference, and changelog. The shared collection mapper rejects missing, non-array, or invalid
items as sanitized upstream response errors. No tests, startup, Inspector, or live calls ran;
target shape and permission behavior need synthetic confirmation.
Static checks passed: `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
--check .` (77 files), `.venv/Scripts/python.exe -m mypy src` (38 files), and staged/unstaged
`git diff --check`. Git Bash launch was denied, so existing executables were used. Diff review
found only scoped changes beyond the preserved baseline.

## 9. Completion and handoff

- [ ] AC-001 and AC-002 have passing evidence.
- [x] Tool reference and dashboard are updated.

Final status: blocked. Next action: add and run STATUS-001 through STATUS-003, including
Inspector and synthetic catalog comparison, in a separate testing assignment.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

STATUS-001/002 pass offline. Six live statuses and closed flags match Redmine; the sampled issue has an empty allowed-status set, so the nonempty workflow comparison remains pending.

See [the dated verification ledger](../prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_issue_statuses` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H1 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
