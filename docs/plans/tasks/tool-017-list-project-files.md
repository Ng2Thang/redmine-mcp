# tool-017-list-project-files: List project files

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-017-list-project-files |
| Assigned capability | List project files: Return project and version files from the documented unpaged endpoint. |
| Type / access / destructive effects | Add reader tool / read / None |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-016-list-document-categories](tool-016-list-document-categories.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; exact release source reviewed, runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Project file model, service/port/gateway, REST route, read policy, MCP catalog, and docs implemented. |
| Blocker / next action | User approved this implementation and directed continuation to tool-018 on 2026-10-02. TOOL-017-001 through TOOL-017-005 remain separately authorized testing work. |

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
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-02 | 7.0.2 source | `FilesController#index` finds the project, authorizes access, and collects project and version attachments. `app/views/files/index.api.rsb` emits an unpaged `files` array, shared attachment attributes, optional version, digest, and downloads. Runtime behavior remains unverified. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `list_project_files` is the sole public owner | No |
| Strict sequence | User directed implementation of tool-017 through tool-022 after tool-016 on 2026-10-02, with review after each tool | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Pinned 7.0.2 release source inspected locally; actual runtime verification remains pending | No to coding |

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
| Tool arguments | Positive project_id; no pagination or sorting inputs | Local path validation requires project_id >= 1; service also requires a strict positive integer. | GET /projects/{project_id}/files.json |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

`Collection[ProjectFile]` has `items` with positive `id`, nonempty `filename`, nonnegative
`filesize` and `downloads`, `content_type`, `description`, `content_url`, `created_on`, optional
`author` and `version`, and `digest`; `visibility` uses the existing requesting-user scope.
The endpoint is unpaged and supplies no count; an empty `files` array maps to empty `items`.
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

N/A - metadata read only. This tool does not follow `content_url` or increment download counts.

Specification exit check: exact 7.0.2 route, authorization, unpaged response, and fields
were reviewed from the pinned release archive. User directed continuation from tool-016.

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
| AC-001 | REQ-001 | List project files returns the expected mapped result. | TOOL-017-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-017-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-017-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-017-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-017-001 | Gateway/REST with exact valid payload and response; check mapped fields | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-017-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no data leak | Offline; permission variant synthetic |
| TOOL-017-003 | Timeout, 429/5xx, malformed/oversized response | Sanitized failure and truthful outcome | Offline |
| TOOL-017-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-017-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | Ruff lint/format, mypy, and `git diff --check` during coding | Static checks pass | Installed Ruff lint passed; format found 155 files formatted; mypy passed for 79 source files; whitespace check passed on 2026-10-02. | Passed via installed executables |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: added typed `ProjectFile`, project reader port/service/gateway method,
  REST route, explicit read policy/MCP allowlist entries, and public documentation.
- Plan deviations: existing project dependency wiring already constructs the service;
  no bootstrap edit or dependency change was required.
- Quality: installed `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
  --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` passed on 2026-10-02.
  Automated tests were not run under the repository instruction.
- Startup/Inspector checks: not run.
- Documentation: tool reference, changelog, task, and dashboard updated.
- Final code diff review: reviewed the project model/port/service/router/gateway additions,
  read-policy and MCP catalog entries, and related docs. Existing operation signatures and
  defaults remain unchanged.
- Remaining verification: TOOL-017-001 through TOOL-017-005 remain unexecuted. Offline checks
  should cover project and version files, absent version/author, empty and malformed arrays,
  metadata field validation, 401/403/404/422, timeout/oversize, and unchanged MCP catalog.
  Startup and Inspector verification on the marked 7.0.2 fixture remain pending.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed from source.
- [x] Final diff reviewed and dashboard synchronized.
- [x] User approved this implementation and directed continuation to tool-018 on 2026-10-02.

Final status: implementation finished; user review approved; testing pending. Next action:
execute TOOL-017-001 through TOOL-017-005 after separate testing authorization.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_project_files` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H2 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
