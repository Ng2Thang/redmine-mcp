# tool-020-upload-attachment: Upload bounded attachment bytes

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-020-upload-attachment |
| Assigned capability | Upload bounded attachment bytes: Send raw bytes with application/octet-stream. |
| Type / access / destructive effects | Add writer tool / write / Temporary uploaded object |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [prep-008-synthetic-writer-verification](prep-008-synthetic-writer-verification.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Writer-only upload operation implemented; static checks pass, runtime evidence pending. |
| Blocker / next action | User approved coding on 2026-10-02; offline/synthetic checks remain separately authorized work. Continue to tool-021. |

## 2. Discovery and evidence

The client outcome is **upload bounded attachment bytes**. Send raw bytes with application/octet-stream. Upload creates an unattached temporary object; caller must attach token in a later operation. Never log token/content. No automatic retry after uncertain result.
Current catalog has no `upload_attachment`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-02 | General/current documentation | POST /uploads.json?filename={filename} takes raw octet-stream bytes and returns 201 with a token. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| `.local/upgrades/source/redmine-7.0.2.tar.gz`: `attachments_controller.rb`, `upload.api.rsb`, `attachment.rb` | 2026-10-02 | Exact 7.0.2 source | Upload requires octet stream, saves an unattached attachment, returns 201 with `upload.id` and `upload.token`; filename maximum is 255. Runtime permission and state behavior remain unverified. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `upload_attachment` is the sole public owner | No |
| Strict sequence | Prep-008 plan committed as `936f554`; user directed automatic implementation with per-tool review, while fixture execution remains pending | No to coding; yes to acceptance |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Pinned 7.0.2 source checked; synthetic behavior remains unverified | Yes to acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Send raw bytes with application/octet-stream. Upload creates an unattached temporary object; caller must attach token in a later operation. Never log token/content. No automatic retry after uncertain result.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Upstream upload permission under caller key; writer gate.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Upload bounded attachment bytes produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"filename":"example.txt","content_base64":"ZXhhbXBsZQ=="}`.
Illustrative selected output fields: `{"outcome":"accepted","attachment_id":1,"token":"1.digest","upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | upload_attachment |
| Stable operation ID | upload_attachment |
| Purpose | Upload bounded attachment bytes; Send raw bytes with application/octet-stream. |
| Local REST route | POST /api/v1/uploads |
| Upstream mapping | POST /uploads.json?filename={filename} |
| Authentication | Personal `X-Redmine-API-Key`; Upstream upload permission under caller key; writer gate. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, idempotentHint=false, openWorldHint=true; destructiveHint=true for deletion. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | filename basename <=255; strict base64 content; decoded size <= configured limit default5MiB | Positive IDs are strict integers; unknown inputs rejected; omitted update fields never change existing state. Follow specific wording in this row. | POST /uploads.json?filename={filename} |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

`attachment_id` and opaque `token` in an accepted write receipt. The result reports `outcome`,
`upstream_accepted`, `verification` (`matched`, `mismatch`, or `unavailable`), and observed filename
and size when read-back succeeds. Upload specifically expects HTTP 201 with `upload.id` and
`upload.token`. A malformed success response is uncertain. Empty 204 handling belongs to the
shared write transport for later operations.
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

- Exact effect: Send raw bytes with application/octet-stream. Upload creates an unattached temporary object; caller must attach token in a later operation. Never log token/content. No automatic retry after uncertain result.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

Specification exit check: exact 7.0.2 source behavior was checked before coding. The predecessor
fixture plan is prepared; its execution and this tool's runtime permission/state evidence remain
pending under the user's separate testing instruction.

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
| AC-001 | REQ-001 | Upload bounded attachment bytes returns the expected mapped result and resulting Redmine state. | TOOL-020-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-020-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-020-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-020-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-020-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-020-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-020-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-020-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-020-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `bash scripts/check.sh` and `git diff --check` during coding | Static checks pass | Not run for this task | Pending |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: upload model, service and writer port, Redmine gateway, REST route, explicit MCP
  writer allowlist, response annotations, tool reference, and changelog.
- Plan deviations: upload expects 201 JSON in exact 7.0.2 source; 204 is a shared transport case.
  Reader catalog remains unchanged. Prep-008 fixture execution is pending; the user directed
  coding continuation without automatic tests.
- Quality checks (2026-10-02): `.venv/Scripts/ruff.exe check .`,
  `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, and
  `git diff --check` pass. Automated tests: not run.
- Startup/Inspector checks: not run.
- Documentation: this task, dashboard, tool reference, and changelog.
- Final code diff review: code, contract, and documentation inspected; user approved continuation on 2026-10-02.
- Remaining blocker: TOOL-020-001 through TOOL-020-005, runtime permissions, resulting state,
  and cleanup remain unverified. User approved coding continuation to tool-021.

## 9. Completion and handoff

- [ ] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [ ] Documentation reflects implemented behavior.
- [ ] Exact target version and contract reviewed.
- [ ] Final diff reviewed and dashboard synchronized.
- [ ] User accepted this task before the next task starts.

Final status: blocked. Next action: Continue tool-021 coding as directed; separately authorize
offline and marked synthetic checks before acceptance. Coding finished; testing remains pending.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
