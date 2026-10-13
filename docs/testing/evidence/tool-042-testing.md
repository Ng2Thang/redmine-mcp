# TOOL-042 testing evidence

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../../configuration.md#separate-writer-deployment).

Date: 2026-10-08. Assignment: implement and execute tests for
[TOOL-042](../../plans/tasks/tool-042-update-time-entry.md). Earlier coding-only restrictions
were superseded for this testing stage. No other tool was implemented; TOOL-043 remains planned.

## Scope and environment

Offline tests use fake settings, HTTPX MockTransport, explicit ASGI lifespan and real MCP SDK
sessions. The autouse fixture blocks real HTTP transports and clears inherited Redmine settings.
Tests cover strict update validation, exact issue/entry/project/user targets, credited-user own
permissions, writer gates, partial payloads, native normalization, independent observations,
mutation uncertainty, schema/discovery/annotations/reporting and existing catalog compatibility.

The selected native environment is the owned `redmine-mcp-e2e` deployment at localhost:3001,
Redmine 7.0.2. Existing preflight verifies image pin, marker, volume labels and baseline manifest.
The shared localhost:3000 Redmine 6.0.5 instance was not used or changed. Incident entries
#919–#924 were not read, updated or used as fixtures.

The task-specific Ruby fixture helper creates one private disposable project, four ordinary
users/roles, active/inactive project activities, and exact entry/issue targets. It does not
change baseline users, roles, global activities, global settings, plugins or deployment settings.
Credentials stay in the ignored private fixture ledger and transient Inspector config; no keys
are written to tracked files or test output. Cleanup validates names and ownership, removes
owned resources, verifies zero remaining projects/entries/users/roles/activities, and writes
redacted counts to `.local/testing-e2e/tool042-last-cleanup.json`. Inspector configuration is
removed and its temporary localhost server is stopped.

## Test implementation and traceability

| Scenarios | Implementation | Evidence boundary |
|---|---|---|
| TOOL-042-001 | `tests/unit/test_time_entry_updates.py`; invalid-input integration cases | Empty/null/unknown inputs, positive strict IDs/hours, finite numbers, dates, activity IDs, comments clear/limit, supplied fields only |
| TOOL-042-002 | `tests/integration/test_time_entry_updates.py`; shared synthetic fixture | Exact target identities, no PUT on missing/wrong/malformed target, partial payload and preservation of control entries |
| TOOL-042-003 | Unit service/permission tests and integration ownership/gates/unknown-role cases | Credited user versus author, own/all/log-only/no-view, pinned/personal admission, native final authority with incomplete evidence |
| TOOL-042-004 | Integration observation cases | 204 without body, minute/API rounding, missing/mismatched/forbidden/malformed observations preserve acceptance |
| TOOL-042-005 | Integration native rejection/pre-dispatch/dispatched/commit-response cases | Sanitized statuses, single mutation attempt, preserved uncertainty after commit even if read-back matches |
| TOOL-042-006 | Integration SDK/schema/discovery/report tests and generic current-writer matrix | Explicit allowlist, allowed_all, destructive hints, unchanged existing readers and writers |
| TOOL-042-007 | `tests/e2e/test_time_entry_update_acceptance.py`: REST/MCP updates and Inspector | Native fields/IDs/credited user, aggregate hours, control preservation, valid activity updates and exact owned cleanup |
| TOOL-042-008 | Owned roles/wrong-target/invalid-inactive activity/current-settings cases | Native own/all/no-edit/no-view, other credited user, current future/closed/comments/daily policy without changing settings |
| TOOL-042-009 | Owned commit fault cases | Real native commit followed by adapter reply-loss injection, failed observation and intervening native edit; no automatic replay |

Shared fixture updates supply exact time-entry detail/PUT responses, native hour display
normalization and project activity expansion for catalog invocation. Existing TOOL-040 activity
discovery is invoked by the preserved reader matrix; this is compatibility evidence, not a
retroactive full acceptance claim for its waived scenarios. TOOL-041 creation tests remain separate.

## Commands and results

All commands run from Git Bash with existing locked dependencies; no installation performed.

```bash
uv run --frozen --no-sync pytest tests/unit/test_time_entry_updates.py tests/integration/test_time_entry_updates.py tests/integration/test_current_tools.py -q --tb=short
uv run --frozen --no-sync pytest tests/unit tests/integration -q --tb=short
uv run --frozen --no-sync pytest tests/integration/test_time_entry_updates.py -q --tb=short -k 'inaccessible_preflight or wrong_response_identity or incomplete_role'
uv run --frozen --no-sync pytest tests/integration/test_reader_contracts.py::test_user_005_009_all_reader_mcp_invocation_and_sanitized_errors -q --tb=short
uv run --frozen --no-sync pytest tests/e2e/test_time_entry_update_acceptance.py --run-e2e -q --tb=short
uv run --frozen --no-sync pytest tests/e2e/test_time_entry_update_acceptance.py --run-e2e -q --tb=short -k 'commit_faults or current_settings'
uv run --frozen --no-sync pytest tests/e2e/test_time_entry_update_acceptance.py --run-e2e -q --tb=short -k native_update_state
uv run --frozen --no-sync mypy src
git diff --check
```

