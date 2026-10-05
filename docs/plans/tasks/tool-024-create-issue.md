# tool-024-create-issue: Create or natively copy an issue

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-024-create-issue |
| Assigned capability | Create or natively copy an issue: Use native copy_from, not a client-side clone. |
| Type / access / destructive effects | Add writer tool / write / Redmine state mutation |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-023-delete-attachment](tool-023-delete-attachment.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Writer-only issue creation/native copy, complete typed inputs, receipt/read-back, REST route, wiring, policy, and docs implemented; static checks pass. |
| Blocker / next action | User review before tool-025; TOOL-024-001 through TOOL-024-005 and writer fixture verification require separate authorization. |

## 2. Discovery and evidence

The client outcome is **create or natively copy an issue**. Use native copy_from, not a client-side clone. No subtree copy in v1. Source must be visible; destination Add permission. Native attachment/link/watcher effects depend on Redmine settings and must be verified on pinned 7.0.2.
Current catalog has no `create_issue`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://github.com/redmine/redmine/blob/master/app/controllers/issues_controller.rb) | 2026-10-01 | General/current documentation | POST /issues.json; optional copy_from query; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz), inspected locally | 2026-10-05 | Exact 7.0.2 | `IssuesController#create` returns 201 with an issue; `build_new_issue_from_params` uses visible `copy_from`, source `copy_issues`, destination `add_issues`, and native attachment/link/watcher policies. `ApplicationController#find_optional_project` reads top-level project_id. `Issue#safe_attributes` applies workflow/field permissions; fields may be ignored. Runtime effects remain pending. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `create_issue` is the sole public owner | No |
| Strict sequence | User approved tool-023 commit `c6ef155` and directed continuation on 2026-10-05 | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Exact 7.0.2 native creation/copy source reviewed; synthetic acceptance pending | Yes to runtime acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Use native copy_from, not a client-side clone. No subtree copy in v1. Source must be visible; destination Add permission. Native attachment/link/watcher effects depend on Redmine settings and must be verified on pinned 7.0.2.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Add issues; Copy issues on source when copy_from; additional field permissions.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Create or natively copy an issue produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"project_id":1,"subject":"New issue"}`. Illustrative selected output
fields: `{"resource_id":1,"upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | create_issue |
| Stable operation ID | create_issue |
| Purpose | Create or natively copy an issue; Use native copy_from, not a client-side clone. |
| Local REST route | POST /api/v1/issues |
| Upstream mapping | POST /issues.json; optional copy_from query |
| Authentication | Personal `X-Redmine-API-Key`; Add issues; Copy issues on source when copy_from; additional field permissions. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, destructiveHint=false, idempotentHint=false, openWorldHint=true. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive project_id; subject required unless copy_from positive; optional tracker/status/priority/category/version/assignee,description,dates,done_ratio,estimated_hours,custom_fields,parent_issue_id,is_private,uploads,watcher_user_ids | Positive IDs are strict integers; unknown inputs rejected; omitted update fields never change existing state. Follow specific wording in this row. | POST /issues.json; optional copy_from query |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

Contract frozen on 2026-10-05: body model rejects unknown fields. `project_id` and all non-null
IDs are strict positive integers. `subject` is nonblank and at most 255 characters, required
without `copy_from`. Optional tracker/status/priority IDs, `is_private`, `done_ratio`, and
array fields reject explicit null. Nullable assignee/category/version/parent IDs, description,
dates, and hours accept null to clear inherited values on a copy. `assigned_to_id` also accepts
`me`. Dates use ISO YYYY-MM-DD; hours are finite nonnegative JSON numbers; done_ratio is a
strict integer from 0 through 100. Custom fields contain unique positive IDs and string,
string-list, or null values. Watcher IDs and upload tokens are unique; upload filenames are
basenames up to 255 characters. Tokens follow Redmine's ID.digest form. Uploads accept optional
description and content_type. Duplicate IDs/tokens and inverted supplied date ranges fail locally.

Always send destination `project_id` as a top-level query parameter and in `issue.project_id`;
send `copy_from` only as a top-level query parameter. Preflight source visibility using a read,
then delegate copying to Redmine without client cloning, copy flags, or `copy_subtasks`.
Omitted fields are omitted from the JSON body. Native link and attachment settings apply;
watcher copying depends on destination permission. Do not promise source status preservation.

Result: `outcome` accepted/uncertain, `upstream_accepted` true for confirmed 201 or null,
nullable `resource_id`, `verification` matched/mismatch/unavailable, per-field
`field_verification`, and optional `observed_issue`. A malformed/missing positive ID leaves
outcome uncertain and cannot trigger an ID-based read-back; a confirmed 201 remains accepted
by upstream even if its body is malformed. With a valid ID, GET the created issue with
attachments/watchers only when requested, compare project and supplied fields, and preserve
write acceptance if read-back fails. Missing/hidden fields are unavailable, never assumed
matches from model defaults. Exact 7.0.2 omits unset optional references; their absence is
compared as null. Any observed mismatch wins; otherwise unavailable fields keep
overall verification unavailable. Upload tokens are not echoed; compare upload IDs and supplied
metadata (description is stripped by native attachment handling). Supplied watcher IDs are
compared as an unordered set; omitted watcher IDs leave native copying policies in control.
No implicit retry or lookup
by subject after an uncertain create; creation can already have succeeded.

Creation expects HTTP 201 with an issue ID; HTTP 204 is not the creation success contract.
Write acceptance and supplied-field read-back remain separate. No source subtree is copied.
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

- Exact effect: Use native copy_from, not a client-side clone. No subtree copy in v1. Source must be visible; destination Add permission. Native attachment/link/watcher effects depend on Redmine settings and must be verified on pinned 7.0.2.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

Specification exit check: exact 7.0.2 destination selection, native copy, permissions, 201
response, and side effects reviewed; tool-023 coding approved. Runtime acceptance pending.

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
| AC-001 | REQ-001 | Create or natively copy an issue returns the expected mapped result and resulting Redmine state. | TOOL-024-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-024-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-024-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-024-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-024-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-024-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-024-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-024-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-024-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` | Static checks pass | Passed on 2026-10-05; 171 formatted files and 95 source files checked. Tests/startup/live calls not run. | Passed |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: typed full creation inputs and receipt, issue creator Protocol/service,
  native-copy gateway, authorized REST POST route, dependency wiring, explicit writer allowlist,
  bounded writer query support, tool reference, changelog, and dashboard. Tool-023 approval recorded.
- Plan deviations: upstream creation uses 201 JSON, not 204. Destination project_id is sent both
  as query and nested body to select permissions before native copy. No copy flags or subtree
  copy are forwarded. Workflow may ignore fields; per-field verification makes observed
  mismatches/unavailable fields explicit instead of claiming acceptance means every field applied.
- Quality: installed Ruff lint/format, mypy, and whitespace passed (EVID-001). Formatting applied
  only to new task files. Automated tests not run under the coding-only/user instructions.
- Startup/Inspector checks: not run.
- Documentation: task, dashboard, tool reference, changelog, and predecessor approval updated.
- Final code diff review: router -> service -> creator port -> Redmine gateway; source preflight,
  destination query, omit/clear mapping, bounded single dispatch, 201 receipt, malformed ID,
  independently verified scalar/reference/custom/upload/watcher fields, no token echo or logging,
  explicit writer-only exposure, and existing reader/write defaults inspected. No dependencies,
  test files, live data, or unrelated source changed.
- Remaining blocker: user review before tool-025. TOOL-024-001 through TOOL-024-005 require
  later offline checks for normal creation/copy, all inputs and null/omission cases, wrong/hidden
  source, destination and field permissions, exact query/body/headers, duplicate input arrays,
  201 and invalid success bodies, timeout uncertainty, read-back mismatches/hidden/failed fields,
  upload IDs and normalized descriptions, watcher/custom-field comparisons, reader denial,
  MCP schema/annotations, and existing upload/write transport compatibility. Opt-in prep-008
  fixtures on marked 7.0.2 must verify native copy attachment/link/watcher settings, no subtree,
  actual issue state, permissions, and task-owned cleanup. Nothing was created in live Redmine.

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
commit before tool-025. Separately authorize TOOL-024-001 through TOOL-024-005 and marked writer
fixture verification before runtime acceptance. Static checks do not prove native copy effects.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
