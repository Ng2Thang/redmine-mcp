# TOOL-043 deletion testing evidence

Date: 2026-10-08. The user explicitly assigned TOOL-043 testing after implementation and review.
This record covers the current uncommitted task changes, preserving existing staged runtime edits.
All commands run from Git Bash using installed locked dependencies. No credentials are recorded.

## Implemented coverage

| Layer | Files | Coverage |
|---|---|---|
| Unit | `tests/unit/test_time_entry_deletions.py` | 32 identity/service/permission/receipt cases, including both an uncertain/204 receipt and a real HTTP response-close error after native 204 |
| Offline integration | `tests/integration/test_time_entry_deletions.py` | 82 exact-target, own/all, admission, no-body/single-delete, duplicate, rejection, receipt/read-back and REST/MCP cases |
| Shared regression | `tests/integration/conftest.py`, `test_current_tools.py` | Stateful exact DELETE support and four added writer matrix cases; existing reader/update/creation contracts retained |
| Owned native | `tests/e2e/test_time_entry_delete_acceptance.py`, `time_entry_delete_helpers.py`, `server.py`, `tools/testing/tool043_fixtures.rb` | Disposable task project/users/roles/activities/entries, native storage inspection, control/totals, permissions, independent calls, faults/race and isolated Inspector |

## Runtime defect and review regression

The initial focused run had **305 passed, 4 failed** in 318.38 seconds. All four failures exposed
one actual runtime defect: `delete_time_entry` MCP accepted undeclared `entries`, `confirm` and
`hours` arguments, and its schema lacked `additionalProperties=false`. The tool now sets that
policy explicitly in `mcp/registration.py`, following the existing strict membership-tool pattern.
The change is scoped to the new deletion operation. The same rejection cases remain regression tests.

The subsequent focused command passed **6 cases**, with 76 deselected, in 6.88 seconds:

```bash
uv run --frozen --no-sync pytest tests/integration/test_time_entry_deletions.py -q --tb=short -k 'extra_mcp or schema_annotations or visibility404 or budget_exhaustion'
```

The two additional cases prove that caller GET404 can coexist with an uncertain write and a
physically present entry, and that read-back budget exhaustion preserves accepted deletion.
The review fix is covered by real HTTPX response cleanup failure after receiving 204 as well as
synthetic `WriteReceipt("uncertain", 204)`. Native 204 retains accepted/true; status500/unknown
retains uncertain/null regardless of a later GET404. No automatic mutation retries are added.

## Execution record

Initial focused command:

```bash
uv run --frozen --no-sync pytest tests/unit/test_time_entry_deletions.py tests/integration/test_time_entry_deletions.py tests/integration/test_current_tools.py -q --tb=short
```

Final full offline regression after runtime correction and the two additional cases:

```bash
uv run --frozen --no-sync pytest tests/unit tests/integration -q --tb=short
```

Result: **1889 passed**, one existing warning, in 1035.05 seconds. This clean full run
includes all final 32 unit/82 dedicated integration cases and the corrected MCP registration.
The ignored output log is `.local/tool043-offline-results.log`.
An existing Pydantic schema deprecation warning is retained; no warning suppression was added.

Owned native command:

```bash
uv run --frozen --no-sync pytest tests/e2e/test_time_entry_delete_acceptance.py --run-e2e -q --tb=short
```

Result: **11 passed** in 272.36 seconds. The added no-issue-view permission case passed separately
with **1 passed, 11 deselected** in 20.82 seconds using `-k time_no_issue`. All 12 native cases
therefore have passing evidence; no single final 12-case rerun is claimed. The Inspector subprocess pins version
2.8.0, starts a temporary localhost writer on a free port, verifies tools/list and tools/call,
then stops the server and removes its private credential config.

Static checks passed: scoped `uv run --frozen --no-sync ruff check` on 21 task runtime/test files,
`ruff format --check` on the same 21 files, `mypy src` on 129 source files and staged/unstaged
`git diff --check`. Final diff review preserves the caller-key architecture and existing staged
runtime edits. No repository-wide Ruff result is claimed; unrelated lint debt remains unchanged.

## Native ownership and evidence limits

Preflight verifies the exact official Redmine 7.0.2 image pin, prep-018 synthetic marker, Compose
project, owned volume labels, private baseline manifest and native metadata before mutation.
Task fixtures use a private `mcp-e2e-tool043-<random>` project with only issue/time modules,
ordinary own/all/no-edit/no-time-view/no-issue-view roles/users and project-scoped activities.
Setup refuses an unreconciled TOOL-043 ledger. API keys remain in the ignored private ledger.

Task-only Rails fixture inspection lists entries in the validated owned project, independently
establishing storage-visible absence and control preservation. MCP never accesses the database.
Accepted deletion updates totals. Duplicate preflight404 does not dispatch another DELETE;
an accepted first call remains committed when a later independent call is denied.

Native fault cases intercept the receipt after a real committed deletion and inject status500,
uncertain/204, or read-back403/404. These are controlled application-level faults, not TCP-loss
experiments. The race case moves an owned entry to another owned issue after preflight and before
native DELETE, exercising the explicitly documented lack of a lock/If-Match linkage guard.
Actual role visibility changes producing caller404 are not forced live; offline coverage proves
that the observation cannot establish physical absence. Arbitrary plugin destruction failures,
every infrastructure cleanup exception and alternative global policies remain outside evidence.

Global policies are observed without changes. Shared users/roles/settings/global activities,
the older shared Redmine 6.0.5 instance and incident entries #919–#924 are untouched.
Cleanup verifies exact owned identifiers, removes remaining task resources and reports zero
project/entry/user/role/activity counts. Final cleanup passed with all five counts zero in
`.local/testing-e2e/tool043-last-cleanup.json`. No TOOL-043 fixture ledger or Inspector credential
config remains. Observed unchanged global policies: future dates allowed, closed-issue time
allowed, daily maximum 999 hours, required fields empty. The temporary Inspector server stopped.

## Traceability and acceptance

| Scenarios | Evidence |
|---|---|
| TOOL-043-001/002 | Unit/service strict IDs, exact gateway preflight and no-body deletion, invalid input and zero mutation on rejection |
| TOOL-043-003/006 | Credited user versus author, native own/all alternatives, view requirements, conditional/unknown evidence, gates, REST/MCP schema/discovery/report, explicit CSV/allowed_all |
| TOOL-043-004/005 | Accepted/uncertain receipts independent of presence, forbidden/malformed/budget/timeout observation, native rejection, pre-dispatch failure, one mutation and duplicate404 |
| TOOL-043-007/008 | Owned native own/all/denied/no-view state, storage absence/control/totals, duplicate and independent-call outcomes; Inspector |
| TOOL-043-009 | Owned committed fault receipts and moved-entry race, offline visibility404 ambiguity; limitations above |

Status: **complete** within the recorded offline and owned native evidence scope. Task/dashboard
acceptance is synchronized; broader policy/plugin/infrastructure variants remain disclosed.