Scoped Ruff commands use only the changed Python test/fixture files. The six task files were
checked together; the corrected reader file was subsequently checked separately:

```bash
test_files=(
  tests/unit/test_time_entry_updates.py
  tests/integration/test_time_entry_updates.py
  tests/integration/test_current_tools.py
  tests/integration/conftest.py
  tests/e2e/test_time_entry_update_acceptance.py
  tests/e2e/server.py
)
uv run --frozen --no-sync ruff check "${test_files[@]}"
uv run --frozen --no-sync ruff format --check "${test_files[@]}"
uv run --frozen --no-sync ruff check tests/integration/test_reader_contracts.py
uv run --frozen --no-sync ruff format --check tests/integration/test_reader_contracts.py
```

| Check | Result |
|---|---|
| Initial focused offline run | 335 passed, 3 failed; test setup corrected as described below |
| Full offline regressions after corrections | 1,755 passed, 1 failed; 1,165.19 seconds. Sole failure was the older reader-catalog argument map; corrected and rerun passing |
| Seven later offline edge cases | 7 passed; 92 deselected |
| Corrected reader-catalog case | 1 passed; 1.52 seconds; no assertion weakened |
| Initial owned live set, including Inspector | 7 passed |
| Added native fault/current-settings set | 4 passed; 6 deselected |
| Native aggregate recheck after correction | 2 passed; 8 deselected |
| Final owned live set with project activities | 10 passed; 152.14 seconds; includes Inspector discovery and update |
| Scoped Ruff lint/format | Pass; six task test/fixture files plus the corrected reader test |
| Full-source mypy | Pass; 128 source files |
| Diff whitespace review | Pass |

No full offline rerun is claimed after the seven late edge cases and corrected catalog argument:
full regression evidence and passing targeted selections are reported separately. All observed
failures are resolved; TOOL-042 has 61 unit and 99 dedicated integration cases with passing
evidence across the full run and later selection. One existing Pydantic
deprecation warning appears in test runs. The seven unrelated repository-wide Ruff lint findings
and one formatting issue recorded during coding are not fixed or hidden by this assignment.

## Findings and corrections

The first offline run found test setup mistakes, not runtime defects: changing the stored entry
ID makes the synthetic lookup return 404 rather than an inconsistent detail body; the pinned
writer needed its configured admitted user ID; the capability endpoint is
`/api/v1/users/current/project-capabilities`. Corrected cases retain negative assertions and
the wrong-detail-response-ID case independently verifies a sanitized 502 and zero mutations.

The native aggregate assertion initially assumed rounded entry display values were also used
in issue totals. Native 7.0.2 displays entry hours as 1.23 for stored 1.234, but reports issue
spent_hours=2.234 after adding the untouched one-hour control. The corrected assertion verifies
that distinction. No runtime code change was required.

The full regression run found one existing all-reader SDK invocation missing TOOL-040's required
project_id. Added that argument in `test_reader_contracts.py` and reran the exact case: passing.
Its discovery, invocation and sanitized-error assertions remain intact. The full run already
passed all then-collected TOOL-042 cases; the seven subsequently added edge cases also passed.

Fault tests distinguish transport-only offline cases from native commit tests. Native reply-loss
injection returns an uncertain adapter receipt after an actual accepted PUT; it does not simulate
a dropped TCP connection. Native read-back failure and concurrent edit are injected only for the
task-owned target. Current policy cases do not force global required-comments/daily/future/closed
settings; disabled constraints are not claimed as exercised rejection variants. Coverage does
not establish arbitrary plugin/custom-field behavior or safety against every concurrent race.
The observed owned policies allow future dates and closed-issue edits, allow empty comments,
and set the daily maximum to 999 hours. Native acceptance exercises those current settings,
including daily-limit rejection, rather than changing the global configuration to force
other combinations. Cleanup evidence reports zero remaining task-owned projects, entries,
users, roles and activities.

Final status: TOOL-042 is **complete** for its specified update contract and documented evidence
boundary. No observed defect remains. Tests cover current owned native policy settings;
alternative global settings, arbitrary plugins/custom fields and every concurrent race remain
unverified variants. Whole-repository Ruff findings remain unrelated baseline debt. The record
does not claim a clean full-suite rerun after the final small fixture/argument edits.
