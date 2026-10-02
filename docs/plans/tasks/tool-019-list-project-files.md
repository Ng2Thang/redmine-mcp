# tool-019-list-project-files: List project files

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-019-list-project-files |
| Assigned capability | List project files: Return project and version files from the documented unpaged endpoint. |
| Type / access / destructive effects | Add reader tool / read / None |
| Status | blocked - documentation draft; no code or verification performed |
| Dependencies | [tool-016-list-document-categories](tool-016-list-document-categories.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Tool outcome and draft contract assigned; implementation and testing not started. |
| Blocker / next action | Predecessor tool-016-list-document-categories must be accepted and exact 7.0.2 source/behavior rechecked. |

## 2. Discovery and evidence

The client outcome is **list project files**. Return project and version files from the documented unpaged endpoint. Do not silently truncate or manufacture counts.
Current catalog has no `list_project_files`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Files) | 2026-10-01 | General/current documentation | GET /projects/{project_id}/files.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `list_project_files` is the sole public owner | No |
| Strict sequence | Wait for tool-016-list-document-categories evidence and explicit user acceptance | Yes to execution |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Use pinned 7.0.2 digest and verify versioned source or synthetic behavior | Yes to acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Return project and version files from the documented unpaged endpoint. Do not silently truncate or manufacture counts.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: View files on selected project.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | List project files produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"project_id":1}`. Illustrative selected output
fields: `{"items":[],"visibility":{"scope":"requesting_redmine_user","observations":[]}}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | list_project_files |
| Stable operation ID | list_project_files |
| Purpose | List project files; Return project and version files from the documented unpaged endpoint. |
| Local REST route | GET /api/v1/projects/{project_id}/files |
| Upstream mapping | GET /projects/{project_id}/files.json |
| Authentication | Personal `X-Redmine-API-Key`; View files on selected project. |
| MCP exposure | reader; writer may reuse read route; explicit allowlist entry. |
| Annotations | readOnlyHint=true, destructiveHint=false, idempotentHint=true, openWorldHint=true. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive project_id; no pagination or sorting inputs | Positive IDs are strict integers; unknown inputs rejected; omitted update fields never change existing state. Follow specific wording in this row. | GET /projects/{project_id}/files.json |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

items of file attachment metadata plus optional version; visibility; no total. Typed data scoped to requesting Redmine user. Reuse the repository's visibility observations; null and omitted are distinct.
Use existing pagination bounds only where this endpoint documents paging. Never fabricate total-count metadata.
Existing REST/MCP error envelopes remain compatible. A new operation must be
registered exactly once and must not change defaults of another operation.

| Scenario | Public handling |
|---|---|
| Invalid input | Local 422 before upstream call; MCP reports tool error. |
| Missing or invalid key | Existing sanitized 401; no upstream data leaked. |
| Forbidden or absent upstream resource | Existing 403 or visibility-safe 404. |
| Redmine validation failure | Sanitized 422; no raw upstream body in logs/results. |
| Timeout, transport, oversized or malformed response | Existing 504/502-family sanitized errors; no fabricated data. |
| Other upstream status | Existing sanitized upstream error; no automatic retry. |

### Write semantics

N/A - reader. For downloads, Redmine may increment Project/Version download counts; disclose this side effect.

Specification exit check: target-build evidence and predecessor acceptance
are pending. Do not start coding from this draft until the exact 7.0.2 behavior
and its permission contract have been reviewed and the task is marked planned.

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
| AC-001 | REQ-001 | List project files returns the expected mapped result. | TOOL-019-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-019-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-019-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-019-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-019-001 | Gateway/REST with exact valid payload and response; check mapped fields | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-019-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no data leak | Offline; permission variant synthetic |
| TOOL-019-003 | Timeout, 429/5xx, malformed/oversized response | Sanitized failure and truthful outcome | Offline |
| TOOL-019-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-019-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `bash scripts/check.sh` and `git diff --check` during coding | Static checks pass | Not run for this task | Pending |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: none; documentation assignment only.
- Plan deviations: none recorded.
- Quality and automated tests: not run.
- Startup/Inspector checks: not run.
- Documentation: this draft and the master dashboard.
- Final code diff review: pending implementation.
- Remaining blocker: Predecessor tool-016-list-document-categories must be accepted and exact 7.0.2 source/behavior rechecked.

## 9. Completion and handoff

- [ ] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [ ] Documentation reflects implemented behavior.
- [ ] Exact target version and contract reviewed.
- [ ] Final diff reviewed and dashboard synchronized.
- [ ] User accepted this task before the next task starts.

Final status: blocked. Next action: Predecessor tool-016-list-document-categories must be accepted and exact 7.0.2 source/behavior rechecked.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
