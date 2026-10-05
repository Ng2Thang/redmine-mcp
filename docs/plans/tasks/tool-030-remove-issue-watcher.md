# tool-030-remove-issue-watcher: Remove one watcher

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-030-remove-issue-watcher |
| Assigned capability | Remove one watcher: Check visible watcher expansion when allowed; 204 may be a no-op. |
| Type / access / destructive effects | Add writer tool / write / Resource deletion or removal |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-029-add-issue-watcher](tool-029-add-issue-watcher.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Watcher-remover Protocol/service/gateway/route, shared typed receipt, wiring, writer policy/annotations, and docs implemented; static checks passed. |
| Blocker / next action | User review; TOOL-030-001 through TOOL-030-005 and marked writer verification require separate authorization. |

## 2. Discovery and evidence

The client outcome is **remove one watcher**. Check visible watcher expansion when allowed; 204 may be a no-op. Do not retry after uncertain outcome.
Current catalog has no `remove_issue_watcher`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Issues) | 2026-10-01 | General/current documentation | DELETE /issues/{issue_id}/watchers/{user_id}.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Documents REST excluded from 7.0.2 | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| Local pinned archive: watcher controller/routes, watchable implementation, issue API view, and permissions | 2026-10-05 | Exact 7.0.2 | Delete watchers permission, Principal.find, direct membership removal, 204 no-op, and separately visible watcher expansion confirmed in source; runtime evidence pending. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `remove_issue_watcher` is the sole public owner | No |
| Strict sequence | User approved coding commit `b930d8c` and requested tool-030 | No; testing still pending |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Use pinned 7.0.2 digest and verify versioned source or synthetic behavior | Yes to acceptance |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Check visible watcher expansion when allowed; 204 may be a no-op. Do not retry after uncertain outcome.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Delete watchers on issue.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Remove one watcher produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{"issue_id":1,"user_id":2}`. Illustrative selected output
fields: `{"upstream_accepted":true,"verification":"matched"}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | remove_issue_watcher |
| Stable operation ID | remove_issue_watcher |
| Purpose | Remove one watcher; Check visible watcher expansion when allowed; 204 may be a no-op. |
| Local REST route | DELETE /api/v1/issues/{issue_id}/watchers/{user_id} |
| Upstream mapping | DELETE /issues/{issue_id}/watchers/{user_id}.json |
| Authentication | Personal `X-Redmine-API-Key`; Delete watchers on issue. |
| MCP exposure | writer only; explicit allowlist entry. |
| Annotations | readOnlyHint=false, idempotentHint=false, openWorldHint=true; destructiveHint=true for deletion. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | Positive issue_id,user_id path parameters | Positive path IDs checked as strict integers by service; no body or batch arguments. | DELETE /issues/{issue_id}/watchers/{user_id}.json without body |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

IssueWatcherResult receipt with outcome, upstream_accepted, issue_id, user_id, observed_present,
and matched/mismatch/unavailable verification. Empty upstream 204 is accepted without JSON
parsing. Public REST returns 200 with the receipt; no resource ID is fabricated. Only explicit
valid watcher lists verify membership; omission is unavailable rather than empty.
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

- Exact effect: Check visible watcher expansion when allowed; 204 may be a no-op. Do not retry after uncertain outcome.
- No automatic retries. A timeout after dispatch produces an unknown outcome requiring a separate read-back before any repeat.
- Success and read-back are separate fields. A failed read-back cannot erase a preceding accepted write.
- Concurrent updates have no promised compare-and-swap guarantee. Do not infer atomicity from timestamps.
- Synthetic verification requires `prep-008`, an isolated marker, task-owned fixtures, and cleanup of only those fixtures.

### Frozen coding contract and exact source evidence (2026-10-05)

Working-tree baseline was clean. Exact source was read from the ignored archive
`.local/upgrades/source/redmine-7.0.2.tar.gz`: `app/controllers/watchers_controller.rb`,
`config/routes.rb`, `lib/plugins/acts_as_watchable/lib/acts_as_watchable.rb`,
`app/views/issues/show.api.rsb`, and `lib/redmine/preparation.rb`. No runtime checks were run.

- Positive issue_id and user_id path parameters; service checks both as strict positive IDs.
  No body or batch arguments. user_id identifies one principal; native User/Group behavior
  is retained without an administrative principal lookup in this application.
- Preflight GET `/issues/{issue_id}.json` for visible same-ID issue. Do not require visible
  watcher membership or View issue watchers before dispatch; those are separate permissions.
- One bounded DELETE `/issues/{issue_id}/watchers/{user_id}.json`, with no body.
  Requires restricted opt-in writer and Delete issue watchers; no extra Edit issues,
  Add watchers, or View watchers prerequisite is imposed locally.
