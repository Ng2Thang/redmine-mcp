# tool-008-list-project-issue-categories: Find project issue categories

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-008-list-project-issue-categories` |
| Capability | Let clients discover category IDs used by a project. |
| Type / access / destructive effects | Add tool / read / none |
| Status | blocked; implementation finished, testing pending |
| Last updated | 2026-09-30 |
| Dependencies | [prep-002](prep-002-offline-tests.md) |
| Target | Redmine 6.0.5-bookworm |
| Next action | Add and run CATEGORY-001 through CATEGORY-004 in a separate testing assignment, including synthetic visibility and count behavior. |

## 2. Discovery and evidence

No category lookup tool exists. [Redmine Issue Categories](https://www.redmine.org/projects/redmine/wiki/Rest_IssueCategories)
documents a project category list with category ID, name, project, and optional default assignee
(reviewed 2026-09-30).
The example has `total_count` but does not establish endpoint-specific `limit`/`offset` support.
The [general REST pagination guide](https://www.redmine.org/projects/redmine/wiki/Rest_api#Collection-resources-and-pagination)
says collections generally paginate without an endpoint-specific guarantee. Per the owner's
2026-09-30 decision, these official docs are the final specification reference; no versioned
source inspection is required. Restricted-account visibility remains a synthetic acceptance
check.

## 3. Requirements

| ID | Client need | Observable behavior |
|---|---|---|
| REQ-001 | Interpret or choose project category IDs. | Return visible category ID, name, project, and optional assignee. |
| REQ-002 | See all categories or explicit pages. | Result never presents one upstream page as the complete set. |
| REQ-003 | Respect project visibility. | Restricted callers cannot use category lookup to expose hidden project data. |

## 4. Public contract and technical specification

Proposed operation `list_project_issue_categories`, route
`GET /api/v1/projects/{project_id}/issue-categories`, positive integer project ID, and upstream
`GET projects/{project_id}/issue_categories.json`. Proposed `IssueCategory` item: positive ID,
nonempty name, project reference, nullable assignee reference. Bearer auth and existing
sanitized 403/404/502/504 errors apply; malformed array/items yield `upstream_response` 502.
No category creation/update/delete or write behavior.

Return `list[IssueCategory]` without public pagination controls. Require a nonnegative integer
`total_count` in Redmine's collection response and return the array only when
`total_count == len(issue_categories)`. Missing or mismatched count is sanitized
`upstream_response` 502, so a partial upstream collection is never presented as complete. This
may reject a paginated response because the endpoint-specific guide does not confirm usable
pagination controls; that is a documented limitation. Preserve Redmine's returned order. The
gateway uses only the shared account's response and performs no local visibility expansion.

## 5. Implementation plan

1. Resolve the blocking collection/visibility evidence and mark the task `specified` or `planned`.
2. Add a typed category model and project-facing port/service/gateway/route.
3. Wire bootstrap and explicit MCP allowlist; document pagination and assignee meaning.
4. Add offline mapping/auth/error scenarios and opt-in synthetic visibility checks.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given a category collection, when called, then ID, name, project, and assignee map correctly. | REQ-001 | Pending |
| AC-002 | Given an upstream count larger than the returned array, when called, then the result is rejected as an upstream response error rather than shown as complete. | REQ-002 | Pending |
| AC-003 | Given a restricted account, when called, then project visibility is preserved. | REQ-003 | Pending |

## 7. Test plan and execution record

CATEGORY-001: documented count behavior and synthetic visibility evidence. CATEGORY-002: populated/empty/
malformed mapping. CATEGORY-003: invalid ID, auth, 403/404/timeout, MCP discovery/call.
CATEGORY-004: opt-in synthetic private project boundary. Run static, offline, and Inspector
checks after contract resolution. All results pending.

## 8. Implementation and review record

The owner accepted official Redmine REST documentation as final contract evidence on
2026-09-30. It documents `total_count` in this collection example and only a general, qualified
pagination pattern. The chosen complete-array contract validates count and fails safely on an
upstream partial response. Earlier failed source-retrieval attempts are superseded as blockers;
restricted-account visibility still needs synthetic acceptance evidence. No tests or live calls
ran.
Implemented `IssueCategory`, project reader/service/gateway/route, complete-collection count
check, explicit MCP registration, tool reference, and changelog. No test, Inspector, startup,
or live verification was performed in this coding-only stage.
Static checks passed: `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
--check .` (77 files), `.venv/Scripts/python.exe -m mypy src` (38 files), and staged/unstaged
`git diff --check`. Git Bash launch was denied, so existing executables were used. Diff review
found only scoped source and documentation changes beyond the preserved baseline.

## 9. Completion and handoff

- [x] Collection contract resolved from the official REST documentation under the owner's decision.
- [ ] AC-001 through AC-003 have passing evidence.
- [x] Tool reference and dashboard are synchronized.

Final status: blocked; implementation finished, testing pending. Next action: add and run
CATEGORY-001 through CATEGORY-004, then perform Inspector and synthetic visibility acceptance
in a separate testing assignment.
