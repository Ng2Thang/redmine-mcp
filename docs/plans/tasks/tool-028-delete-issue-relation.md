# tool-028-delete-issue-relation: Delete one issue relation

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-028-delete-issue-relation |
| Assigned capability | Delete one issue relation: Resolve relation's visible source/target before delete, verify absence from issue context, and record unknown outcomes without retry. |
| Type / access / destructive effects | Add writer tool / write / Resource deletion or removal |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-027-create-issue-relation](tool-027-create-issue-relation.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Typed receipt, relation deletion gateway/port/service/REST route, wiring, writer policy/annotations, and docs implemented; static checks passed. |
| Blocker / next action | User approved coding commit `f21140d` and directed continuation; TOOL-028-001 through TOOL-028-005 and marked writer verification require separate authorization. |

## 2. Discovery and evidence

The client outcome is **delete one issue relation**. Resolve relation's visible source/target before delete, verify absence from issue context, and record unknown outcomes without retry.
Current catalog has no `delete_issue_relation`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_IssueRelations) | 2026-10-01 | General/current documentation | DELETE /relations/{relation_id}.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| Local pinned 7.0.2 source archive: relation controller/model and issue controller/API view/model | 2026-10-05 | Exact 7.0.2 | Visible relation endpoints, Manage relations on either project, removal journals, and omitted empty visible relation lists confirmed in source; runtime evidence pending. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `delete_issue_relation` is the sole public owner | No |
| Strict sequence | User approved tool-027 coding commit `a7f89f8` and assigned tools 028-030 | No; testing still pending |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Use pinned 7.0.2 digest and verify versioned source or synthetic behavior | Yes to acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Resolve relation's visible source/target before delete, verify absence from issue context, and record unknown outcomes without retry.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Manage issue relations on either endpoint project,
  visibility of both endpoints, and separately enabled restricted writer.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Delete one issue relation produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"relation_id":3}`. Illustrative selected output
fields: `{"resource_id":3,"upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | delete_issue_relation |
| Stable operation ID | delete_issue_relation |
| Purpose | Delete one issue relation; Resolve relation's visible source/target before delete, verify absence from issue context, and record unknown outcomes without retry. |
| Local REST route | DELETE /api/v1/relations/{relation_id} |
| Upstream mapping | DELETE /relations/{relation_id}.json |
| Authentication | Personal `X-Redmine-API-Key`; both endpoints visible; Manage issue relations on either endpoint project. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, idempotentHint=false, openWorldHint=true; destructiveHint=true for deletion. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive relation_id path parameter | Positive path ID, checked as strict integer by service; no body or context arguments. | DELETE /relations/{relation_id}.json |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

Typed receipt with outcome, upstream acceptance, resource ID, resolved relation,
per-endpoint observations, aggregate observed presence, and matched/mismatch/unavailable
verification. Empty upstream 204 is accepted without JSON parsing. Public REST returns 200
with the receipt. Verification describes visible absence in both successful issue contexts.
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

- Exact effect: Resolve relation's visible source/target before delete, verify absence from issue context, and record unknown outcomes without retry.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

### Frozen coding contract and source evidence (2026-10-05)

Working-tree baseline was clean. Exact 7.0.2 source was read from ignored archive
`.local/upgrades/source/redmine-7.0.2.tar.gz`: `app/controllers/issue_relations_controller.rb`,
`app/models/issue_relation.rb`, `app/controllers/issues_controller.rb`,
`app/views/issues/show.api.rsb`, and `app/models/issue.rb`. No runtime checks were run.

- Positive relation path ID, checked again by the service; no body or context parameters.
- Resolve GET `/relations/{id}.json` into a strict typed visible relation, including both
  endpoint IDs. Preflight both GET `/issues/{endpoint}.json?include=relations` and require
  the relation ID in both contexts before dispatch. Invalid or hidden context stops the write.
- Redmine `deletable?` requires both endpoints visible and Manage issue relations on either
  endpoint's project. Do not impose permission on both projects or require Edit issues.
- One bounded DELETE `/relations/{id}.json`; 204 is accepted without parsing a body.
  Return a receipt with outcome, upstream acceptance, relation resource ID, resolved relation,
  per-endpoint presence observations, aggregate observed presence, and verification.
- Independently re-read both issue contexts. Presence in either is mismatch; absence from
  both is matched; unresolved context with no observed presence is unavailable. Read-back
  errors preserve write acceptance. A 404 on relation or endpoint is never treated as proof
  of deletion. Unknown outcomes have no automatic retry or rollback.
- Requested relations are filtered by other-issue visibility in the pinned controller.
  The pinned issue API omits `relations` when this filtered list is empty; a successful
  correctly identified issue response with that omission means empty visible context.
  Supplied non-list/null entries, invalid or duplicate IDs, and inconsistent endpoint
  membership are malformed. Verification describes visible absence, not stored-row proof.
- Destroy callbacks journal relation removal on both issues. Deleting a scheduling relation
  does not restore dates previously changed by creation. No journal/date state is verified
  by this receipt. Concurrent permission/visibility/state changes have no atomic guarantee.
- Writer-only explicit operation, destructiveHint=true, readOnlyHint=false,
  idempotentHint=false, openWorldHint=true. Existing reader and create contracts preserved.

This resolves the draft's generic update-field wording and permission ambiguity. Specification
exit check passed for coding; testing prerequisites and runtime acceptance remain pending.

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
| AC-001 | REQ-001 | Delete one issue relation returns the expected mapped result and resulting Redmine state. | TOOL-028-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-028-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-028-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-028-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-028-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-028-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-028-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-028-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-028-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, `git diff --check` from Git Bash | Static checks pass | Lint passed; 175 files formatted; no issues in 99 source files; whitespace passed on 2026-10-05 | Pass |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: typed receipt, deleter Protocol/service, relation router registered before MCP,
  visible relation/endpoint preflights, one bounded DELETE, independent context observations,
  writer allowlist, destructive hints, bootstrap wiring, and docs. Tool-027 approval recorded.
- Plan deviations: clarified exact permission on either project and explicit visible absence
  semantics. Source-backed omitted-empty relation handling avoids needing Manage relations
  on both projects for index endpoints. No dependencies, tests, or live data changed.
- Quality: EVID-001 passed. Ruff fixed import ordering and formatted only changed files.
  Tests were not written, modified, or run under this coding-only assignment.
- Startup/Inspector checks: not run.
- Documentation: task, dashboard, tool reference, changelog, and predecessor approval updated.
- Final code diff review: strict service/path IDs, typed same-ID resolution, both visible
  issue contexts before dispatch, positive unique relation IDs and endpoint membership,
  single bounded DELETE, empty 204, independent read-back of each issue, presence dominating
  unavailable observations, no 404-as-deletion inference, no retries or payload logging,
  source permission rule preserved, explicit writer-only route and destructive hints inspected.
  No pre-existing failures were found; prior create/default reader contracts preserved.
- Remaining blocker: separately authorized testing. Exact later
  TOOL-028-001 through TOOL-028-005 work: visible relation and both issue preflights; invalid IDs,
  malformed/missing/duplicate relation entries, endpoint inconsistencies, self relation data,
  hidden or absent contexts and membership stopping dispatch; 204, uncertain timeout/unexpected
  status, either endpoint still present, both absent, omitted empty list, null/malformed list,
  one/both read-back failures including 404, acceptance retained, no retries, reader denial,
  destructive MCP hints, and prior-tool compatibility. Marked prep-008 fixtures must verify
  permissions separately on either project, actual row removal, removal journals, retained
  scheduling dates, visibility changes, Inspector/startup, and task-owned cleanup. No live
  relation was deleted. Static checks alone do not establish acceptance criteria.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed.
- [x] Final diff reviewed and dashboard synchronized.
- [x] User accepted this task before the next task starts.

User approval (2026-10-05): accepted coding commit `f21140d` and requested continuation
through tool-030, retaining review after each tool. Runtime acceptance remains pending.

Final status: implementation finished; testing pending. Next action: separately authorize
TOOL-028-001 through TOOL-028-005 and marked writer
state/permission verification for runtime acceptance. Visible absence does not prove row deletion.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.

## Prep-020 evidence reconciliation, 2026-10-07

Current `delete_issue_relation` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H2/H4 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
