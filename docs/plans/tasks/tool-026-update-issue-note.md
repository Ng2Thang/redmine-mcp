# tool-026-update-issue-note: Edit a journal note

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-026-update-issue-note |
| Assigned capability | Edit a journal note: Verify journal belongs to issue and caller can view it before update. |
| Type / access / destructive effects | Add writer tool / write / Redmine state mutation |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-025-update-issue](tool-025-update-issue.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Typed note request/receipt, scoped journal gateway, port/service/REST route, wiring, writer policy/annotations, and docs implemented; static checks pass. |
| Blocker / next action | User approved coding commit `6aef9de` and directed tool-027; TOOL-026-001 through TOOL-026-005 and marked writer verification require separate authorization. |

## 2. Discovery and evidence

The client outcome is **edit a journal note**. Verify journal belongs to issue and caller can
view it before update. Empty notes can remove an entry from visible issue history without
deleting its journal row; disclose this effect and verify through get_issue journals.
Current catalog has no `update_issue_note`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Journals) | 2026-10-01 | General/current documentation | PUT /journals/{journal_id}.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz), inspected locally | 2026-10-05 | Exact 7.0.2 | `JournalsController` finds a visible journal, checks `editable_by?`, applies journal safe attributes, and returns 204. `Journal#save` does not delete an existing blank journal; `Issue#visible_journals_with_index` filters entries with neither notes nor visible details. Pinned functional test source explicitly asserts empty notes do not delete the journal; read only, not executed. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `update_issue_note` is the sole public owner | No |
| Strict sequence | User approved tool-025 commit `27cae75` and directed tool-026 on 2026-10-05 | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Exact PUT/204, permission and visibility source reviewed; synthetic acceptance pending | Yes to runtime acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Verify visible journal membership before updating supplied notes/privacy. Empty
  notes may hide an entry with no visible details; do not claim this deletes its stored row.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Edit notes or Edit own notes; Set notes private when requested.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Edit a journal note produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"issue_id":1,"journal_id":2,"notes":"Corrected"}`. Illustrative selected output
fields: `{"resource_id":2,"upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | update_issue_note |
| Stable operation ID | update_issue_note |
| Purpose | Edit a journal note; Verify journal belongs to issue and caller can view it before update. |
| Local REST route | PUT /api/v1/issues/{issue_id}/notes/{journal_id} |
| Upstream mapping | PUT /journals/{journal_id}.json |
| Authentication | Personal `X-Redmine-API-Key`; Edit notes or Edit own notes; Set notes private when requested. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, destructiveHint=true, idempotentHint=false, openWorldHint=true; supplied notes can overwrite or clear existing text. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive issue_id,journal_id; notes optional string,private_notes optional boolean; at least one supplied | Positive IDs are strict integers; unknown inputs rejected; omitted update fields never change existing state. Follow specific wording in this row. | PUT /journals/{journal_id}.json |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

Contract frozen on 2026-10-05: positive issue/journal path IDs validated before upstream
access. Body contains optional string `notes` (including empty/whitespace strings) and optional
strict boolean `private_notes`; at least one must be supplied. Explicit null and unknown body
fields are rejected. Omitted fields are excluded. Privacy-only changes are valid for this
operation; it edits an existing note rather than adding one. Redmine requires `edit_issue_notes`
or `edit_own_issue_notes` for the author, with `set_notes_private` for supplied privacy changes.
No application Edit issues requirement is added; the restricted writer must allow this tool.

Preflight GET /issues/{issue_id}.json?include=journals must expose the requested positive,
unique journal ID. Missing journal membership is a safe 404 before PUT; malformed membership
or journal data is a safe 502. PUT /journals/{journal_id}.json sends only supplied fields under
`journal`; Redmine sets updated_by itself. HTTP 204 confirms acceptance. Read the same issue's
journals independently afterward and match the same journal ID, not note text from another row.

Receipt: `outcome`, `upstream_accepted`, `issue_id`, `resource_id` (journal ID), `verification`,
`field_verification`, nullable `observed_present`, and optional `observed_journal` with caller
visibility metadata. For a returned journal, compare supplied fields only; missing fields are
unavailable and observed differences mismatch. For visible absence, observed_present is false
and field verification remains unavailable, even after clearing text. Absence can reflect
filtering/privacy/concurrency and does not prove deletion or successful clearing. Failed
read-back leaves presence unknown and preserves write acceptance/uncertainty. No retries,
locking, database reads, hidden-journal bypass, or rollback promise are introduced.

Write receipt with journal identity/read-back. Accepted-write receipt; verification matched, mismatch, or unavailable. The writer receipt includes `upstream_accepted`, `verification`, returned resource ID where available, and observed-field details; empty upstream 204 is accepted without JSON parsing.
No upstream pagination applies to this operation.
Existing REST/MCP error envelopes remain compatible. A new operation must be
registered exactly once and must not change defaults of another operation.

| Scenario | Public handling |
|---|---|
| Invalid input | Local 422 before upstream call; MCP reports tool error. |
| Missing or invalid key | Existing sanitized 401; no upstream data leaked. |
| Forbidden or absent upstream resource | Existing 403 or visibility-safe 404. |
| Redmine validation failure | Sanitized 422; no raw upstream body in logs/results. |
| Timeout, transport, oversized or malformed response | Existing 504/502-family sanitized errors; post-dispatch result remains uncertain. |
| Other upstream status | Existing sanitized upstream error; no automatic retry. |

### Write semantics

- Exact effect: overwrite/clear supplied note text or change its privacy after proving visible
  issue membership. Blank notes without visible details can disappear from issue history;
  existing journal rows are retained by the pinned source. Redmine records updated_by.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

Specification exit check: exact 7.0.2 update/permission/empty-note source reviewed and draft
deletion claim corrected; predecessor coding approved. Runtime acceptance remains pending.

## 5. Implementation plan

| Step | Concrete change | Owner/components | Dependency and review |
|---|---|---|---|
| 1 | Confirm exact 7.0.2 endpoint, permission, response, and side effects; freeze contract. | This task document | prep-005 evidence; specification review |
| 2 | Add or extend typed models and Protocol port; preserve public defaults. | Feature models/ports | Step 1; type review |
| 3 | Map upstream request/response and sanitized errors using bounded async client. | Redmine gateway | Step 2; gateway review |
| 4 | Implement service, REST validation, and dependency wiring. | Service/router/bootstrap | Step 3; architecture review |
| 5 | Update explicit MCP catalog, application policy, and annotations if public. | MCP/auth modules | Step 4; discovery review |
| 6 | Update English tool docs and task execution record; run applicable static checks. | docs/scripts | Step 5; diff review |
| 7 | Hand off planned offline/Inspector scenarios to separately authorized testing stage. | Testing owner | User testing authorization, then user acceptance |

For a shared prerequisite, omit irrelevant public layers and record why in
the implementation review. No dependency or lockfile change is assumed;
record any newly required package and update `uv.lock` together.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Planned scenario | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | Edit a journal note returns the expected mapped result and resulting Redmine state. | TOOL-026-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-026-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-026-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-026-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-026-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-026-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-026-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-026-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-026-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` | Static checks pass | Passed on 2026-10-05; 173 formatted files and 97 source files checked. Tests/startup/live calls not run. | Passed |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: typed note edit request/receipt and journal observation, note-updater Protocol,
  service validation, scoped journal gateway, authorized PUT route, dependency wiring, explicit
  writer policy, destructive text-edit hints, tool reference, changelog, and dashboard. Tool-025
  approval recorded alongside this implementation.
- Plan deviations: corrected the draft's deletion claim against exact source and existing
  functional test source (read only). Blank notes retain the journal row but may hide it from
  issue history. Visible absence never proves clearing/deletion; field verification remains
  unavailable. Omitted fields are preserved and privacy-only changes are allowed.
- Quality: installed Ruff lint/format, mypy, and whitespace passed (EVID-001). Formatting was
  applied only to changed files. Automated tests not run under coding-only/user instructions.
- Startup/Inspector checks: not run.
- Documentation: task, dashboard, tool reference, changelog, and predecessor approval updated.
- Final code diff review: router -> service -> note-updater port -> gateway; strict service IDs,
  body validation, visible issue membership, positive unique journal IDs, targeted journal
  validation before dispatch, single bounded PUT, empty 204, supplied-only payload, unchanged
  upstream permissions, independent same-ID read-back, missing/absent/malformed fields, no
  note logging, no retries, and writer-only catalog inspected. No dependency, test, or live data
  changes were made. Existing creation/update/default reader contracts remain unchanged.
- Remaining blocker: separately authorized testing. TOOL-026-001 through TOOL-026-005 later offline
  work must cover text/privacy/both, empty and whitespace notes, null/unknown/empty body, invalid
  IDs, wrong/hidden issue-journal membership, duplicate/malformed journal IDs, malformed target,
  Edit notes/Edit own notes/Set notes private distinctions, 204, ignored privacy/mismatched text,
  missing fields, returned/filtered journals, timeout and read-back failure, reader denial,
  destructive MCP hints, and existing tool compatibility. Marked 7.0.2 prep-008 fixtures must
  verify actual permissions, author/updated_by state, private visibility, retained journal rows
  after blanking, visible details, and task-owned cleanup. No live journal was edited.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed.
- [x] Final diff reviewed and dashboard synchronized.
- [x] User accepted this task before the next task starts.

User approval (2026-10-05): accepted implementation commit `6aef9de` and requested tool-027.
This approves coding progression; runtime acceptance remains pending.

Final status: implementation finished; testing pending. Next action: separately authorize
TOOL-026-001 through TOOL-026-005 and marked writer
fixture verification before runtime acceptance. Static checks do not prove journal state or
permission behavior; filtered visible history does not prove row deletion.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.

## Prep-020 evidence reconciliation, 2026-10-07

Current `update_issue_note` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H2 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
