# tool-034-list-issue-estimates: Preserve estimates in issue lists

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-034-list-issue-estimates |
| Capability | Clients can read issue estimates from a complete list and calculate truthful totals |
| Type / access / destructive effects | Extend `list_issues` / read-only / none |
| Status | complete - implementation and authorized acceptance passed |
| Dependencies | Existing issue reader, tool-015 detail estimate implementation, prep-015 read budgets; prep-002/016/017 testing infrastructure for later verification |
| Related tasks | [tool-035](tool-035-list-time-entries.md), [dashboard](../index.md) |
| Target Redmine | Owned pinned 7.0.2-bookworm; native/REST/SDK acceptance passed |
| Last updated | 2026-10-06, Codex |
| Assignment | User requested implementation and separately authorized testing on 2026-10-06 |
| Next action | None for this assignment; repeat commands are recorded below |

## 2. Discovery and evidence

The conversation exposed a list/detail mismatch: eight selected Urgent issues had 12-hour
detail estimates, but the list model discarded estimates. The reporting helper then converted
absent fields to null and incorrectly claimed estimates were unset. The conversational 96-hour
result is historical evidence, not a pinned-runtime acceptance check.

`IssueDetail` previously defined estimates; `Issue`, used by `Page[Issue]`, did not. The list
gateway observed only spent-hour fields. The smallest fix extends the existing shared model and
mapper; it does not fetch one detail per issue or introduce an aggregate tool.

