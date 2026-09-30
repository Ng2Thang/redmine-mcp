# prep-001-ruff-checks: Restore a reliable static-check baseline

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `prep-001-ruff-checks` |
| Capability | Make repository lint and format checks usable before tool implementation. |
| Type / access / destructive effects | Shared prerequisite / local source maintenance / none |
| Status | complete; repository check script and contract checks pass |
| Last updated | 2026-09-30 |
| Dependencies | None |
| Target | Python 3.13; Redmine version irrelevant to this prerequisite |
| Next action | None for this task. |

## 2. Discovery and evidence

Read-only checks on 2026-09-30 confirmed four Ruff `E501` errors and one Ruff format failure in
`src/redmine_mcp/features/issues/router.py`. The router was then reformatted. Direct Ruff lint,
Ruff format, mypy, and contract checks pass. The repository check script also passes with `uv`
available in Git Bash.
Preserve the user's deletion of the old endpoint backlog and all unrelated working-tree changes.

## 3. Requirements

| ID | User outcome | Observable behavior |
|---|---|---|
| REQ-001 | Later agents can distinguish their regressions from baseline failures. | Ruff lint, Ruff format check, and mypy complete with recorded results. |
| REQ-002 | Clients retain existing tools. | No route name, parameter, response, authentication, or MCP catalog change. |

## 4. Public contract and technical specification

No new or changed public tool, REST route, model, setting, or upstream request. Change only
formatting and lint defects in the issue router unless checks reveal a directly related blocker.
Do not suppress checks to make them pass. Error and write semantics: N/A, no runtime behavior
change is intended.

## 5. Implementation plan

1. From Git Bash, run non-rewriting Ruff lint and format checks; record exact diagnostics.
2. Correct the issue router with the smallest behavior-preserving edit.
3. Run `bash scripts/check.sh` and `git diff --check`; inspect OpenAPI operation IDs if an edit
   could affect a decorator or signature. Record any independent failures separately.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given installed tools, when checks run, then Ruff lint/format and mypy pass. | REQ-001 | Pass: `bash scripts/check.sh` reports passing Ruff lint/format and mypy. |
| AC-002 | Given the edited router, when its public signatures are inspected, then the existing tool contracts match the baseline. | REQ-002 | Pass: AST matches `HEAD`, including operation IDs and signatures. |

## 7. Test plan and execution record

STATIC-001: The initial `bash scripts/check.sh` attempt exited 1 before checks because `uv` was
unavailable in Git Bash. After `uv` became available at `/c/Users/CCVN/.local/bin/uv`,
`uv --version` reported `0.12.21` and `bash scripts/check.sh` exited 0: `All checks passed!`,
`68 files already formatted`, and `Success: no issues found in 32 source files`. Direct
equivalents from Git Bash also passed: `.venv/Scripts/ruff.exe check .`
(`All checks passed!`), `.venv/Scripts/ruff.exe format --check .` (`68 files already formatted`),
and `.venv/Scripts/mypy.exe src` (`Success: no issues found in 32 source files`). STATIC-002:
`git diff --check` exited 0. CONTRACT-001: a Python AST comparison of the complete edited router
against `git show HEAD:src/redmine_mcp/features/issues/router.py` passed; both functions retain
their names, signatures, decorators, and operation IDs (`list_issues`, `get_issue`). No Redmine,
Docker, fixtures, or live calls were needed. All commands ran from Git Bash on 2026-09-30.

## 8. Implementation and review record

The initial direct Ruff checks reproduced four `E501` lines (23-26) and one format failure in
the issue router; mypy passed. Running Ruff format on
`src/redmine_mcp/features/issues/router.py` reformatted only that file. Final direct Ruff lint,
Ruff format, mypy, diff whitespace, and AST contract checks passed. The AST of the entire module
matches `HEAD` without location attributes, so formatting did not change Python behavior or
public contracts. No other source file was edited. With `uv` available in Git Bash,
`bash scripts/check.sh` passed its frozen Ruff and mypy checks. The unrelated staged changes and
deleted issue backlog were preserved.

## 9. Completion and handoff

- [x] Direct Ruff, mypy, and contract preservation checks have passing evidence.
- [x] Repository check script passes with `uv` available in Git Bash.
- [x] Dashboard status and next action are synchronized.

Final status: complete. No further action is required for this task.
