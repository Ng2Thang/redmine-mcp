# tool-037-update-issue-tags: Change issue tag assignments with permission preflight

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-037-update-issue-tags |
| Assigned capability | Later add/remove assignments on one issue, creating unfamiliar names only with permission |
| Type / access / effects | Proposed update_issue extension / write / issue associations and possibly new tag names |
| Status | blocked |
| Dependencies | Existing TOOL-025 writer/PREP-019 receipts and effective preflight; proven native REST write/verification contract; explicit future write assignment |
| Related tasks | [prep-028](prep-028-redmineup-tags-api-readiness.md), [dashboard](../index.md) |
| Target | Existing Redmine 7.0.2 + Tags 2.2.0 Light; no server modifications |
| Last updated | 2026-10-08, Codex |
| Next action | Keep writes deferred; establish effective preflight, new-name existence and concurrency/verification through existing REST before coding |

## 2. Discovery and evidence

Original outcome: add/remove on one issue, create a name when assigning if allowed; never
globally rename/delete/merge tags or create unused names independently. Current update models
forbid unknown fields; no tag writer exists. Current server interaction is authorized for REST
queries only. This plan does not authorize PUT, a writer test, server changes or installation.

Apply `AGENTS.md`, [workflow](../../workflows/redmine-tools.md),
[template](../../templates/redmine-tool-task.md), review/planning skills, English Markdown and
Git Bash. Preserve staged docs/PREP-028 source. No code/tests/live calls are performed here.

[TAGS-REST-001..003](../../integrations/redmineup-tags.md) prove known-name filtering and
missing full-tag reads. They prove neither write permission nor mutation side effects.
Exact Tags `init.rb:47-50` registers edit_tags/create_tags. `issue_patch.rb:125-137` accepts
tag_list/add_tag_list/remove_tag_list inside safe_attributes and silently omits denied changes.
Creation or globally allowed existing names are checked after edit_tags. Issue.allowed_tags?
uses a memoized global used-name list, not a complete caller-visible REST catalogue.

Core IssuesController admits API update, has an Issue.transaction save path and native 204
success. Those facts do not establish effective per-field preflight or concurrency-safe tag
deltas. The vendor computes deltas from its loaded tag list before saving; the tag hook journals
tag_list requests, not automatically add_tag_list/remove_tag_list. No authorized live write
evidence was supplied. Source existence is distinct from an implementable safe public writer.

| Decision | Resolution |
|---|---|
| DEC-001 | Assignment removal only; creation only with assignment |
| DEC-002 | Reuse update_issue after prerequisites; no new tag management tool |
| DEC-003 | Permission names known, effective issue/tag preflight and new-name existence remain unresolved |
| DEC-004 | Atomicity/concurrency and mixed-field/no-op behavior remain unresolved |
| DEC-005 | Write effects, journaling/notifications, duplicate behavior and sufficient REST verification remain unresolved |
| DEC-006 | Conditional/unknown role evidence is not an effective grant; read filter success is no grant |

## 3. Requirements

| ID | Required behavior |
|---|---|
| REQ-001 | Deltas preserve unrelated assignments on the selected visible issue |
| REQ-002 | New names are created only with effective create permission |
| REQ-003 | Prove effective target/tag permissions and new-name rules before mutation |
| REQ-004 | Separate restricted writer, source-backed concurrency guard, no automatic mutation retries |
| REQ-005 | Report acceptance/uncertainty separately from actual REST state verification |
| REQ-006 | Preserve other issues/global tags and existing non-tag update contracts |

## 4. Public contract and technical specification

Proposed extension only: update_issue, `PUT /api/v1/issues/{issue_id}`. Existing separate writer
and operation gate; add optional add_tags/remove_tags arrays. Target issue ID positive. Proposed
bound 20 unique nonblank names per delta, no nulls/overlap; creation never from removals.
Exact canonicalization/length, empty/no-op and mixed ordinary-field rules remain blocked.
No fields are added to runtime request/schema until the safe contract is finalized.

Native source identifies a candidate payload, not accepted behavior:

```json
{"issue":{"add_tag_list":["notification"],"remove_tag_list":["urgent"]}}
```

Candidate native route: PUT /issues/{id}.json. The source supplies issue update 204/no-body
handling, but permission failures may silently discard tag attributes. Never infer tag success
from that HTTP status or rely on silent omission as the required permission preflight.
Full visible list_tags output would not prove global name existence. Current REST exposes no
proven new-name/effective authorization endpoint. Add-notes permission alone is insufficient.

Native optimistic issue locking/transaction source does not prove this delta computation
preserves concurrent tag updates. Do not calculate a replacement tag_list client-side or
assume two writes can atomically combine fields/tags. A server companion is prohibited; if the
existing API cannot meet the guarantees, leave this outcome blocked.

