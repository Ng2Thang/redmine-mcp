# tool-023-delete-attachment: Delete one attachment

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-023-delete-attachment |
| Assigned capability | Delete one attachment: Confirm attachment belongs to declared container; 204 can delete stored bytes. |
| Type / access / destructive effects | Add writer tool / write / Resource deletion or removal |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-022-update-attachment](tool-022-update-attachment.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Writer-only deletion, shared container proof, REST route, wiring, MCP policy/annotations, and documentation implemented; static checks pass. |
| Blocker / next action | User approved commit `c6ef155` on 2026-10-05 and directed continuation to tool-024. TOOL-023-001 through TOOL-023-005 require separately authorized verification. |


Document attachment containers are excluded from the 7.0.2 contract.

## 2. Discovery and evidence

The client outcome is **delete one attachment**. Confirm attachment belongs to declared container by reading the containing Project/Version file list or Issue and comparing attachment IDs; the attachment metadata endpoint alone is insufficient. A 204 may mean stored bytes were removed. Do not delete when container identity is unverified; no rollback promise.
Current catalog has no `delete_attachment`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Attachments) | 2026-10-01 | General/current documentation | DELETE /attachments/{attachment_id}.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| [Exact release source](https://www.redmine.org/releases/redmine-7.0.2.tar.gz), inspected from `.local/upgrades/source/redmine-7.0.2.tar.gz` | 2026-10-05 | 7.0.2 | `AttachmentsController#destroy` checks `deletable?`, initializes Issue journals, removes the attachment through association callbacks, and returns HTTP 204. `Attachment` deletes stored bytes after commit; Project/Version require `manage_files`; Issue requires visibility and editable issue attributes. Runtime evidence remains pending. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `delete_attachment` is the sole public owner | No |
| Strict sequence | User approved tool-022 on 2026-10-05 and assigned tool-022 through tool-027 coding with review after each task | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Exact 7.0.2 source reviewed; synthetic behavior remains pending | Yes to runtime acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Confirm attachment belongs to declared container; 204 can delete stored bytes. Do not delete when container identity is unverified; no rollback promise.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: restricted writer explicitly allows `delete_attachment`.
  Project/Version requires visibility and `manage_files`; Issue requires visibility and
  tracker-aware `edit_issues`, or `edit_own_issues` for the issue author. Redmine enforces access.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Delete one attachment produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"attachment_id":1,"container_type":"project","container_id":1}`. Illustrative selected output
fields: `{"upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | delete_attachment |
| Stable operation ID | delete_attachment |
| Purpose | Delete one attachment; Confirm attachment belongs to declared container; 204 can delete stored bytes. |
| Local REST route | DELETE /api/v1/attachments/{attachment_id} |
| Upstream mapping | DELETE /attachments/{attachment_id}.json |
| Authentication | Personal `X-Redmine-API-Key`; Container-specific attachment delete permission. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, idempotentHint=false, openWorldHint=true; destructiveHint=true for deletion. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive attachment_id path; required container_type query enum project/version/issue and positive container_id query | Required query inputs; unknown query inputs rejected; IDs validated before upstream access. Service IDs and body-model IDs are strict positive integers. No request body. | DELETE /attachments/{attachment_id}.json; no container parameters forwarded |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

Write receipt; verify resource absence if caller can read it. Accepted-write receipt; verification matched, mismatch, or unavailable. The writer receipt includes `upstream_accepted`, `verification`, returned resource ID where available, and observed-field details; empty upstream 204 is accepted without JSON parsing.
Result: `outcome` accepted/uncertain, `upstream_accepted` true for confirmed 204 or null,
`attachment_id`, `verification` matched/mismatch/unavailable, and nullable `observed_present`.
Preflight uses the visible Issue attachment array or Project file list; Version resolves its
owning project and requires a matching version reference. Missing membership is a safe 404
before DELETE. Malformed membership data fails with 502. After dispatch, repeat the same
container read; visible absence is matched, presence is mismatch, and any failed read is
unavailable. A 404 from a failed container read is not proof of deletion. Visible absence does
not prove stored-byte removal or unrestricted visibility. Uncertain dispatch stays uncertain
even when read-back observes absence. No download is performed.
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

- Exact effect: Confirm attachment belongs to declared container; 204 can delete stored bytes. Do not delete when container identity is unverified; no rollback promise.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

Specification exit check: exact 7.0.2 deletion, empty success, side effects, permissions, and
container-proof sources reviewed. Predecessor coding approved; runtime acceptance remains pending.

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
| AC-001 | REQ-001 | Delete one attachment returns the expected mapped result and resulting Redmine state. | TOOL-023-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-023-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-023-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-023-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-023-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-023-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-023-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-023-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-023-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` | Static checks pass | Passed on 2026-10-05; 168 formatted files and 92 source files checked. No automated tests or runtime calls. | Passed |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: shared typed container request, delete query/result, deleter Protocol/service,
  deletion gateway, REST DELETE route, dependency wiring, explicit writer registration,
  destructive MCP hints, tool reference, changelog, and synchronized dashboard.
- Plan deviations: DELETE uses required query inputs rather than a body to fit REST-backed MCP
  discovery. Query IDs are parsed from strings; service IDs remain strict positive integers.
  Container membership logic is shared with tool-022; malformed Issue attachment IDs now fail
  safely with 502. A failed container read never counts as verified absence.
- Quality: installed Ruff lint/format, mypy, and whitespace checks passed (EVID-001).
  Automated tests: not run under the user instruction and coding-only skill.
- Startup/Inspector checks: not run.
- Documentation: task, dashboard, tool reference, and changelog updated in English.
- Final code diff review: router -> service -> port -> gateway, explicit writer-only exposure,
  no retry/download, single DELETE, empty 204 handling, independent read-back, and preserved
  tool-022 inputs/results inspected. No dependency changes or unrelated edits.
- User review: commit `c6ef155` approved on 2026-10-05; user directed continuation to tool-024.
- Remaining blocker: TOOL-023-001 through TOOL-023-005 runtime
  acceptance. Later offline checks must cover all three containers, wrong containers, malformed
  proof, query validation/unknown fields, 204, timeouts, read-back absence/presence/failure,
  reader denial, destructive discovery hints, and tool-022 compatibility. Opt-in marked 7.0.2
  checks require prep-008 fixtures, actual permission/state evidence, Issue journals, stored-byte
  effects, and task-owned cleanup. No live deletion or data creation was performed.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed.
- [x] Final diff reviewed and dashboard synchronized.
- [x] User approved the implementation on 2026-10-05 and directed continuation to tool-024.

Final status: implementation finished; user review approved; testing pending. User approved
commit `c6ef155` on 2026-10-05 and directed continuation to tool-024. Separately authorize TOOL-023-001 through TOOL-023-005
verification before runtime acceptance; static checks do not establish deletion/state evidence.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
