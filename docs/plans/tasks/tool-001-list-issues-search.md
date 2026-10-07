# tool-001-list-issues-search: Find work in visible issues

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-001-list-issues-search` |
| Capability | Extend `list_issues` so a client can narrow and order work. |
| Type / access / destructive effects | Extend existing tool / read / none |
| Status | complete; implementation and acceptance verified |
| Last updated | 2026-09-30 |
| Dependencies | [prep-002](prep-002-offline-tests.md) |
| Target | Redmine 7.0.2; runtime acceptance pending |
| Next action | None for this task. |

## 2. Discovery and evidence

Current `list_issues` accepts `project_id`, `status_id`, `assigned_to_id`, `limit`, and `offset`;
defaults are open status, 25 results, offset 0, and upstream `id:asc`. Its result is `Page[Issue]`.
The shared Redmine identity determines visibility and the meaning of `me`. The [Redmine Issues
API](https://www.redmine.org/projects/redmine/wiki/rest_issues) documents tracker, parent,
updated-time filtering and sorting (reviewed 2026-09-30). Read-only Inspector calls against the
marked Previously inspected Redmine container confirmed combined filtering and sorting for visible
synthetic issues. This does not establish permissions for other accounts or instances.

## 3. Requirements

| ID | Client need | Observable behavior |
|---|---|---|
| REQ-001 | Find a smaller work queue. | Optional tracker, parent, and last-updated filters combine with existing filters. |
| REQ-002 | Review recent work first. | A bounded sort choice changes ordering without changing omitted defaults. |
| REQ-003 | Keep existing clients working. | Name, prior inputs, pagination, output wrapper, auth, and omitted-input behavior remain stable. |

## 4. Public contract and technical specification

Keep operation ID `list_issues`, `GET /api/v1/issues`, and `Page[Issue]`. Add optional
`tracker_id` and `parent_id` as positive integers, `updated_since` as an RFC 3339 timestamp with
timezone, and `sort` as one of `id:asc`, `id:desc`, `updated_on:asc`, or `updated_on:desc`; default
`id:asc`. Existing inputs and defaults are unchanged. Omitted new filters are not forwarded;
explicit empty strings or invalid IDs/timestamps/sort return FastAPI 422 before Redmine.

Map new inputs to Redmine `tracker_id`, `parent_id`, `updated_on=>=<timestamp>`, and `sort` on
`GET issues.json`; let HTTPX encode the query once. Normalize aware timestamps to UTC `Z` at the
gateway, preserving the caller's instant: the pinned Redmine instance returned 422 for an
equivalent `+00:00` offset and accepted `Z`. Preserve `status_id=open` and the current
ascending ID request by default. Keep response mapping to `Page[Issue]`; no new response field
is required for this task. `updated_since` is inclusive in upstream query syntax, without a
snapshot guarantee. No free-text search or arbitrary Redmine query pass-through.

Require the existing bearer token. Preserve sanitized 403, 404, 502, and 504 mapping; malformed
upstream JSON/model data is `upstream_response` 502. MCP uses the adapter's tool-result/error
envelope; do not promise REST status as the outer MCP response. Write semantics: N/A, read-only.

## 5. Implementation plan

1. Extend validated route inputs, service method, `IssueReader` Protocol, and gateway arguments.
2. Centralize timestamp serialization at the gateway boundary, preserving timezone information.
3. Keep the existing explicit MCP operation; update description, tool reference, and changelog.
4. Add offline REST/MCP and adapter scenarios; run synthetic read verification separately.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given a tracker, parent, and timestamp, when listing, then the exact encoded upstream filters are sent and only visible results are returned. | REQ-001 | Pass: offline exact-query assertion and marked synthetic Inspector call returned the selected visible child with all three filters. |
| AC-002 | Given each supported sort, when listing, then ordering is forwarded; omission still sends `id:asc`. | REQ-002 | Pass: four offline sort cases, old default assertion, and synthetic descending update/ID ordering. |
| AC-003 | Given old client inputs, when listing through REST/MCP, then name, schema, defaults, pagination, auth, and error behavior remain compatible. | REQ-003 | Pass: 32-test offline suite, MCP discovery and invocation, and old-default/pagination assertions. |

## 7. Test plan and execution record

LIST-001: old defaults and pagination. LIST-002: combined filters and RFC 3339 encoding.
LIST-003: sort enum and invalid values rejected before upstream. LIST-004: empty, malformed,
forbidden, timeout, and MCP error results. LIST-005: opt-in synthetic visibility and ordering.
On 2026-09-30, `uv run --frozen pytest tests/test_list_issues_search.py` passed 22 offline tests.
`bash scripts/check.sh` passed Ruff lint, Ruff format (71 files), and mypy (32 source files);
`uv run --frozen pytest` passed 32 offline tests (one Pydantic dependency deprecation warning);
`git diff --check` passed. An initial full static run found test import ordering, and an initial
live call exposed Redmine's rejection of `+00:00`; both were corrected before passing results.
After those checks, the user supplied a new instruction against automatic unit-test verification;
no further unit tests were run after that instruction. All automated results here predate it.

Inspector CLI 2.8.0 on the already-running local MCP server discovered exactly `list_projects`,
`list_issues`, and `get_issue`. The previously observed Redmine container was healthy and had
`REDMINE_TEST_MARKER=redmine-mcp-synthetic-v1`. A read-only all-status call reported 150 issues
at verification time. Combined tracker, parent, and inclusive `updated_since` filters found the
selected visible child; `updated_on:desc` and `id:desc` results were ordered as requested. A
direct read-only comparison confirmed the pinned Redmine instance accepted `Z` and returned 422
for `+00:00`. No Docker start, seed, reset, restore, write call, or external Redmine call occurred.
Offline mock results and live synthetic observations are separate evidence.

## 8. Implementation and review record

Coding stage on 2026-09-30: extended the issue route, service, port, and Redmine gateway with
validated tracker, parent, update-time, and sort inputs. The gateway serializes the aware
timestamp as UTC `Z` and lets HTTPX encode the `>=` operator. Existing defaults and the
`Page[Issue]` result remain. Updated the tool reference and changelog. Ruff formatting was
applied only to the four touched source files. Static results: `uv run --frozen --no-sync ruff
check .` passed; `uv run --frozen --no-sync ruff format --check .` reported 70 files formatted;
`uv run --frozen --no-sync mypy src` reported no issues in 32 source files; `git diff --check`
passed. The first Ruff run found misplaced imports from the initial edit; these were corrected
before the passing run. No tests, startup, Inspector, or live calls ran in the coding stage.
The verification stage added `tests/test_list_issues_search.py` for LIST-001 through LIST-004 and
ran LIST-005 via Inspector. Target-version evidence changed timestamp serialization from an
unchanged numeric timezone offset to normalized UTC `Z`, preserving the instant. No model or MCP
allowlist edit was needed because `Page[Issue]` and the explicit `list_issues` registration already
matched the contract. The retired issue backlog and unrelated staged changes were preserved.

## 9. Completion and handoff

- [x] AC-001 through AC-003 have passing evidence.
- [x] Tool reference, tests, and dashboard reflect the final contract.

Final status: complete. Next action: none for this task.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_issues` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H1 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
