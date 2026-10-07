# tool-002-get-issue-context: Read related context for one issue

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-002-get-issue-context` |
| Capability | Extend `get_issue` with selectable related context. |
| Type / access / destructive effects | Extend existing tool / read / none |
| Status | blocked; implementation finished, testing pending |
| Last updated | 2026-10-02, Codex |
| Dependencies | [prep-002](prep-002-offline-tests.md) |
| Target | Redmine 7.0.2; reactions remain outside the scoped contract |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

Current `get_issue(issue_id)` requests `journals,attachments` and returns `Issue`. The shared
model already has journals and attachment metadata. The [Redmine Issues API](https://www.redmine.org/projects/redmine/wiki/rest_issues)
documents children, attachments, relations, changesets, journals, watchers, and
allowed statuses for issue detail. Upstream decides which related data is visible to the shared
account and which status transitions are allowed; this tool makes no local workflow prediction.
The documentation was reviewed 2026-09-30.

## 3. Requirements

| ID | Client need | Observable behavior |
|---|---|---|
| REQ-001 | Inspect issue context without several unrelated tools. | Caller can select documented detail expansions. |
| REQ-002 | Distinguish omitted expansions from no related data. | The description states which data was requested; omitted default remains journals and attachments. |
| REQ-003 | Keep prior clients working. | Existing operation name, issue ID validation, and default result shape remain compatible. |

## 4. Public contract and technical specification

Keep `get_issue`, `GET /api/v1/issues/{issue_id}`, positive integer `issue_id`, and `Issue` result.
Add optional `include` as a comma-separated string of unique values from `children`,
`attachments`, `relations`, `changesets`, `journals`, `watchers`, `allowed_statuses`. Omission
requests `journals,attachments`; an explicit empty string requests no expansions. Reject empty
CSV segments, duplicates, unknown values, and `reactions` with 422 before upstream access.
Preserve caller order in the forwarded list. Map nonempty selection to Redmine
`GET issues/{issue_id}.json?include=<csv>`; omit `include` when explicitly empty.

Extend `Issue` with `children` (list of issue references), `relations` (ID, source/target issue
IDs, relation type, optional delay), `watchers` (references), and `allowed_statuses` (ID, name,
closed flag). Keep changesets as JSON object arrays until the 7.0.2 serializer contract is
confirmed; restrict values to JSON types. All four collections default to empty arrays for
backward response compatibility. Document that an empty array for an unrequested expansion says
nothing about upstream related data. Do not download attachment content.

Existing personal `X-Redmine-API-Key` authentication and sanitized upstream error mapping apply. Hidden issue is 404; forbidden
data follows Redmine visibility. MCP error envelope is adapter-owned. Write semantics: N/A.

## 5. Implementation plan

1. Add include parsing/validation at the route and pass the selection through service and port.
2. Extend shared Issue response models and gateway mapping; keep old fields/defaults.
3. Preserve `get_issue` in the explicit allowlist and update descriptions/tool reference.
4. Verify default, explicit empty, each include, rejected input, and visibility with offline and
   opt-in synthetic scenarios.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given supported includes, when reading a visible issue, then the exact selection reaches Redmine and returned related data is mapped. | REQ-001 | Pending |
| AC-002 | Given omission or explicit empty include, when reading, then default expansions or no expansion are requested respectively. | REQ-002 | Pending |
| AC-003 | Given an old `issue_id` call or invalid include, when using REST/MCP, then old behavior is preserved or validation occurs before upstream. | REQ-003 | Pending |

## 7. Test plan and execution record

DETAIL-001: omitted default and explicit empty. DETAIL-002: supported combinations and nested
mapping. DETAIL-003: duplicate/unknown/invalid ID rejected. DETAIL-004: visibility, malformed
upstream, 403/404/timeout, MCP envelope. DETAIL-005: opt-in synthetic private journal and
allowed-status behavior. Run static, offline, and Inspector checks. All results pending.

## 8. Implementation and review record

Implementation finished; testing pending. Previously inspected Redmine
`show.api.rsb` (prior source inspection; current release review pending)
serializes changesets as JSON objects with revision, optional user, comments, and committed time.
Its children serializer is recursive, so the model preserves nested children. Added include
validation and passed selections through router, service, port, and gateway. Added related fields,
tool reference, and changelog. No tests, startup, Inspector, or live calls were run.
Static checks: `.venv/Scripts/ruff.exe check .` passed, `.venv/Scripts/ruff.exe format
--check .` passed (71 files), `.venv/Scripts/python.exe -m mypy src` passed (32 files), and
`git diff --check` plus `git diff --cached --check` passed. Git Bash launch was denied by
this environment, so existing Windows executables were used for static checks. Diff review
found only task-scoped source and documentation changes beyond the preserved baseline.

## 9. Completion and handoff

- [ ] AC-001 through AC-003 have passing evidence.
- [x] Tool reference and dashboard match the implemented includes.

Final status: blocked. Next action: implement and run DETAIL-001 through DETAIL-005, then run
required repository and synthetic acceptance checks in a separate testing assignment.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

DETAIL-001 through DETAIL-004 pass offline. Same-reader journal IDs/private flags and empty allowed statuses match Redmine; contrasting ordinary-role visibility and nonempty transitions remain pending.

See [the dated verification ledger](../../testing/evidence/prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.

## Prep-020 evidence reconciliation, 2026-10-07

Current `get_issue` functional evidence is mapped in the
[32-operation ledger](../../testing/evidence/current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H1/H2 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
