# Testing and evidence

Testing is described here for a separately authorized verification assignment. Reading these
instructions or serving this portal does not execute tests, prepare fixtures, start Inspector,
or authorize live requests.

## Three layers

| Layer | Location | Purpose and environment |
| --- | --- | --- |
| Unit | `tests/unit/` | Models, policies and services using fake ports |
| Offline integration | `tests/integration/` | REST/MCP contracts with mocked Redmine and internal ASGI |
| Live E2E | `tests/e2e/` | Explicitly selected cases against the owned 6.0.1 or 7.0.2 development stack |

Default pytest discovery selects only the two offline layers. Live E2E requires `--run-e2e`,
owned pinned fixtures, and the documented preparation/admission checks. Do not substitute a
shared Redmine instance or a real customer environment.

## Commands for an authorized assignment

### Registered tool coverage

`tests/e2e/test_mcp_tool_lifecycles.py` adds 22 cases covering the 36 registered MCP tools:
18 independent reader scenarios and four write lifecycles covering all 18 writes. Reader
cases compare caller-visible IDs and selected fields with native Redmine. Write cases check
receipts and resulting native state for issues/notes, relations/watchers, files/attachments,
time entries, versions and memberships. Owned fixtures clean up disposable resources.

These additions have not yet been executed on 6.0.1 or 7.0.2. They supplement the existing
permission, visibility, retry and Inspector cases; tool coverage does not imply exhaustive
argument or permission coverage. The retired `download_attachment` is outside the catalog.
The MCP SDK uses the application's existing in-process ASGI transport with real requests
to the selected Redmine container. Run cases sequentially rather than with parallel workers.

For an authorized focused run:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e/test_mcp_tool_lifecycles.py --run-e2e
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e/test_mcp_tool_lifecycles.py --run-e2e
```

See the [coverage matrix](../docs/plans/testing-coverage.md#mcp-catalog-lifecycle-additions)
for the mapping from tool names to cases and assertions.

### Layer and full-suite commands

Run from Git Bash at the repository root:

```bash
uv sync --frozen
uv run --frozen pytest tests/unit
uv run --frozen pytest tests/integration
uv run --frozen pytest
```

For an authorized live run, start Docker Desktop with Linux containers. Use Docker Compose
2.24.4+ and Node.js/npm for the Inspector cases. Run either version, or run both sequentially:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e --run-e2e
```

Default E2E selection is 7.0.2. Pytest automatically runs
`uv run --frozen python scripts/prepare-e2e.py` once before the selected live cases.
It starts PostgreSQL/Redmine, checks the selected image, version, ownership, and mounts,
then creates or reuses owned fixture data. Preparation failure stops pytest before testing.
Normal preparation does not reset the database. Test cases mutate and clean up disposable
resources while retaining baseline fixtures for subsequent runs.

Running `dev-up.sh` first is optional. E2E uses the same projects and ports as development,
without requiring Docker MCP or the demo/history datasets. Tests use their own MCP application
instances. Built-in profiles use no env file and ignore root `.env`.

| Version | Compose project | Redmine address | Private manifests and logs |
| --- | --- | --- | --- |
| 6.0.1 | `redmine-mcp-dev-6-0-1` | `http://127.0.0.1:3001` | `.local/e2e/redmine-mcp-dev-6-0-1/` |
| 7.0.2 | `redmine-mcp-dev-7-0-2` | `http://127.0.0.1:8001` | `.local/e2e/redmine-mcp-dev-7-0-2/` |

The E2E overlay mounts the selected private directory at `/e2e-state`. Development seed
manifests stay in the separate `seed_state` Docker volume at `/seed-state`.
`REDMINE_E2E_VERSION` selects tests; `REDMINE_TEST_VERSION` selects development lifecycle
helpers. The E2E launcher aligns its internal helper version automatically.

If you previously exported custom profile settings, clear them before using built-in defaults:

```bash
unset REDMINE_E2E_COMPOSE_FILE REDMINE_E2E_COMPOSE_PROJECT REDMINE_E2E_ENV_FILE
unset REDMINE_E2E_PORT REDMINE_E2E_IMAGE
```

For a focused live run, preparation remains automatic:

```bash
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e/test_reporting_acceptance.py --run-e2e -q
```

Standalone Inspector/browser scripts require explicit preparation with the same version:

```bash
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/prepare-e2e.py
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/verify-reporting-inspector.py
```

Run preparation again after development startup recreates Redmine without the E2E overlay.
Offline runs and `--collect-only` do not prepare Docker. Additional exact 6.x.x releases
require a complete custom profile; see the linked roadmap for its env-file and image-pin contract.

## Reset and preparation failures

For a deliberate fresh E2E start, discard only the selected disposable stack:

```bash
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/prepare-e2e.py --reset
```

Use `6.0.1` for that version. This stops/removes the selected containers, deletes its
marked database/files volumes and checked host E2E state, then prepares E2E fixtures.
It retains development seed and backup volumes; their seed manifests become stale when
the database is replaced. Development reset has different boundaries: it also removes
named seed/E2E-state volumes, reseeds demo/history data, and retains host E2E evidence.
That retained E2E manifest needs explicit E2E reset before reuse against the new database.
See [operations](../docs/operations.md#seed-and-reset) before choosing a reset workflow.

For `E2E preparation failed`, inspect the selected private `pytest-prepare.log` first.
Later `compose-up.log` and `seed.log` may be absent if setup stopped early. TOOL-042/043
fixture failures have separate `tool042-<action>.log` and `tool043-<action>.log` files.
Logs may contain personal API keys; do not paste them unredacted into shared reports.
See [setup troubleshooting](troubleshooting.md#setup-and-testing) for port conflicts,
custom env-file errors, and the existing Pydantic warning.

Consult the [testing roadmap](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing-roadmap.md) for dependency/fixture prerequisites,
cleanup ownership, supplemental verification, and execution boundaries. Inspector input and
expected results are in [manual verification](../docs/manual-verification.md).

Offline tests of supplemental helpers must replace both `ROOT` and the separately imported
`STATE` with temporary paths and mock network/process calls. Changing `ROOT` alone does
not redirect Inspector credentials out of the real private E2E directory.

## Interpret existing evidence

Evidence belongs to its recorded revision, environment, scenario set, and date. A historical
passing count does not verify a new working tree or close pending acceptance automatically.
The dated 50-case 6.0.1 result used the earlier `redmine-mcp-test-6-0-1` layout; it does
not establish acceptance of the later self-contained `redmine-mcp-dev-*` setup refactor.

Use the [current task summary](../docs/plans/index.md),
[coverage matrix](../docs/plans/testing-coverage.md), and
[catalog acceptance ledger](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing/evidence/current-catalog-acceptance.md) together.
Later preparation, retry, and time-entry changes have their own evidence linked from
[Contributors](contributors.md#testing-and-evidence).
Time-entry creation acceptance remains pending, and activity discovery testing was waived in
the documented baseline. Follow the canonical roadmap for subsequent updates.

Coverage thresholds, testing CI, and broader operational/recovery readiness remain deferred.
The portal preserves the existing evidence rather than presenting a new acceptance result.

## Verify the portal separately

The [portal checklist](verification.md) covers offline assets, navigation, diagrams, export
boundaries, and static deployment. It needs no Redmine credentials or test fixtures. The
implementation handoff does not claim those manual checks were performed.
