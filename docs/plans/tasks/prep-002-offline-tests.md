# prep-002-offline-tests: Establish offline MCP tool verification

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | `prep-002-offline-tests` |
| Capability | Verify reader tools without Docker, network, or real credentials. |
| Type / access / destructive effects | Shared testing prerequisite / test infrastructure / none |
| Status | complete; offline suite and repository checks pass |
| Last updated | 2026-09-30 |
| Dependencies | [prep-001](prep-001-ruff-checks.md) |
| Target | Redmine 7.0.2; runtime acceptance pending |
| Next action | None for this task. |

## 2. Discovery and evidence

Before this task there was no automated test directory or testing CI. `create_app` reads `.env`
through `Settings`, manages an HTTPX upstream client, and mounts MCP over internal ASGI requests.
The current three tools are in the explicit allowlist. Existing testing guidance is in
`docs/testing-roadmap.md`.
Python 3.13, `uv` 0.12.21, and local Ruff are available in Git Bash with
`$HOME/.local/bin` on `PATH`. Testing CI remains unconfigured.

## 3. Requirements

| ID | User outcome | Observable behavior |
|---|---|---|
| REQ-001 | Later tool agents can test safely. | Default test command needs no Docker, network, `.env`, or real Redmine key. |
| REQ-002 | Changes are checked at the MCP boundary. | Baseline tests cover discovery, bearer auth, invocation, response mapping, and errors. |

## 4. Public contract and technical specification

No public tool contract changes. Add `pytest` and `pytest-asyncio` as dev dependencies with
`pyproject.toml` and `uv.lock` updated together. Provide fake settings before app creation, an
HTTPX `MockTransport` upstream, explicit ASGI lifespan handling, and an in-process MCP SDK
client. The default command is `uv run --frozen pytest`. Tests must fail if they accidentally
reach the network or load local credentials. Write semantics: N/A.

## 5. Implementation plan

1. Add locked dev dependencies with `uv`, not hand-edited lockfile entries.
2. Add reusable fake settings and upstream transport fixtures with client/session cleanup.
3. Cover the current three tool names, representative successful calls, invalid/missing bearer,
   invalid inputs, upstream 403/404/timeout/malformed responses, and MCP error envelopes.
4. Document the test command and separation of opt-in synthetic live checks.

## 6. Acceptance criteria and traceability

| Criterion | Given / when / then | Requirement | Evidence |
|---|---|---|---|
| AC-001 | Given no `.env` or Docker, when the default suite runs, then it passes without network access. | REQ-001 | Pass: fake settings disable `.env` loading, all HTTP clients use mock or ASGI transport, and 10 tests pass. |
| AC-002 | Given fake Redmine responses, when REST and MCP calls run, then catalog, auth, data, and error behavior match current contracts. | REQ-002 | Pass: REST and MCP assertions in `tests/test_offline_baseline.py`; 10 tests pass. |

## 7. Test plan and execution record

BASE-001: credential-free offline suite. BASE-002: REST success/error/auth cases. BASE-003:
MCP discovery, invocation, auth, and error envelope. BASE-004: client/session cleanup. On
2026-09-30, `uv add --dev pytest pytest-asyncio` updated `pyproject.toml` and `uv.lock` together.
`uv run --frozen pytest` passed 10 tests in 0.92 seconds with one dependency deprecation
warning. `bash scripts/check.sh` passed Ruff lint, Ruff format (70 files), and mypy (32 source
files). `uv build` produced source and wheel distributions. `git diff --check` passed. MCP
discovery confirmed exactly the three existing operation names; invocation and REST contract
assertions passed within the 10 tests. These are offline mock results; no Docker, live Redmine,
or Inspector call was used. No CI or coverage threshold is part of this task.

## 8. Implementation and review record

Added locked pytest dependencies, `tests/conftest.py` with fake settings, an HTTPX MockTransport,
explicit ASGI lifespan and closed-client checks, and `tests/test_offline_baseline.py` with REST
and MCP SDK coverage. Updated `docs/testing-roadmap.md` with the default command and live-check
boundary. The initial suite failed due to async fixture registration and MCP result-shape
assumptions; these were corrected before the passing run. The suite does not claim live synthetic
Redmine behavior. Unrelated working-tree changes and the retired issue backlog were preserved.

## 9. Completion and handoff

- [x] Offline fixtures and baseline scenarios pass without secrets or network.
- [x] Dependency, documentation, and dashboard records are synchronized.

Final status: complete. Next action: none for this task.
