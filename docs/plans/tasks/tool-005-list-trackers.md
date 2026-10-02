# tool-005-list-trackers: Resolve tracker choices

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `tool-005-list-trackers` |
| Capability | Let clients understand tracker IDs and their supported standard fields. |
| Type / access / destructive effects | Add tool / read / none |
| Status | blocked; implementation finished, testing pending |
| Last updated | 2026-10-02, Codex |
| Dependencies | [prep-002](prep-002-offline-tests.md) |
| Target | Redmine 7.0.2; runtime acceptance pending |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

Issues include tracker references but no tracker catalog is exposed. [Redmine Trackers](https://www.redmine.org/projects/redmine/wiki/Rest_Trackers)
documents IDs, names, default status, description, and enabled standard fields (reviewed
2026-09-30). The target behavior still needs checking. The global catalog does not prove
that a tracker is enabled in every project.

## 3. Requirements

| ID | Client need | Observable behavior |
|---|---|---|
| REQ-001 | Interpret tracker references and field availability. | Return ID, name, optional description/default status, and supported standard field names. |
| REQ-002 | Avoid claiming project-specific availability. | Description identifies the result as the global catalog. |

## 4. Public contract and technical specification

Add no-input `list_trackers` at `GET /api/v1/trackers`, with explicit MCP allowlist entry.
Return `list[Tracker]`: positive `id`, nonempty `name`, nullable `description`, nullable
`default_status` reference, and `enabled_standard_fields: list[str]` defaulting to empty when
upstream omits it. Map `trackers` from `GET trackers.json`. Empty array is valid; missing array,
invalid nested data, or malformed JSON is sanitized `upstream_response` 502. Personal `X-Redmine-API-Key` authentication and
existing upstream errors apply. No pagination or write behavior is introduced.

## 5. Implementation plan

Add typed reference-data layers and bootstrap dependency, register the stable operation, update
tool reference/changelog, and verify the nested field mapping and public description. Reuse the
shared Redmine client without introducing a generic CRUD framework.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given a tracker array, when called, then names, default status, and enabled fields map without loss. | REQ-001 | Pending |
| AC-002 | Given the documented tool description, when inspected, then project availability is not implied. | REQ-002 | Pending |

## 7. Test plan and execution record

TRACKER-001: populated/empty and optional fields. TRACKER-002: malformed, 403/timeout, auth,
MCP discovery/call. TRACKER-003: opt-in synthetic comparison with project tracker settings.
Static, offline, and Inspector evidence pending.

## 8. Implementation and review record

Implementation finished; testing pending. Added typed tracker model, reference reader/service,
Redmine gateway, authenticated REST route, explicit MCP registration, tool reference, and
changelog. The route describes global rather than project-specific availability. Shared
collection mapping rejects malformed roots or items. No tests, startup, Inspector, or live calls
ran; target response and permissions need synthetic confirmation.
Static checks passed: `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
--check .` (77 files), `.venv/Scripts/python.exe -m mypy src` (38 files), and staged/unstaged
`git diff --check`. Git Bash launch was denied, so existing executables were used. Diff review
found only scoped changes beyond the preserved baseline.

## 9. Completion and handoff

- [ ] AC-001 and AC-002 have passing evidence.
- [x] Documentation and dashboard are synchronized.

Final status: blocked. Next action: add and run TRACKER-001 through TRACKER-003, including
Inspector and synthetic project comparison, in a separate testing assignment.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

TRACKER-001/002 pass offline. Three registry tracker IDs/names match Redmine; full comparison against visible project tracker settings and a clean live rerun remain pending.

See [the dated verification ledger](../prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.