Reuse existing accepted/uncertain receipts only after contract completion. tags observation
requires actual REST data; current issue reads omit it. TOOL-036 can check a supplied known
name under verified visibility, but cannot reconstruct complete assignments, prove untouched
names were preserved or resolve every negative match. A selected filter name must never be
inserted into observed_issue.tags. Verification must stay unavailable where evidence is absent.
Exact success/error/no-op/mixed-field rules must be finalized before implementation.

### Write effects and recovery prerequisites

Source tagging callbacks can create tag rows and remove associations. Orphan deletion depends
on native configuration; other plugins/hooks can journal or notify. Side effects/partial failure
need owned evidence, not assumptions. Repeated desired deltas may preserve a set but journal,
notifications and creation race behavior are not asserted idempotent. Never retry mutations
automatically. Timeout/read-back failure preserves uncertainty or accepted status; reconcile
using proven existing REST state before another attempt. No rollback/cleanup guarantee is made.

Input/auth/resource/native-validation/transport errors retain current conventions after the
exact native contract is frozen. Do not predeclare a new tags_unavailable flag/code or bypass
existing permission/receipt rules. Specification exit: blocked; no writer coding is ready.

## 5. Implementation plan

| Step | Ownership / prerequisite |
|---|---|
| 1 | Establish effective existing REST permission/new-name proof and explicit write authorization |
| 2 | Freeze atomic/concurrency/no-op/mixed-field/effect/verification contract |
| 3 | Only then add request fields, capability intent and port/service/gateway mapping |
| 4 | Preserve single-dispatch receipts and safe read-back; update writer guidance |
| 5 | Separate static checks and explicitly authorized disposable writer verification |

Potential paths after unblocking: write_models, capability models/resolver, issue updater,
writer router and public docs. No dependency/server installation changes. Tag filtering
is not a sufficient safety prerequisite or a mandatory code dependency. PREP-028
does not own writer permission/concurrency decisions; this task owns its unresolved write contract.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Expected | Scenario |
|---|---|---|---|
| AC-001 | REQ-001 | Adds/removes preserve other assignments | TOOL-037-001,006 |
| AC-002 | REQ-002 | Create denied/allowed with correct unfamiliar-name proof | TOOL-037-002,006 |
| AC-003 | REQ-003 | Effective issue/tag checks precede dispatch | TOOL-037-002,005 |
| AC-004 | REQ-004 | Restricted writer, concurrency, no automatic retry | TOOL-037-003,004,006 |
| AC-005 | REQ-005 | Receipts reflect acceptance/uncertainty and actual available observations | TOOL-037-003,005,006 |
| AC-006 | REQ-006 | Other issues/global rows and non-tag contracts preserved | TOOL-037-001,004,006 |

## 7. Test plan and execution record

| Scenario | Later separately authorized verification |
|---|---|
| TOOL-037-001 | Delta/payload/preservation, already-present/absent and no-op rules after decisions are frozen |
| TOOL-037-002 | edit_tags/create_tags and issue/workflow/ownership combinations; unfamiliar global names and incomplete metadata |
| TOOL-037-003 | Empty 204, silent ignored fields, lost response/timeouts, malformed/read-back-unavailable receipts |
| TOOL-037-004 | Input/mixed-field/duplicate rules; restricted deployment and no retries; old writer contracts |
| TOOL-037-005 | REST/MCP schema/auth/preflight/receipt parity; no fabricated tags |
| TOOL-037-006 | Explicitly authorized disposable existing-environment writer checks, real state, concurrency/journals/hooks and task-owned cleanup |

TOOL-037-EVID-001 planning/source review retained. TOOL-037-EVID-002/003 remain not run;
the supplied GET controls are not writer tests. No PUT, fixtures, test dependency, seed/reset,
installation or cleanup ran. Any future mutation/cleanup needs an explicit writer assignment.

## 8. Implementation and review record

Renumbered from the former assignment-write task on 2026-10-08 at the user's request, after
the complete-assignment read and discovery plans were removed. Scenario and evidence IDs now
use TOOL-037. No writer code or verification was added by the renumbering; existing blockers
remain. See the [mapping](../index.md#tags-task-removal-and-renumbering-2026-10-08).

Reviewed with TAGS-REV-005. Replaced unknown permission identifiers with source facts while
retaining effective authorization gaps. Removed stale package-access/PREP-028 writer ownership
and assumed full-tag catalogue/read-back dependencies. Added the current query-only execution
boundary. No mutation code, new capability, request fields or tags receipts are implemented.

## 9. Completion and handoff

- [x] Source facts and independent writer blockers reviewed.
- [ ] Effective preflight/new-name/concurrency/verification contract established.
- [ ] Explicit mutation assignment and disposable scope provided.
- [ ] Runtime writer implemented and acceptance passed.
- [x] Dashboard synchronized.

Final status: **blocked**, not implemented. Filtering can proceed separately; it does not
unblock writes or authorize attempts against the current server.
