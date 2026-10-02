# tool-015-get-issue-write-context: Expose issue write and file context

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-015-get-issue-write-context |
| Assigned capability | Expose issue write and file context: Only expose fields Redmine returns. |
| Type / access / destructive effects | Extend existing tool / read / None |
| Status | blocked - implementation finished; verification deferred |
| Dependencies | [tool-014-list-issues-associations](tool-014-list-issues-associations.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm; exact release source reviewed; runtime verification waived |
| Last updated | 2026-10-02, Codex |
| Progress summary | Added estimates, attachment URL, and journal edit metadata; existing include defaults preserved. |
| Blocker / next action | Coding and static checks finished; verification remains deferred under the user's instructions. |

## 2. Discovery and evidence

The client outcome is **expose issue write and file context**. Only expose fields Redmine returns. Distinguish absent/null estimates; never synthesize an editable-field guarantee from a visible value. Preserve existing include defaults and observations.
The existing `get_issue` operation is extended, so its name, defaults, and existing output behavior remain compatible.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Issues) | 2026-10-01 | General/current documentation | GET /issues/{issue_id}.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | Pinned target accepted with a runtime waiver. |
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-02 | 7.0.2 release source | `app/views/issues/show.api.rsb` emits both estimates and journal updated_on/updated_by. `app/helpers/attachments_helper.rb` emits content_url. No runtime call was made. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `get_issue` is the sole public owner | No |
| Strict sequence | User directed continuation after tool-014 on 2026-10-02; unexecuted verification retained | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Exact 7.0.2 release source reviewed; actual runtime verification waived | No to coding |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Only expose fields Redmine returns. Distinguish absent/null estimates; never synthesize an editable-field guarantee from a visible value. Preserve existing include defaults and observations.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: View issues and expansion-specific visibility.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Expose issue write and file context produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"issue_id":1}`. Illustrative selected output
fields: `{"id":1,"estimated_hours":null,"total_estimated_hours":null,"attachments":[]}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | get_issue |
| Stable operation ID | get_issue |
| Purpose | Expose issue write and file context; Only expose fields Redmine returns. |
| Local REST route | GET /api/v1/issues/{issue_id} |
| Upstream mapping | GET /issues/{issue_id}.json |
| Authentication | Personal `X-Redmine-API-Key`; View issues and expansion-specific visibility. |
| MCP exposure | reader; writer may reuse read route; explicit allowlist entry. |
| Annotations | readOnlyHint=true, destructiveHint=false, idempotentHint=true, openWorldHint=true. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Existing positive issue_id and include CSV; preserve default journals,attachments | Positive IDs are strict integers; unknown inputs rejected; omitted update fields never change existing state. Follow specific wording in this row. | GET /issues/{issue_id}.json |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

Existing IssueDetail plus nullable estimated_hours,total_estimated_hours, attachment content_url, journal updated_on/updated_by where returned. Typed data scoped to requesting Redmine user. Reuse the repository's visibility observations; null and omitted are distinct.
Estimates accept finite nonnegative JSON numbers, using the existing hour validator.
Absent estimates produce `not_returned` observations at `/estimated_hours` and
`/total_estimated_hours`; explicit nulls produce no absence observation. Missing optional
attachment and journal metadata map to null. Content URLs are returned as strings without
fetching them. Values do not establish edit permissions. Shared attachment and journal models
also expose these fields when used in list expansions; no new include defaults are introduced.
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

Specification exit check: predecessor continuation was accepted and exact release source
supports all added fields. No writer permissions or editability guarantees are inferred.

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
| AC-001 | REQ-001 | Expose issue write and file context returns the expected mapped result. | TOOL-015-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-015-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-015-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-015-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.
The user instructed continuation without actual runtime verification. No tests, startup,
Inspector, or live calls were executed for this task.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-015-001 | Gateway/REST with exact valid payload and response; check mapped fields | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-015-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no data leak | Offline; permission variant synthetic |
| TOOL-015-003 | Timeout, 429/5xx, malformed/oversized response | Sanitized failure and truthful outcome | Offline |
| TOOL-015-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-015-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | Ruff lint/format, mypy, and `git diff --check` during coding | Static checks pass | Ruff check/format passed for the repository; mypy passed for 79 source files; whitespace check passed on 2026-10-02 | Passed |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure | Required runtime cases pass | Not run under user runtime waiver | Waived, not passed |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: Extended IssueDetail estimates, Attachment.content_url, and Journal edit
  metadata; added estimate visibility observations to the existing gateway mapping.
- Plan deviations: no service, port, bootstrap, or catalog edits needed because the existing
  typed get_issue route owns this response. Shared nested models also serve list expansions.
- Quality: repository Ruff lint/format, mypy `src`, and `git diff --check` passed on
  2026-10-02 using installed tools. Automated tests not run.
- Startup/Inspector checks: not run under the user's runtime waiver.
- Documentation: tool reference, changelog, this task, and dashboard updated.
- Final code diff review: typed response additions and gateway observation changes reviewed;
  dashboard synchronized. Existing request inputs and default expansions are preserved.
- Remaining verification: TOOL-015-001 through TOOL-015-005 remain unexecuted. Future offline
  work should cover absent/null/zero estimates, rejected numeric strings and invalid numbers,
  populated/missing nested metadata, unchanged includes/defaults, errors, and MCP schemas.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed from source.
- [x] Final diff reviewed and dashboard synchronized.
- [ ] User accepted this task before the next task starts.

Final status: implementation finished; static checks passed. Runtime and automated
verification remain unexecuted and are not claimed as passing.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
