# tool-027-create-issue-relation: Create one issue relation

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-027-create-issue-relation |
| Assigned capability | Create one issue relation: Create exactly one relation. |
| Type / access / destructive effects | Add writer tool / write / Redmine state mutation |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-026-update-issue-note](tool-026-update-issue-note.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Typed request/receipt, relation gateway, port/service/REST route, wiring, writer allowlist, and docs implemented; static checks pass. |
| Blocker / next action | User approved coding commit `a7f89f8` and assigned tools 028-030; TOOL-027-001 through TOOL-027-005 and marked writer verification require separate authorization. |

## 2. Discovery and evidence

The client outcome is **create one issue relation**. Reject all destination lists and invalid
delay/type combinations before upstream calls; verify normalized direction and target.
Current catalog has no `create_issue_relation`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_IssueRelations) | 2026-10-01 | General/current documentation | POST /issues/{issue_id}/relations.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| Local pinned source archive: controller/model/API view and `lib/redmine/preparation.rb` | 2026-10-05 | Exact 7.0.2 | Single integer target, source Manage relations permission, visible destination, 201 relation ID, inverse normalization, scheduling delay/date effects and journals confirmed in source; runtime evidence pending. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `create_issue_relation` is the sole public owner | No |
| Strict sequence | User accepted tool-026 implementation `6aef9de` on 2026-10-05 | No; testing still pending |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Use pinned 7.0.2 digest and verify versioned source or synthetic behavior | Yes to acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Create exactly one relation; reject destination lists and invalid delay/type
  combinations before upstream access; verify normalized direction and target.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Manage issue relations on the source project;
  both issues visible; separately enabled restricted writer.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Create one issue relation produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"issue_id":1,"issue_to_id":2,"relation_type":"blocks"}`. Illustrative selected output
fields: `{"resource_id":3,"upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | create_issue_relation |
| Stable operation ID | create_issue_relation |
| Purpose | Create one issue relation; Create exactly one relation. |
| Local REST route | POST /api/v1/issues/{issue_id}/relations |
| Upstream mapping | POST /issues/{issue_id}/relations.json |
| Authentication | Personal `X-Redmine-API-Key`; Manage issue relations on source project; both issues visible. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, idempotentHint=false, openWorldHint=true, destructiveHint=false. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive source issue_id and scalar issue_to_id; relation_type defaults to relates; delay only for precedes/follows | Strict positive body ID, signed integer delay; reject nulls, unknown fields, lists, strings, and self-relations. | POST /issues/{issue_id}/relations.json with one relation object |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

Write receipt with new relation ID and independent read-back. Verification is matched, mismatch,
or unavailable. The receipt includes `upstream_accepted`, `verification`, `field_verification`,
optional `resource_id`, and optional `observed_relation`. Upstream success is 201 with a relation
object; empty or malformed success preserves acceptance but leaves outcome uncertain without
a trustworthy positive ID. Public REST returns the typed receipt with status 200.
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

- Exact effect: Create exactly one relation; native journals and scheduling cascades can occur.
  Reject destination lists and invalid delay/type combinations before upstream access; verify
  normalized direction and target separately from those additional effects.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

### Frozen contract and source review (2026-10-05)

The working tree was clean. User approved predecessor commit `6aef9de` and explicitly
assigned tool-027. Exact source was read from the ignored pinned archive
`.local/upgrades/source/redmine-7.0.2.tar.gz`: `app/controllers/issue_relations_controller.rb`,
`app/models/issue_relation.rb`, `app/models/issue.rb`,
`app/views/issue_relations/show.api.rsb`, and `lib/redmine/preparation.rb`.
These establish the following coding contract; runtime acceptance remains pending.

- Input: strict positive scalar `issue_to_id`; source path ID positive and checked by the
  service; default `relation_type=relates`. Allowed types: `relates`, `duplicates`,
  `duplicated`, `blocks`, `blocked`, `precedes`, `follows`, `copied_to`, `copied_from`.
  Reject nulls, unknown fields, destination arrays/comma-separated strings, and self-relations.
  Optional `delay` is a strict signed integer in days, only for precedes/follows; supplied
  null or a delay for other types is rejected. Negative delays are permitted by target source.
- Preflight both visible issue IDs with the caller's key. The create action requires Manage
  issue relations on the source project; no additional destination Manage relations or Edit
  issues permission is imposed locally. Cross-project settings, duplicate pairs, ancestors,
  and circular dependencies remain Redmine validation rules (sanitized 422).
- Send exactly one POST with `{"relation": {"issue_to_id": ..., "relation_type": ...}}`,
  adding delay only if supplied. The upstream controller supports batch input but this tool
  deliberately rejects it. Success is 201 with a relation object, not empty 204.
- Result: accepted/uncertain outcome, `upstream_accepted`, optional positive `resource_id`,
  aggregate and per-field verification, and optional typed `observed_relation` with visibility.
  A 201 with malformed/missing relation ID is uncertain with upstream acceptance preserved;
  no ID is guessed from an existing pair. With a valid returned ID, independently GET
  `/relations/{id}.json` and compare stored issue_id, issue_to_id, relation_type, and delay.
  Read-back failure or missing fields leaves verification unavailable; a differing field
  is mismatch. Status 201 alone never proves the requested direction or target.
- Normalize expected inverse types: duplicated -> duplicates, blocked -> blocks,
  follows -> precedes, copied_from -> copied_to, each swapping endpoints. Relates sorts
  endpoints by ID. Scheduling types default delay to zero; all other stored delays are null.
- One relation is created, but native callbacks also journal both issues. Scheduling relations
  can reschedule the successor and downstream dates. This receipt verifies the relation only,
  not those additional effects. No retry, rollback, or concurrency guarantee is promised.
- Writer-only allowlist and restricted opt-in deployment; readOnlyHint=false,
  idempotentHint=false, destructiveHint=false, openWorldHint=true. Other catalogs unchanged.

This section supersedes generic draft wording about destination lists, update omissions,
204 success, and deletion hints. Specification exit check passed for coding; required
offline and marked synthetic evidence remains pending.

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
| AC-001 | REQ-001 | Create one issue relation returns the expected mapped result and resulting Redmine state. | TOOL-027-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-027-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-027-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-027-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-027-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-027-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-027-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-027-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-027-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, `git diff --check` from Git Bash | Static checks pass | Lint passed; 174 files formatted; no type issues in 98 source files; whitespace passed on 2026-10-05 | Pass |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: strict scalar destination/type/delay models and observation receipt, relation
  creator Protocol, self-relation service validation, single-create gateway, authorized POST
  route, dependency wiring, explicit writer operation, and public docs. Predecessor approval
  recorded. Reader catalog and prior contracts remain unchanged.
- Plan deviations: replaced generic draft batch/204/deletion wording with exact 201 scalar
  create behavior. Expected read-back accounts for inverse and symmetric normalization and
  default delay; signed delays retained because target source permits them. Disclosed native
  journals and scheduling cascades. No dependencies, tests, or live data changed.
- Quality: EVID-001 passed. Initial mypy caught missing explicit query arguments; corrected
  both GET calls and reran all static checks successfully. Formatting only changed files.
  Automated tests were not written, modified, or run under this coding assignment.
- Startup/Inspector checks: not run.
- Documentation: task, dashboard, tool reference, changelog, and tool-026 approval updated.
- Final code diff review: router -> service -> port -> gateway, positive IDs, validation before
  upstream access, both visibility preflights, single bounded POST, sanitized Redmine errors,
  201 acceptance separated from uncertainty and read-back, strict returned positive ID,
  independent same-ID observation, no fabricated matches for absent fields, normalized
  expected direction/type/delay, no retry or payload logging, opt-in writer policy inspected.
- Remaining blocker: separately authorized TOOL-027-001 through TOOL-027-005.
  Later offline scenarios must cover all nine types, inverse swaps, sorted relates, omitted,
  zero and negative scheduling delay, invalid/null/unknown/list/comma-separated/bool/float IDs,
  self-relations, invalid delay combinations, hidden endpoints and permission rejection before
  mutation, duplicates/circular/ancestor/cross-project 422, 201 malformed/missing/invalid IDs,
  unexpected/empty status, timeout, malformed or mismatched read-back, missing delay, rejected
  read-back, catalog schema/hints, reader denial, and existing-tool compatibility. Marked
  prep-008 writer fixtures must verify source-only Manage relations permission, destination
  visibility, actual normalized relation state, journal records, successor/downstream date
  changes, and task-owned cleanup. Cleanup must account for dates/journals; deleting a relation
  does not promise rollback. No live relation was created.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed.
- [x] Final diff reviewed and dashboard synchronized.
- [x] User accepted this task before the next task starts.

User approval (2026-10-05): accepted coding commit `a7f89f8` and assigned tools 028-030,
with review after each tool. The prior range ended at tool-027; this new instruction authorizes
tool-028 coding. It does not establish runtime acceptance.

Final status: implementation finished; testing pending. Next action: separately authorize
TOOL-027-001 through TOOL-027-005 and marked writer fixture
verification before runtime acceptance. Static checks do not prove relation state,
permissions, journals, or date effects.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.

## Prep-020 evidence reconciliation, 2026-10-07

Current `create_issue_relation` functional evidence is mapped in the
[32-operation ledger](../../testing/evidence/current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H2 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
