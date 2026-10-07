# tool-018-get-attachment: Read attachment metadata

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-018-get-attachment |
| Assigned capability | Read attachment metadata: Redmine controls visibility for Project/Version, Document, and Issue containers. |
| Type / access / destructive effects | Add reader tool / read / None |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-017-list-project-files](tool-017-list-project-files.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; exact release source reviewed, runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Attachment model, service/port/gateway, REST route, dependency wiring, MCP registration, and docs implemented. |
| Blocker / next action | User approved this implementation and directed continuation to prep-006 on 2026-10-02. TOOL-018-001 through TOOL-018-005 remain separately authorized testing work. |

## 2. Discovery and evidence

The client outcome is **read attachment metadata**. Redmine controls visibility for Project/Version, Document, and Issue containers. This tool returns metadata only, not file content.
Current catalog has no `get_attachment`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Attachments) | 2026-10-01 | General/current documentation | GET /attachments/{attachment_id}.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-02 | 7.0.2 source | `AttachmentsController#show` accepts API auth and uses `file_readable` and `read_authorize`. The first returns 404 if the stored file cannot be read; `Attachment#visible?` delegates to the container's attachment visibility. `show.api.rsb` wraps `render_api_attachment`, whose helper emits metadata and a content URL without reading file bytes. Runtime behavior remains unverified. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `get_attachment` is the sole public owner | No |
| Strict sequence | User approved tool-017 and directed continuation on 2026-10-02 | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Pinned 7.0.2 release source inspected locally; runtime verification remains pending | No to coding |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Redmine controls visibility for Project/Version, Document, and Issue containers. This tool returns metadata only, not file content.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Container-specific view permission.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Read attachment metadata produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"attachment_id":1}`. Illustrative selected output
fields: `{"id":1,"filename":"example.txt","filesize":7,"content_url":"http://redmine.local/attachments/download/1/example.txt"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | get_attachment |
| Stable operation ID | get_attachment |
| Purpose | Read attachment metadata; Redmine controls visibility for Project/Version, Document, and Issue containers. |
| Local REST route | GET /api/v1/attachments/{attachment_id} |
| Upstream mapping | GET /attachments/{attachment_id}.json |
| Authentication | Personal `X-Redmine-API-Key`; Container-specific view permission. |
| MCP exposure | reader; writer may reuse read route; explicit allowlist entry. |
| Annotations | readOnlyHint=true, destructiveHint=false, idempotentHint=true, openWorldHint=true. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive attachment_id | Local path validation requires attachment_id >= 1; service also requires a strict positive integer. | GET /attachments/{attachment_id}.json |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

`AttachmentDetail` contains positive `id`, nonempty `filename`, nonnegative `filesize`,
optional `content_type`, `description`, and `author`, required `content_url` and `created_on`,
plus requesting-user `visibility`. Missing optional fields produce `not_returned` observations;
explicit nulls remain null without absence observations. No pagination or count applies.
Existing REST/MCP error envelopes remain compatible. A new operation must be
registered exactly once and must not change defaults of another operation.

| Scenario | Public handling |
|---|---|
| Invalid input | Local 422 before upstream call; MCP reports tool error. |
| Missing or invalid key | Existing sanitized 401; no upstream data leaked. |
| Forbidden, absent, or unreadable upstream attachment | Existing 403 or visibility-safe 404. |
| Redmine validation failure | Sanitized 422; no raw upstream body in logs/results. |
| Timeout, transport, oversized or malformed response | Existing 504/502-family sanitized errors; no fabricated data. |
| Other upstream status | Existing sanitized upstream error; no automatic retry. |

### Write semantics

N/A - metadata read only. This tool does not download content or increment download counts.

Specification exit check: exact 7.0.2 API route, container authorization, and response mapping
were reviewed from the pinned release archive. The user approved tool-017 and directed continuation.

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
| AC-001 | REQ-001 | Read attachment metadata returns the expected mapped result. | TOOL-018-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-018-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-018-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-018-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-018-001 | Gateway/REST with exact valid payload and response; check mapped fields | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-018-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no data leak | Offline; permission variant synthetic |
| TOOL-018-003 | Timeout, 429/5xx, malformed/oversized response | Sanitized failure and truthful outcome | Offline |
| TOOL-018-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-018-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | Ruff lint/format, mypy, and `git diff --check` during coding | Static checks pass | Installed Ruff lint passed; format found 161 files formatted; mypy passed for 85 source files; whitespace check passed on 2026-10-02. | Passed via installed executables |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: added attachment metadata model, reader port/service/gateway, REST route,
  dependency wiring, read-policy and MCP catalog entries, and public documentation.
- Plan deviations: added a dedicated attachment feature to keep this tool's model and gateway
  available for subsequent attachment operations. No dependency change was required.
- Quality: installed `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
  --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` passed on 2026-10-02.
  Automated tests were not run under the repository instruction.
- Startup/Inspector checks: not run.
- Documentation: tool reference, changelog, task, and dashboard updated.
- Final code diff review: reviewed the new attachment model/port/service/router/gateway,
  dependency wiring, read-policy and MCP catalog entries, and English docs. Existing
  operation names, inputs, and defaults remain unchanged.
- Remaining verification: TOOL-018-001 through TOOL-018-005 remain unexecuted. Offline checks
  should cover complete and missing optional metadata, ID mismatch and malformed wrappers,
  401/403/404/422, timeout/oversize, catalog compatibility, and MCP schema. Synthetic
  permission checks on the pinned 7.0.2 fixture remain pending.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed from source.
- [x] Final diff reviewed and dashboard synchronized.
- [x] User approved this implementation and directed continuation to prep-006 on 2026-10-02.

Final status: implementation finished; user review approved; testing pending. Next action:
execute TOOL-018-001 through TOOL-018-005 after separate testing authorization.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.

## Prep-020 evidence reconciliation, 2026-10-07

Current `get_attachment` functional evidence is mapped in the
[32-operation ledger](../../testing/evidence/current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H2 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
