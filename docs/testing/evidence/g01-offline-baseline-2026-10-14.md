# G01: Current offline baseline

Date: 2026-10-14. Status: complete; current unit and integration baseline accepted.

## Assignment and tested source

The user explicitly assigned G01 from the
[coverage review plan](../../plans/testing-gap-plan-2026-10-14.md).
This authorizes the existing unit and integration suites, investigation/correction of
failures, and appropriate offline reruns. New scenario generation belongs to later packages.

Source revision: `2938733394a72ddf0fcfda7632a7a93bdd47a41f`.
At execution start, the working tree had an existing `README.md` edit, coverage/index
documentation edits and the untracked review plan. Runtime, test code, `pyproject.toml`
and `uv.lock` had no tracked differences from that revision.

Git Bash was launched outside the sandbox because its Windows shared-memory initialization
is denied inside the sandbox. Commands ran from the repository root using the existing
locked environment. The unit invocation rebuilt the local editable package; no dependency
or lockfile change was required.

Private logs and the source manifest are retained under ignored
`.local/testing/g01-2026-10-14/`. `tested-sources.sha256` fingerprints the tracked runtime,
tests, testing helpers, preparation entry point, project configuration and lockfile. Its hash:

```text
7ab210bc94908abfd8e80a34d6014e1547a207a54fb9d4f720ddba7fa775fcc6
```

The manifest also includes live helpers for source identification; their inclusion is not
evidence that E2E or administrative setup was executed.
After both runs, all manifest hashes still matched; runtime/tests/configuration remained
unchanged while the evidence and roadmap documentation were updated.

## Environment

| Component | Version |
| --- | --- |
| Python | 3.13.3 |
| uv | 0.12.21 |
| pytest | 9.1.1 |
| pytest-asyncio | 1.4.0 |
| MCP SDK | 1.30.0 |
| FastAPI-MCP | 0.4.0 |
| HTTPX | 0.28.1 |
| Pydantic | 2.13.5 |

## Commands and results

```bash
uv run --frozen pytest tests/unit -q
uv run --frozen pytest tests/integration -q
```

| Scope | Result | Pytest duration | Local log |
| --- | --- | --- | --- |
| Complete unit suite | 855 passed; 1 warning; exit 0 | 3.74 seconds | `unit.log` |
| Complete integration suite | 1,541 passed; 1 warning; exit 0 | 1,280.77 seconds (21 minutes 20 seconds) | `integration.log` |

Together, the two complete suites passed **2,396 cases**, with no failures, skips or xfails
reported. These were separate invocations against the same runtime/test source, not a single
combined pytest invocation. No failure required correction, so no focused or duplicate full
rerun was necessary. No test or runtime code was modified.

Each invocation reported the same `PydanticDeprecatedSince211` warning for the upstream
`BaseModel.__get_pydantic_core_schema__` hook. The initial uv invocation also reported
fallback from hardlinking to copying; dependency installation completed successfully.

## Regression scope and execution limits

The integration run includes the existing creation regression tests for exact payload,
caller credit, independent read-back, strict schema and undeclared fields. These address
the earlier reported six failures without reintroducing the SDK discovery-GET counting issue.
All passed in the complete integration run. It also passed the existing writer admission,
allowed operations and session isolation cases, including rotated keys, a second user with
native permissions, denied users, reader deployments and empty/explicit operation ceilings.
These are offline simulated native permissions, not live permission acceptance.

The unit run includes retired writer setting handling and strict creation inputs/services.
All passed. No failure occurred and no correction was needed. There are no failing node IDs
or failure tracebacks to hand off from these runs. The original six reported failures were
not reproduced on this revision with its existing corrections.

No E2E, Docker, seed/reset, Inspector, browser, deployment or coverage-measurement command
was run. No static-check pass is claimed by this test evidence. This baseline does not
close the G02..G08 scenario/infrastructure gaps or establish native acceptance of TOOL-040/041.
