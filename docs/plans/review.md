# Review of the Redmine 7.1 capability roadmap

Reviewed 2026-10-01 against the repository task workflow, current 11-tool
catalog, `deploy/compose.test.yaml`, the 28 new task documents, and
authoritative Redmine API and source references linked in the
[master plan](redmine-7-1-capabilities.md).

Verdict: **ready as a sequential task breakdown; implementation is blocked
until prerequisite evidence and task review are complete**. No code, tests,
Docker data, or live Redmine state were changed for this review.

| Finding | Severity | Evidence and impact | Correction / current resolution |
|---|---|---|---|
| REV-001 | Blocking for implementation | Repository targets 6.0.5; Documents REST begins in 7.1, and no exact released 7.1 build is pinned. | `prep-005` requires an immutable build, versioned source review, isolated migration, API check, backup, and recovery. Dependent contracts are blocked until evidence exists. |
| REV-002 | Major | Existing tasks `prep-003` and `tool-002` through `tool-013` have pending runtime/testing acceptance. | `prep-004` reconciles original records and requires separately authorized checks before the new chain opens. |
| REV-003 | Major | A generic attachment mutation could target the wrong container; `GET /attachments/:id` metadata does not prove Project/Version/Document/Issue ownership. | Mutation tools require declared type/ID and a containing-resource read before PATCH/DELETE. |
| REV-004 | Major | A schedule assembled from issues does not enforce Redmine's native `view_gantt` permission. | Main plan explicitly labels the client-rendered schedule and creates no Gantt tool. |
| REV-005 | Major | Existing MCP catalog validates only GET operations, and a true read-only deployment cannot expose writes safely. | `prep-007` owns the separate writer, operation authorization, catalog validation, and truthful write receipts before any write tool. |
| REV-006 | Major | User instructions prohibit automatic unit-test verification, while completion requires accepted evidence. | Each task has a separate testing handoff and remains blocked if testing is not authorized or acceptance evidence is missing. |
| REV-007 | Minor | Initial generated prerequisite documents contained tool-specific boilerplate, and unrelated readers mentioned download-counter effects. | Replaced all six prerequisite contracts with relevant procedures and corrected reader access/effect descriptions. |

## Structural audit

- One public owner per selected behavior: two existing operation extensions,
  six new readers, and fourteen new writers.
- Six shared prerequisites and 22 tool tasks are in one dependency chain with
  unique IDs `prep-004..009` and `tool-014..035`. Retired and old IDs remain
  untouched.
- All 28 child documents contain the nine task-template sections, a source
  link, requirements, acceptance criteria, planned scenarios, pending evidence,
  and a next action.
- Future task documents are intentionally `blocked` while exact 7.1 evidence
  and predecessor acceptance are absent. `prep-004` is `planned` as the first
  documentation-ready action; no future code or test is marked done.
- Upgrade, permission, retry, timeout, binary-limit, state verification,
  and cleanup boundaries are assigned to explicit owners.

## Remaining handoff

The next action is `prep-004-accept-existing-baseline`: inspect the pending
old-task criteria, prepare a reviewable testing request, and run only checks
separately authorized by the user. After user acceptance of that task, select
an exact released Redmine 7.1 artifact for `prep-005`.

This review evaluates the planning artifacts. It is not runtime acceptance
of any planned operation.