| Source | Checked | Finding / limitation |
|---|---|---|
| [Exact Redmine 7.0.2 release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-06 | `app/views/issues/index.api.rsb` and `show.api.rsb` emit both estimate fields; no live call needed to establish source mapping |
| `deploy/compose.test.yaml` | 2026-10-06 | Pins the target 7.0.2 image; does not prove the shared running container version |
| `features/issues/models.py`, `integrations/redmine/issues.py`, issue router | 2026-10-06 | Detail-only fields caused list truncation; existing typed response wiring carries the extension |

Preserve the working-tree baseline: pre-existing membership, writer configuration, catalog,
documentation and test edits were present. This assignment uses one agent, English Markdown
and Git Bash. It excludes tests, fixtures, startup, Inspector and live state changes.

Decisions: retain both direct and descendant-inclusive estimates; retain nullable types and
existing detail behavior; missing upstream fields remain distinguishable through visibility.

## 3. Requirements

| ID | Observable behavior |
|---|---|
| REQ-001 | Both estimate fields survive issue-list model conversion and REST/MCP serialization |
| REQ-002 | Missing, explicit null and zero estimates retain distinct evidence |
| REQ-003 | Invalid estimates fail safely; existing search/detail inputs, auth and pagination remain compatible |
| REQ-004 | Tool guidance describes complete pagination, deduplication, decimal sums and unavailable estimates |

No new inputs, permissions, dependencies, aggregation service or priority filter are in scope.
Use existing caller issue visibility; this task introduces no editability guarantee.

## 4. Public contract and technical specification

- MCP operation: existing `list_issues`; REST `GET /api/v1/issues`; upstream `GET /issues.json`.
- Move `estimated_hours` and `total_estimated_hours` into `Issue`; `IssueDetail` inherits them.
- Both fields use nullable `IssueHours`: finite nonnegative JSON numbers, including zero.
  Strings, booleans, negative values and nonfinite numbers remain invalid.
- Extend the list gateway's `observed_fields` with both estimates. Missing keys yield null and
  `/items/{index}/{field}` marked `not_returned`; explicit null yields no absence observation.
- Existing page envelope, inputs/defaults, ordering, includes and request count remain intact.
  Reader annotations remain read-only, nondestructive, idempotent and open-world.
- Existing personal-key authentication and issue visibility apply. No writer access is needed.
- Invalid input uses existing 422; rejected keys/resources use sanitized 401/403/404;
  malformed response uses 502; transport/deadline/budget errors retain existing envelopes.
- Reporting guidance: collect the complete permitted scope, deduplicate IDs, sum numeric
  `estimated_hours` with decimal arithmetic, and report unavailable estimates separately.
  Never substitute zero for null or add overlapping descendant totals. Check `get_issue` with
  the same caller before concluding an unavailable list estimate is unset.
- Write semantics: N/A - read-only; no Redmine state change or retry policy change.

## 5. Implementation plan

| Step | Change | Dependency |
|---|---|---|
| 1 | Move estimates into the shared issue model | Existing detail contract |
| 2 | Observe estimates in paginated list mapping | Step 1 |
| 3 | Update router description, public reference, changelog and reporting examples | Steps 1-2 |
| 4 | Run Ruff/mypy and inspect the diff; synchronize task/dashboard records | Steps 1-3 |
| 5 | Implement and execute planned regressions only in a separate testing assignment | User testing authorization |

No Protocol signature, service, bootstrap, allowlist or dependency changes are required.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Result | Verification |
|---|---|---|---|
| AC-001 | REQ-001 | A list and detail both retain upstream 12-hour estimates | TOOL-034-001,003,005 passed |
| AC-002 | REQ-002 | Omitted/null/zero estimates have the documented evidence | TOOL-034-001 passed |
| AC-003 | REQ-003 | Malformed numbers fail safely; existing queries and detail fields remain compatible | TOOL-034-002,003 passed |
| AC-004 | REQ-004 | Eight unique selected 12-hour estimates sum to 96; incomplete/null cases are not claimed complete | TOOL-034-004 passed |

## 7. Test plan and execution record

| Scenario | Planned layer and setup | Expected |
|---|---|---|
| TOOL-034-001 | Offline model/gateway/REST: numeric, missing, explicit null and zero for both fields in list and detail | Values and page/detail visibility paths match |
| TOOL-034-002 | Offline malformed numbers, including strings, booleans, negative and raw nonfinite payloads | Sanitized 502; no fabricated estimate |
| TOOL-034-003 | REST/MCP discovery and invocation with existing include/filter defaults | Additive response schema, inherited detail fields, no detail-request fanout |
| TOOL-034-004 | Offline reporting example with multiple pages, duplicate IDs, parent/child rollups, decimals, null and incomplete pages | Unique direct estimates, 96-hour complete fixture; truthful partial/unavailable totals |
| TOOL-034-005 | Opt-in owned Redmine 7.0.2 same-key native/REST/MCP list/detail comparison | Actual estimate parity and caller visibility |

Extend existing reader contract and MCP tests in a later assignment; do not modify their
fixtures or expectations during coding. Reporting examples remain client calculations, not a
new runtime aggregation interface.

| Evidence | Procedure | Actual | Status |
|---|---|---|---|
| EVID-001 | Git Bash prerequisite doctor | Required prerequisites ready | Passed 2026-10-06 |
| EVID-002 | `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .`; `uv run --frozen --no-sync mypy src`; `git diff --check` | Lint passed; 239 files already formatted; mypy passed for 120 source files; no whitespace errors | Passed 2026-10-06 |
| EVID-003 | TOOL-034-001..005 automated and owned live checks | Not run; excluded from coding assignment | Pending separate authorization |

## 8. Implementation and review record

Testing follow-up (2026-10-06): the user explicitly requested the testing phase for tasks 034
and 035. Added `tests/integration/test_issue_estimates.py` with list/detail presence and value
parity, malformed raw numeric payloads, SDK invocation without detail fanout, complete paginated
deduplication and the 96-hour fixture, decimal arithmetic and truthful partial previews. The
general-reader suite verifies additive Issue/IssueDetail OpenAPI fields. Existing reader tests
retain include/filter/default regressions.

`tests/e2e/test_reporting_acceptance.py` creates eight disposable 12-hour issues in the owned
reporting project, compares same-key native/list/detail/SDK responses and deletes those issues.
The repeatable Inspector helper verifies discovery and estimate fields through a temporary
reader-only server. Initial test-only assertions were corrected for MCP identity traffic;
no runtime change was needed in this testing assignment.

| Evidence | Procedure | Actual | Status |
|---|---|---|---|
| EVID-004 | `uv run --frozen --no-sync pytest tests/e2e/test_reporting_acceptance.py --run-e2e -q` | Both reporting acceptance tests passed on the owned pinned 7.0.2 environment; issue and time-log cleanup passed | Passed 2026-10-06 |
| EVID-005 | `uv run --frozen --no-sync python scripts/verify-reporting-inspector.py` | Inspector 2.8.0 discovered the reader catalog and passed six calls, including list/detail estimates; temporary server stopped | Passed 2026-10-06 |
| EVID-006 | `uv run --frozen --no-sync pytest -q` | 883 offline cases passed, including all 139 new dedicated reporting cases and extended reader errors/catalog checks; one existing Pydantic deprecation warning | Passed 2026-10-06 |
| EVID-007 | Ruff lint, Ruff format check, `mypy src`, `git diff --check` | Lint passed; 244 Python files formatted; mypy passed for 120 source files; no whitespace errors | Passed 2026-10-06 |

The initial coding restrictions and pending evidence above are historical. This explicitly
authorized testing assignment supersedes them for the selected scenarios.

- Changed shared issue fields, list observation mapping and existing tool guidance.
- Updated tool reference, changelog, manual-verification plan and coverage/dashboard records.
- Preserved unrelated edits and all test files. No dependencies or lockfile changes.
- Static checks: EVID-002 passed. Final diff review confirmed inherited detail types,
  raw upstream absence observations and unchanged list request parameters; no detail fanout.
  No tests, startup, Inspector or live calls executed.
- Plan deviations: none; inherited detail fields preserve their existing types and defaults.

## 9. Completion and handoff

- [x] Required behavior implemented in code.
- [x] Public documentation updated.
- [x] Source evidence reviewed for the target version.
- [x] Static checks and final diff review recorded.
- [x] TOOL-034-001..005 have passing acceptance evidence.
- [x] Task/dashboard final status synchronized.

Final status: complete. Offline, owned live and Inspector acceptance passed, with static
checks and task/dashboard/coverage records synchronized. Existing staged implementation
changes were preserved; the testing assignment did not change runtime code or dependencies.
The 96-hour result is an owned fixture assertion, not a claim about the conversation's project.