- The controller resolves Principal.find (missing principal is sanitized 404), removes the
  direct User/Group watcher entries, and returns empty 204 even if none existed. This receipt
  never asserts a previously present membership was changed solely from status 204.
- Reuse IssueWatcherResult: outcome, upstream_accepted, issue_id, user_id, observed_present,
  and verification. Public REST returns 200 with this receipt; no new resource ID invented.
- Independently GET same issue with include=watchers and validate the whole list's unique
  strict positive IDs. Explicit list without the principal is matched; presence is mismatch.
  Omitted, malformed/null, invalid/duplicate-ID list, wrong issue ID, or failed read-back
  yields null observation and unavailable verification. A read-back 404 never proves removal.
- The API exposes watchers only with View issue watchers, including explicit empty lists.
  Missing expansion does not mean empty. Failed verification preserves 204 acceptance;
  uncertain write outcome remains uncertain even when absence is subsequently observed.
- Removing a direct principal entry does not prove all effective watching or notifications
  stopped: a user can still watch through groups or other notification preferences. Native
  remove_watcher deletes membership rows without issue relation/note journal callbacks.
- No automatic retries, rollback, or atomic concurrency guarantee. Reader and add-watcher
  contracts unchanged. Explicit writer operation with destructiveHint=true,
  readOnlyHint=false, idempotentHint=false, openWorldHint=true.

This replaces draft generic update-field wording and resolves permission/no-op/visibility
semantics. Specification exit check passed for coding; required acceptance evidence pending.

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
| AC-001 | REQ-001 | Remove one watcher returns the expected mapped result and resulting Redmine state. | TOOL-030-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-030-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-030-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-030-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-030-001 | Gateway/REST with exact valid payload and response; inspect changed synthetic state | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-030-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no unintended write | Offline; permission variant synthetic |
| TOOL-030-003 | Timeout, 429/5xx, malformed/oversized response, duplicate and uncertain call | Sanitized failure and truthful outcome | Offline |
| TOOL-030-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-030-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions, resulting state and cleanup | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, `.venv/Scripts/mypy.exe src`, `git diff --check` from Git Bash | Static checks pass | Lint passed; 176 files formatted; no type issues in 100 source files; whitespace passed on 2026-10-05 | Pass |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: watcher-remover Protocol, strict service IDs, bounded single-delete gateway,
  authorized DELETE route, shared receipt and full-list validation reuse, wiring, explicit
  writer operation, destructive hints, and docs. Tool-029 approval recorded.
- Plan deviations: clarified direct principal removal, no-op 204, missing principal 404,
  separate View watcher permission, and no inference about group-derived watching or
  notification delivery. No dependencies, tests, or live data changed.
- Quality: EVID-001 passed; formatting only changed files. Automated tests were not written,
  modified, or run under the coding-only/user assignment.
- Startup/Inspector checks: not run.
- Documentation: task, dashboard, tool reference, changelog, and predecessor approval updated.
- Final code diff review: router -> service -> remover port -> gateway, positive IDs,
  same-ID visible issue preflight, one bounded bodyless DELETE, empty 204, independent same-ID
  watcher read-back, strict positive unique IDs across the whole list, presence/absence reversed
  correctly from add-watcher verification, missing expansion and errors unavailable, acceptance
  preserved, no extra view/add/edit/admin gates, retries, or payload logging; writer allowlist
  and destructive hints inspected. Prior contracts preserved and no static failures found.
- Remaining blocker: user review and separately authorized TOOL-030-001 through TOOL-030-005.
  Later scenarios must cover exact path/method/no body, direct User/Group membership removal,
  existing principal already absent (204 no-op), missing principal 404, invalid IDs and hidden
  issue stopping dispatch, Delete watchers without Add/View/Edit permissions, missing Delete
  permission, explicit present/absent/empty list, omitted/null/malformed expansion, malformed
  entry after the target, invalid/duplicate IDs, wrong issue ID, timeout/unexpected status,
  failed/404 read-back retaining acceptance, no retries, group-derived watching remaining,
  reader denial, destructive MCP hints, and previous-tool compatibility. Marked prep-008
  fixtures must verify actual direct membership state and permission/no-op variants, startup/
  Inspector, remaining group memberships, and task-owned cleanup preserving prior watchers.
  Builds and notification delivery checks are not needed for this unchanged-dependency contract.

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
commit. Separately authorize TOOL-030-001 through TOOL-030-005 and marked writer state/permission
verification before runtime acceptance. This ends the requested 028-030 coding range; release
acceptance and verification prerequisites are separate work, not automatically authorized here.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
