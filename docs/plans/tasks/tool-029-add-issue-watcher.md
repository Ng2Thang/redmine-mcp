# tool-029-add-issue-watcher: Add one watcher

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-029-add-issue-watcher |
| Assigned capability | Add one watcher: Redmine may accept an ineligible user without adding them. |
| Type / access / destructive effects | Add writer tool / write / Redmine state mutation |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-028-delete-issue-relation](tool-028-delete-issue-relation.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Strict watcher request/receipt, gateway, port/service/route, wiring, writer allowlist, and docs implemented; static checks passed. |
| Blocker / next action | User approved coding commit `b930d8c` and directed tool-030; TOOL-029-001 through TOOL-029-005 and marked writer verification require separate authorization. |

## 2. Discovery and evidence

The client outcome is **add one watcher**. Redmine may accept an ineligible user without adding them. Check visible watcher expansion when allowed; do not equate 204 with successful membership.
Current catalog has no `add_issue_watcher`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Issues) | 2026-10-01 | General/current documentation | POST /issues/{issue_id}/watchers.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| Local pinned archive: watcher controller, issue API view, principal/watchable models, and permissions | 2026-10-05 | Exact 7.0.2 | Single watcher body, 204 no-op for ineligible principals, Add watchers separate from View watchers, explicit empty/omitted expansion semantics confirmed in source; runtime evidence pending. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `add_issue_watcher` is the sole public owner | No |
| Strict sequence | User approved coding commit `f21140d` and directed continuation | No; tests still pending |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Use pinned 7.0.2 digest and verify versioned source or synthetic behavior | Yes to acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Redmine may accept an ineligible user without adding them. Check visible watcher expansion when allowed; do not equate 204 with successful membership.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Add watchers on issue.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Add one watcher produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"issue_id":1,"user_id":2}`. Illustrative selected output
fields: `{"upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | add_issue_watcher |
| Stable operation ID | add_issue_watcher |
| Purpose | Add one watcher; Redmine may accept an ineligible user without adding them. |
| Local REST route | POST /api/v1/issues/{issue_id}/watchers |
| Upstream mapping | POST /issues/{issue_id}/watchers.json |
| Authentication | Personal `X-Redmine-API-Key`; Add watchers on issue. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, idempotentHint=false, openWorldHint=true, destructiveHint=false. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive issue_id path and strict positive user_id body; one principal per call | Reject null, bool, string/fractional IDs, arrays, batch fields, and unknown body fields. | POST /issues/{issue_id}/watchers.json with watcher.user_id |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

Typed receipt with outcome, upstream_accepted, issue_id, user_id, observed_present, and
matched/mismatch/unavailable verification. Empty upstream 204 is accepted without JSON parsing;
no new resource ID is fabricated. Public REST returns 200 with the receipt. Only explicit valid
watcher lists prove observed membership or absence; omitted expansion is unavailable.
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

- Exact effect: Redmine may accept an ineligible user without adding them. Check visible watcher expansion when allowed; do not equate 204 with successful membership.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

### Frozen coding contract and exact source evidence (2026-10-05)

Working-tree baseline was clean. Exact source was read from the ignored archive
`.local/upgrades/source/redmine-7.0.2.tar.gz`: `app/controllers/watchers_controller.rb`,
`app/views/issues/show.api.rsb`, `app/models/principal.rb`,
`lib/plugins/acts_as_watchable/lib/acts_as_watchable.rb`, and `lib/redmine/preparation.rb`.
No tests or live calls were executed.

- Required body `user_id`: one strict positive integer. Reject unknown fields, null,
  bool, fractional/string IDs, arrays, and batch fields. Source issue path is positive,
  checked again in the service. The upstream user_id names a principal; target Redmine
  permits eligible User or Group principals. Do not add an administrative user-lookup gate.
- Preflight GET `/issues/{issue_id}.json` for caller visibility and exact issue ID.
  Send one POST `/issues/{issue_id}/watchers.json` with `{"watcher":{"user_id":id}}`.
  Require restricted opt-in writer and Add issue watchers permission; do not locally require
  Edit issues or View issue watchers. Redmine decides principal eligibility and issue visibility.
- Exact controller filters active visible assignable principals and valid watchers, then
  responds 204 even when no matching eligible principal was added. Existing memberships can
  also produce accepted no-ops. Never equate acceptance with a new membership or mutation.
- Return typed receipt: outcome, upstream_accepted, issue_id, user_id, observed_present
  (bool or null), and verification. No new resource ID is invented for empty success.
- Independently GET the same issue with `include=watchers`. An explicit valid watcher list
  containing the ID is matched; an explicit valid list without it is mismatch. An omitted
  watcher list, null/malformed list, invalid/duplicate IDs, wrong issue ID, or read failure
  leaves observation null and verification unavailable. Validate the whole list before matching.
- The API view requires View issue watchers to expose this expansion, including empty lists.
  Omission never means no membership. Read-back failures preserve the preceding 204 acceptance.
  Unknown write outcomes remain uncertain even if later membership is observed.
- No automatic retry, rollback, or atomic concurrency guarantee. Membership may already exist
  or change concurrently; matched verification does not prove this call created it. Native
  watcher membership can affect future notifications; no notification delivery is verified.
- Writer-only explicit operation; readOnlyHint=false, idempotentHint=false,
  destructiveHint=false, openWorldHint=true. Existing read/write contracts unchanged.

This supersedes draft generic update/deletion wording. Specification exit check passed for
coding; acceptance evidence and marked synthetic verification remain pending.

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
| AC-001 | REQ-001 | Add one watcher returns the expected mapped result and resulting Redmine state. | TOOL-029-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-029-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-029-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-029-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-029-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-029-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-029-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-029-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-029-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, `git diff --check` from Git Bash | Static checks pass | Lint passed; 176 files formatted; no type issues in 100 source files; whitespace passed on 2026-10-05 | Pass |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: strict single-principal body and receipt, watcher adder Protocol/service,
  gateway with issue preflight and independent watcher observation, authorized POST route,
  wiring, writer allowlist, and docs. Predecessor approval recorded.
- Plan deviations: replaced generic draft update/deletion hints with scalar watcher creation
  and non-destructive annotations; clarified native eligible User/Group principal behavior,
  separate view permission, and no-op acceptance. No dependency, test, or live data changes.
- Quality: EVID-001 passed. Formatting applied only to changed files. Automated tests were
  not written, modified, or run under this coding-only/user assignment.
- Startup/Inspector checks: not run.
- Documentation: task, dashboard, tool reference, changelog, and predecessor approval updated.
- Final code diff review: router -> service -> port -> gateway, strict IDs and body, exact
  visible issue preflight, bounded single POST, empty 204, same-ID read-back, full-list unique
  positive ID validation before matching, omitted/failed expansion unavailable, no eligibility
  lookup requiring administrator access, no retries or payload logging, explicit writer-only
  operation inspected. Prior operations/default reader remain unchanged; no static failures.
- Remaining blocker: separately authorized verification.
  Later TOOL-029-001 through TOOL-029-005 must cover exact payload/preflight/read-back, active
  users and eligible groups, already-watching and ineligible/missing/inactive principals, invalid
  IDs/body and hidden issue stopping dispatch, Add watchers without View watchers or Edit issues,
  missing Add permission, 204 with present/absent/empty/omitted watcher lists, malformed/null
  lists and invalid/duplicate IDs including a malformed entry after the target, wrong issue ID,
  timeout/unexpected status/read-back failure retaining acceptance, no retries, reader denial,
  MCP schema/hints and previous tools. Marked prep-008 fixtures must verify actual membership,
  eligibility and permission variants, no-op behavior, startup/Inspector and task-owned cleanup
  preserving pre-existing watchers. Notification delivery is outside receipt verification.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed.
- [x] Final diff reviewed and dashboard synchronized.
- [x] User accepted this task before the next task starts.

User approval (2026-10-05): approved coding commit `b930d8c` and requested tool-030.
Runtime acceptance remains pending.

Final status: implementation finished; testing pending. Next action: separately authorize
TOOL-029-001 through TOOL-029-005 and marked writer
membership/permission verification before runtime acceptance. Static checks and upstream 204
do not prove watcher membership.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.

## Prep-020 evidence reconciliation, 2026-10-07

Current `add_issue_watcher` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H2 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
