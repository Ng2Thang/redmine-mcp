# tool-007-list-project-versions: Find project release targets

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-007-list-project-versions` |
| Capability | Let clients discover versions available for a project. |
| Type / access / destructive effects | Add tool / read / none |
| Status | blocked; implementation finished, testing pending |
| Last updated | 2026-10-02, Codex |
| Dependencies | [prep-002](prep-002-offline-tests.md) |
| Target | Redmine 7.0.2; runtime acceptance pending |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

No version lookup tool exists. [Redmine Versions](https://www.redmine.org/projects/redmine/wiki/Rest_Versions)
documents a project version list and says it may include versions shared from other projects
(reviewed 2026-09-30).
Its example carries `total_count` but does not establish whether this endpoint accepts
`limit`/`offset` or returns every version in one call. The [general REST pagination guide](https://www.redmine.org/projects/redmine/wiki/Rest_api#Collection-resources-and-pagination)
says collections generally paginate, without making an endpoint-specific guarantee. Per the
owner's 2026-09-30 decision, these official docs are the final specification reference; no
versioned source inspection is required.

## 3. Requirements

| ID | Client need | Observable behavior |
|---|---|---|
| REQ-001 | Choose an available release target for a project. | Return visible version IDs, names, status, owning project, and optional due date. |
| REQ-002 | Avoid silently losing versions. | Result contract represents the full set or explicitly exposes upstream pagination. |
| REQ-003 | Respect visibility. | Hidden projects/versions are not surfaced through another account. |

## 4. Public contract and technical specification

Proposed operation `list_project_versions`, route `GET /api/v1/projects/{project_id}/versions`,
positive integer project ID, and upstream `GET projects/{project_id}/versions.json`. Proposed
`Version` item: positive ID, name, `project` reference, status (`open`, `locked`, or `closed`),
nullable description and due date. Personal `X-Redmine-API-Key` authentication and sanitized 403/404/502/504 errors apply;
malformed items yield `upstream_response` 502. No write behavior.

Return `list[Version]` without public pagination controls. Require a nonnegative integer
`total_count` in Redmine's collection response and return the array only when
`total_count == len(versions)`. Missing or mismatched count is sanitized `upstream_response` 502,
so a partial upstream collection is never presented as complete. This may reject a paginated
response because the endpoint-specific guide does not confirm usable pagination controls; that
is a documented limitation. Preserve Redmine's returned order. The gateway uses only the shared
account's response and performs no cross-account or local visibility expansion. Redmine's exact
restricted-account sharing outcome remains an acceptance check, not a locally invented guarantee.

## 5. Implementation plan

1. Resolve the blocking collection/visibility evidence and mark the task `specified` or `planned`.
2. Add a typed version model and project-facing port/service/gateway/route.
3. Wire bootstrap and the explicit MCP allowlist; document sharing and pagination truthfully.
4. Add offline mapping/auth/error scenarios and opt-in synthetic visibility checks.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given project versions, when called, then IDs, names, status, owner, and due date map correctly. | REQ-001 | Pending |
| AC-002 | Given an upstream count larger than the returned array, when called, then the result is rejected as an upstream response error rather than shown as complete. | REQ-002 | Pending |
| AC-003 | Given a restricted account, when called, then Redmine's visibility boundaries are preserved. | REQ-003 | Pending |

## 7. Test plan and execution record

VERSION-001: documented count behavior and synthetic sharing evidence. VERSION-002: complete/empty/malformed
mapping. VERSION-003: invalid ID, auth, 403/404/timeout, MCP discovery/call. VERSION-004:
opt-in synthetic shared/private version visibility. Run static, offline, and Inspector checks
after the contract is fixed. All results pending.

## 8. Implementation and review record

The owner accepted official Redmine REST documentation as final contract evidence on
2026-09-30. It documents `total_count` in this collection example and only a general, qualified
pagination pattern. The chosen complete-array contract validates count and fails safely on an
upstream partial response. Earlier failed source-retrieval attempts are superseded as blockers;
restricted-account sharing still needs synthetic acceptance evidence. No tests or live calls ran.
Implemented `Version`, project reader/service/gateway/route, complete-collection count check,
explicit MCP registration, tool reference, and changelog. No test, Inspector, startup, or live
verification was performed in this coding-only stage.
Static checks passed: `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
--check .` (77 files), `.venv/Scripts/python.exe -m mypy src` (38 files), and staged/unstaged
`git diff --check`. Git Bash launch was denied, so existing executables were used. Diff review
found only scoped source and documentation changes beyond the preserved baseline.

## 9. Completion and handoff

- [x] Collection contract resolved from the official REST documentation under the owner's decision.
- [ ] AC-001 through AC-003 have passing evidence.
- [x] Tool reference and dashboard are synchronized.

Final status: blocked; implementation finished, testing pending. Next action: add and run
VERSION-001 through VERSION-004, then perform Inspector and synthetic sharing acceptance in a
separate testing assignment.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

VERSION-002/003 pass offline, including strict collection counts. The sampled base project's empty version set matches Redmine; populated shared/private visibility under contrasting ordinary roles remains pending.

See [the dated verification ledger](../prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_project_versions` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H1 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
