# tool-019-download-attachment: Download bounded attachment content

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-019-download-attachment |
| Assigned capability | Download bounded attachment content: Use shared metadata and bounded binary transport; reject larger files before and during streaming. |
| Type / access / destructive effects | Add reader tool / read with a Project/Version download-count effect / Counter may increase |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [prep-006-bounded-binary-downloads](prep-006-bounded-binary-downloads.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; exact release source reviewed, runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Bounded metadata-first download, typed base64 response, REST route, policy/catalog entry, annotations, and docs implemented; configured transfer limit defaults to 5 MiB. |
| Blocker / next action | User approved this implementation and directed continuation to prep-007 on 2026-10-02. TOOL-019-001 through TOOL-019-005 remain separately authorized testing work. |

## 2. Discovery and evidence

The client outcome is **download bounded attachment content**. Use shared metadata and bounded binary transport; reject larger files before and during streaming. Project/Version download counts can increase; disclose this effect.
Current catalog has no `download_attachment`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Attachments) | 2026-10-01 | General/current documentation | GET /attachments/{attachment_id}.json then validated content_url; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-02 | 7.0.2 source | Attachment metadata emits a named download URL. `AttachmentsController#download` accepts API auth, checks readability and visibility, increments Project/Version download counters before `send_file`, and may return a cache response. Runtime behavior remains unverified. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `download_attachment` is the sole public owner | No |
| Strict sequence | User approved prep-006 and directed continuation on 2026-10-02 | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Pinned 7.0.2 release source inspected locally; runtime verification remains pending | No to coding |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Use shared metadata and bounded binary transport; reject larger files before and during streaming. Project/Version download counts can increase; disclose this effect.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Container-specific view permission.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Download bounded attachment content produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"attachment_id":1}`. Illustrative selected output
fields: `{"attachment_id":1,"filename":"example.txt","content_base64":"ZXhhbXBsZQ==","filesize":7}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | download_attachment |
| Stable operation ID | download_attachment |
| Purpose | Download bounded attachment content; Use shared metadata and bounded binary transport; reject larger files before and during streaming. |
| Local REST route | GET /api/v1/attachments/{attachment_id}/content |
| Upstream mapping | GET /attachments/{attachment_id}.json then validated content_url |
| Authentication | Personal `X-Redmine-API-Key`; Container-specific view permission. |
| MCP exposure | reader; writer may reuse read route; explicit allowlist entry. |
| Annotations | readOnlyHint=false and idempotentHint=false because Redmine may increment download counts; destructiveHint=false; openWorldHint=true. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive attachment_id | Local path validation requires attachment_id >= 1; service also requires a strict positive integer. | GET /attachments/{attachment_id}.json then validated content_url |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

`AttachmentDownload` contains positive `attachment_id`, nonempty `filename`, optional
`content_type`, `content_base64`, nonnegative `filesize`, and requesting-user `visibility`.
The gateway checks metadata size against the configured limit, 5 MiB by default, before fetching
content. Binary transport checks the header and streamed decoded bytes against the same bound.
A returned byte count must match
metadata `filesize`; otherwise the tool returns sanitized 502. Missing `content_type` preserves
the metadata visibility observation. No pagination or count applies.
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

The binary GET can increment a Project or Version attachment's download count before transfer
completes. A failed or timed-out response does not prove the counter stayed unchanged. The tool
does not automatically retry; it does not create, edit, or delete attachment records.

Specification exit check: exact 7.0.2 metadata, download route, permission, and counter effect
were reviewed from source. User approved the bounded binary transport prerequisite.

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
| AC-001 | REQ-001 | Download bounded attachment content returns the expected mapped result. | TOOL-019-001 | Pending |
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
| EVID-001 | Ruff lint/format, mypy, and `git diff --check` during coding | Static checks pass | Installed Ruff lint passed; format found 161 files formatted; mypy passed for 85 source files; whitespace check passed on 2026-10-02. | Passed via installed executables |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: added typed `AttachmentDownload`, attachment port/service/gateway method,
  REST route, explicit reader policy/MCP catalog entry, counter-aware MCP annotations, and docs.
- Plan deviations: the shared bounded transport was implemented and approved in prep-006;
  no new dependency or bootstrap wiring was required.
- Quality: installed `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
  --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` passed on 2026-10-02.
  Automated tests were not run under the repository instruction.
- Startup/Inspector checks: not run.
- Documentation: tool reference, changelog, task, and dashboard updated.
- Contract correction after user review on 2026-10-02: the master roadmap requires a
  configurable shared binary limit; Settings, Compose, and docs now use a 5 MiB default.
  The user reviewed and approved this follow-up before writer foundation work.
- Final code diff review: reviewed the attachment model/port/service/router/gateway additions,
  policy/catalog entry, counter-aware annotations, and docs. Existing tool signatures and
  defaults remain unchanged.
- Remaining verification: TOOL-019-001 through TOOL-019-005 remain unexecuted. Offline checks
  should cover valid bytes/base64, zero bytes, metadata and stream size bounds, byte-count
  mismatch, unsafe content URLs, redirects, timeout after dispatch, permission errors,
  no retry, MCP annotations, and old catalog compatibility. Synthetic checks must compare
  Project/Version download counts and disclose any uncertain counter outcome.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed from source.
- [x] Final diff reviewed and dashboard synchronized.
- [x] User approved this implementation and directed continuation to prep-007 on 2026-10-02.

Final status: implementation finished; user review approved; testing pending. Next action:
execute TOOL-019-001 through TOOL-019-005 after separate testing authorization.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
