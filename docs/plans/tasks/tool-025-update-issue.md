# tool-025-update-issue: Update issue fields or add a note

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-025-update-issue |
| Assigned capability | Update issue fields or add a note: Do not require Edit issues for notes-only. |
| Type / access / destructive effects | Add writer tool / write / Redmine state mutation |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-024-create-issue](tool-024-create-issue.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Typed field/notes updates, preflight/read-back, writer PUT transport/catalog support, REST route, wiring, and docs implemented; static checks pass. |
| Blocker / next action | User review before tool-026; TOOL-025-001 through TOOL-025-005 and writer fixture verification require separate authorization. |

## 2. Discovery and evidence

The client outcome is **update issue fields or add a note**. Do not require Edit issues for notes-only. Evaluate permission for each supplied field, preserve omissions, reject unknown fields, and compare read-back to expose silently ignored values.
Current catalog has no `update_issue`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Issues) | 2026-10-01 | General/current documentation | PUT /issues/{issue_id}.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz), inspected locally | 2026-10-05 | Exact 7.0.2 | `IssuesController#update` applies safe attributes, conditionally saves uploads, and returns empty 204. `Issue` gates notes by `add_issue_notes`, fields by editable attributes/workflow, parent by `manage_subtasks`, and privacy by separate permissions. `visible_journals_with_index` and `show.api.rsb` expose caller-visible journals. Runtime evidence pending. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `update_issue` is the sole public owner | No |
| Strict sequence | User approved tool-024 commit `d600fda` and directed tool-025 on 2026-10-05 | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Exact update/notes/permissions source reviewed; synthetic acceptance pending | Yes to runtime acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Do not require Edit issues for notes-only. Evaluate permission for each supplied field, preserve omissions, reject unknown fields, and compare read-back to expose silently ignored values.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Edit issues/Edit own issues for fields; Add notes for notes-only; Manage subtasks/privacy as applicable.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Update issue fields or add a note produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"issue_id":1,"notes":"Progress update"}`. Illustrative selected output
fields: `{"resource_id":1,"upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | update_issue |
| Stable operation ID | update_issue |
| Purpose | Update issue fields or add a note; Do not require Edit issues for notes-only. |
| Local REST route | PUT /api/v1/issues/{issue_id} |
| Upstream mapping | PUT /issues/{issue_id}.json |
| Authentication | Personal `X-Redmine-API-Key`; Edit issues/Edit own issues for fields; Add notes for notes-only; Manage subtasks/privacy as applicable. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, destructiveHint=false, idempotentHint=false, openWorldHint=true. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive issue_id; at least one permitted field, uploads, or nonempty notes; private_notes only with notes; explicit null for clearable fields | Positive IDs are strict integers; unknown inputs rejected; omitted update fields never change existing state. Follow specific wording in this row. | PUT /issues/{issue_id}.json |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

Contract frozen on 2026-10-05: supplied issue fields are project/tracker/status/priority IDs,
subject, category/version/assignee/parent IDs, description, dates, hours, done_ratio, is_private,
custom_fields, uploads, notes, and private_notes. Field validation matches tool-024: strict
positive IDs (assignee also `me`), nonblank subject up to 255 characters, finite nonnegative
hours, ISO dates, strict 0..100 done_ratio, strict booleans, unique custom/upload IDs, valid
token/basename metadata. Project is optional and non-null when supplied. Description, assignee,
category, version, parent, dates, and hours can be cleared with explicit null. Omitted fields
are excluded; unknown inputs are rejected. At least one real field/custom-field/upload/note
must be supplied; empty arrays alone do not count. Notes must be nonblank strings and
private_notes requires notes. Creation/copy, watcher mutation, attachment deletion, time entry,
lock_version, and conflict-resolution flags are excluded from this operation.

The writer must explicitly allow update_issue. Redmine enforces field permissions, including
Edit issues/Edit own issues and workflow rules, Add notes without Edit issues for notes-only,
attachment-add permission for uploads, Manage subtasks for parent, and issue/note privacy
permissions. Destination project changes also depend on native allowed-target Add issues.
Do not infer permission from role names or impose Edit issues on every request.

Result: `outcome`, `upstream_accepted`, positive `resource_id`, nullable `journal_id`,
`verification`, `field_verification`, and optional `observed_issue`. Preflight reads the visible
issue; for notes it snapshots strict positive unique visible journal IDs and resolves caller ID.
PUT only supplied fields under `issue`; 204 confirms acceptance. Independently read the same
issue afterward with journals/uploads only as needed. Compare observable fields using the
tool-024 rules; hidden fields are unavailable and ignored/changed observed values mismatch.
Notes verification considers only new caller-authored journals, never old identical notes.
One matching new note supplies journal_id; ambiguous/missing candidates or omitted note fields
are unavailable. Privacy compares the same new journal. Observation is not an atomic attribution
guarantee under concurrent updates. Accepted/uncertain write state survives a failed read-back;
uncertain outcomes require reconciliation before manual repeat, especially for duplicate notes.

Write receipt with requested/observed fields. Accepted-write receipt; verification matched, mismatch, or unavailable. The writer receipt includes `upstream_accepted`, `verification`, returned resource ID where available, and observed-field details; empty upstream 204 is accepted without JSON parsing.
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

- Exact effect: Do not require Edit issues for notes-only. Evaluate permission for each supplied field, preserve omissions, reject unknown fields, and compare read-back to expose silently ignored values.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

Specification exit check: pinned PUT/204, permission distinctions, safe attributes, uploads,
journals, and concurrency limits reviewed; predecessor coding approved. Runtime evidence pending.

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
| AC-001 | REQ-001 | Update issue fields or add a note returns the expected mapped result and resulting Redmine state. | TOOL-025-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-025-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-025-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-025-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-025-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-025-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-025-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-025-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-025-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` | Static checks pass | Passed on 2026-10-05; 172 formatted files and 96 source files checked. Tests/startup/live calls not run. | Passed |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: typed update request/receipt, updater port/service/gateway, authorized PUT route,
  dependency wiring, explicit writer policy, bounded writer PUT support, catalog PUT validation,
  per-field comparisons, preflight/new-journal notes verification, and documentation. Tool-024
  approval recorded alongside this change.
- Plan deviations: request explicitly rejects watcher mutation and attachment deletion because
  those are owned by separate tools. Redmine's authoritative per-field/workflow permission checks
  are retained; application authorization does not add Edit issues to notes-only requests.
  Empty custom/upload arrays alone are not meaningful updates. Preflight captures visible
  journal IDs and caller identity so existing identical notes do not count as new-note evidence.
- Quality: installed Ruff lint/format, mypy, and whitespace passed (EVID-001). Import/format
  fixes were limited to changed files. Automated tests not run under coding-only/user rules.
- Startup/Inspector checks: not run.
- Documentation: task, dashboard, tool reference, changelog, and tool-024 approval updated.
- Final code diff review: router -> service -> updater port -> gateway; positive IDs, omitted/null
  mapping, notes-only access, bounded single PUT, empty 204, independent read-back, no automatic
  retries, author/new-journal checks, no token/note logging, explicit writer-only discovery, and
  retained existing tool defaults inspected. No dependency, test, or live-state changes.
- Remaining blocker: user review before tool-026. Later TOOL-025-001 through TOOL-025-005
  offline work must cover every field, clear/omit validation, notes-only Add notes without Edit
  issues, privacy/parent/workflow distinctions, uploads and ignored fields, 204/invalid success,
  malformed preflight journals, repeated old note text, multiple/new/hidden journals, private
  journal splitting, timeout uncertainty, read-back failure, mixed matched/mismatch/unavailable
  results, reader denial, PUT MCP discovery, and previous transport/tool compatibility. Marked
  7.0.2 prep-008 fixtures must verify actual permission and resulting issue/journal/upload state,
  project moves and workflow behavior, and task-owned cleanup. No live update was performed.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed.
- [x] Final diff reviewed and dashboard synchronized.
- [ ] User accepted this task before the next task starts.

Final status: implementation finished; testing pending. Next action: user review of this coding
commit before tool-026. Separately authorize TOOL-025-001 through TOOL-025-005 and marked writer
fixture verification before runtime acceptance. Static checks do not establish permission/state
acceptance, and a matched observation is not an atomic concurrency guarantee.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
