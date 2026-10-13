# PREP-029: Redmine 6.0.1 E2E verification

Date: 2026-10-13. The user authorized running and fixing the complete selected E2E
suite, then separately authorized Ruff and mypy. Verification used the working tree
and existing Compose project `redmine-mcp-test-6-0-1` at `http://127.0.0.1:3001`.

## Results

Executed from the repository root in Git Bash:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e
```

The final command exited zero: **50 passed, 0 failed, 0 skipped**, with one Pydantic
deprecation warning, in **624.41 seconds**. Private output is retained at
`.local/e2e-6.0.1-final.log`. An earlier complete run recorded 23 failures, 25 passes,
and two skips; an intermediate focused run passed all eight selected cases.

| Acceptance module | Passed |
|---|---:|
| Catalog | 4 |
| Issue tag filters | 3 |
| Live tool lifecycle and permissions | 15 |
| Preparation acceptance | 2 |
| Read retries | 2 |
| Reporting | 2 |
| Time-entry deletion | 12 |
| Time-entry updates | 10 |
| Total | 50 |

Ruff lint and formatting checks passed for all eight changed Python files. Mypy passed
for `src/redmine_mcp` (130 source files). A broader `mypy src` invocation reported four
errors in the separate documentation package: `vendor_assets.py` has an Any return;
`portal.py` has a variable-type mismatch and two HTTP handler override mismatches.
Those errors remain unresolved and do not constitute a clean repository-wide type check.

## Fixes verified

- Normalize the complete counted project collection returned by 6.0.1 when it ignores
  pagination. Require matching integer echoes and distinct positive IDs before slicing;
  preserve existing acquisition budgets and other strict envelope checks.
- Decode native rational time-entry hours such as `"5/4"` in the adapter. Public write
  requests retain numeric-only hour validation. Receipt verification accounts for native
  whole-minute precision; the live update assertion checks the native rational value on
  6.0.1 and the two-decimal number on newer APIs.
- Observe the installed time-log settings, including unrestricted closed-issue logging
  when the newer closed-issue setting is absent.
- Supply the native category permission and repair manifest-owned project fixture states
  after reloading their nested-set positions. Refuse outstanding permission reconciliation
  and unexpected descendants before changing project states.
- Seed the `notification` tag on the owned baseline issue. All three read-only tag tests
  executed and passed against the existing plugin.
- Retain private TOOL-042/043 stdout/stderr diagnostics when fixture commands fail.

## Cleanup and limits

The final TOOL-042 and TOOL-043 cleanup evidence both report `cleanup: passed`, with
zero remaining projects, entries, users, roles, and activities. Their evidence files are
`.local/e2e/6.0.1/tool042-last-cleanup.json` and `tool043-last-cleanup.json`.
The persistent baseline fixtures remain available for subsequent runs.

This result verifies the complete requested 6.0.1 E2E command, including its Inspector
cases. Redmine 7.0.2 acceptance, simultaneous-stack coexistence, explicit reset isolation,
browser supplements, and the remaining offline PREP-029 lifecycle/profile scenarios were
not executed in this assignment. PREP-029's broader acceptance remains pending.
