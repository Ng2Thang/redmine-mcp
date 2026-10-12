# Testing roadmap

### Issue time-entry deletion acceptance

The user separately assigned TOOL-043 testing on 2026-10-08. [Deletion evidence](testing/evidence/tool-043-testing.md)
records 32 unit cases in `tests/unit/test_time_entry_deletions.py`, 82 dedicated integration
cases in `tests/integration/test_time_entry_deletions.py`, four current-writer matrix additions,
and 1889 clean full offline regression passes. Tests exposed and fixed ignored undeclared
MCP arguments; deletion now explicitly rejects them. Native acceptance in
`tests/e2e/test_time_entry_delete_acceptance.py` passed 11 cases plus one added no-issue-view
permission case, including Inspector 2.8.0. Owned storage absence/control/totals, role boundaries,
duplicate/independent-call receipts, committed faults and moved-entry race have passing evidence.
Exact cleanup reports zero projects/entries/users/roles/activities and no private task ledger or
Inspector config remains. Scoped checks pass; injection/policy/plugin limits remain disclosed.
No final single 12-case native rerun is claimed. TOOL-041 creation remains a separate task.


The user assigned TOOL-042 testing on 2026-10-08.
[Time-entry update evidence](testing/evidence/tool-042-testing.md) records 61 unit/99 dedicated
integration cases, shared catalog fixture updates, 10 owned Redmine 7.0.2/Inspector cases and
verified zero-resource cleanup. Full offline regressions had 1,755 passes and one older reader
argument failure; its corrected rerun and seven later edge cases pass. The record does not
claim a clean full-suite rerun after final small additions/corrections. Tests use current native
settings without changing shared roles, global settings, plugins or the shared 6.0.5 server.
Broader policy/plugin/race variants and unrelated repository Ruff debt remain disclosed.

The user authorized testing for prep-022 through prep-026 on 2026-10-07.
[Preparation regression testing](testing/evidence/prep-022-026-testing.md) records the new tests,
runtime defects and corrections, owned live/Inspector results, cleanup and final offline evidence.

The user subsequently assigned PREP-027 testing on 2026-10-07.
[Read retry verification](testing/evidence/prep-027-testing.md) records deterministic retry,
budget/deadline, cancellation, identity, REST/MCP and writer receipt scenarios, adapted reader
error contracts, and read-only owned live/Inspector compatibility. Fault injection and mutations
are covered offline; the selected live checks perform zero mutations.

Current verification has three layers: unit tests, offline REST/MCP integration tests, and opt-in
live E2E against an isolated owned Redmine 7.0.2 environment. Testing CI and percentage coverage
thresholds remain deferred. The [coverage matrix](plans/testing-coverage.md) maps every current
operation and common runtime scenario to its task and selected evidence.

On 2026-10-07, [PREP-020](plans/tasks/prep-020-current-catalog-acceptance.md) reconciled the
32-operation functional catalog: **1,086 offline and 21 owned Redmine 7.0.2 live tests passed**.
The [PREP-020 ledger](testing/evidence/current-catalog-acceptance.md) records the source revision and exact
evidence, including versions, memberships, `allowed_all`, shared write uncertainty and Inspector
catalog/read compatibility. Broader historical variants remain in H1..H6; counts do not close
them automatically. No tests or runtime checks were rerun for the PREP-021 documentation update.
The registered catalog now contains 18 reads and 18 writes; consult the
[current roadmap summary](plans/index.md#current-status-2026-10-09) for later evidence and
the still-pending or waived acceptance stages. Test counts do not automatically close those gaps.

## Three-phase implementation

| Phase | Directory | Task | Environment |
|---|---|---|---|
| Unit | `tests/unit/` | [prep-016](plans/tasks/prep-016-unit-testing.md) | Fake ports, models and policies |
| Integration | `tests/integration/` | [prep-017](plans/tasks/prep-017-offline-integration-testing.md) | Mocked Redmine and in-process REST/MCP |
| E2E | `tests/e2e/` | [prep-018](plans/tasks/prep-018-live-e2e-testing.md) | Owned selected Redmine 6.x.x or 7.0.2 and PostgreSQL |

The user authorized implementation and execution on 2026-10-05. Future coding-only assignments
still require separate testing authorization. Run from Git Bash within an authorized assignment:

```bash
uv run --frozen pytest tests/unit
uv run --frozen pytest tests/integration
uv run --frozen pytest
bash scripts/check.sh
```

Default discovery selects only unit and integration. Explicit E2E selection without `--run-e2e`
exits with usage error before fixtures run. Offline fixtures disable dotenv loading, clear inherited
Redmine settings and reject real HTTPX network dispatch. Shared data and MCP session helpers are
in `tests/helpers.py`; collected test modules do not provide helpers to other modules.

### Isolated live environment

The pre-existing shared synthetic environment runs 6.0.5. Preparation creates a separate
`redmine-mcp-e2e` Compose project on localhost port 3001 with owned database/files volumes,
preserving existing containers, configuration and data. Existing E2E volumes must match ownership
and version labels. Preparation creates fixtures; it is not a read-only smoke check.

```bash
uv run --frozen pytest tests/e2e --run-e2e
uv run --frozen python scripts/verify-e2e-supplement.py
```

Pytest automatically runs `uv run --frozen python scripts/prepare-e2e.py` once per
session before any selected E2E test or its fixtures run. Docker Desktop and `uv` on
`PATH` are required. Preparation reuses the selected owned environment and seeds its
fixtures; it does not reset volumes. A preparation failure stops the session before test
execution. Private subprocess output is saved as `pytest-prepare.log` in the selected
environment's state directory; fixture seed output remains in `seed.log`.

Offline runs, collection-only runs, and runs with no selected E2E tests do not prepare
Docker. E2E selection without `--run-e2e` is still rejected before preparation.
The preparation command remains available separately, for example before running only
the supplemental Inspector/browser scripts.

### Selecting a Redmine release

E2E accepts exact stable `6.x.x` releases and `7.0.2` (the default). Other 7.x versions,
older majors, floating tags, and prereleases are rejected. This is a configuration range,
not evidence that every release has passed the suite. The Docker tag must exist.

For Redmine 6.0.1, use Git Bash from the repository root with Docker Desktop running:

```bash
export REDMINE_E2E_VERSION=6.0.1
uv run --frozen pytest tests/e2e --run-e2e
# Optional Inspector and authenticated browser checks:
uv run --frozen python scripts/verify-e2e-supplement.py
```

Keep the exported selection for pytest, preparation, and supplemental scripts. Automatic preparation
creates and seeds an isolated environment; it does not connect to an arbitrary external
Redmine or use the root `.env`. The 6.0.1 project is `redmine-mcp-e2e-6-0-1`, private state
is `.local/testing-e2e-6-0-1/`, and Redmine listens on `127.0.0.1:3002`. Other 6.x releases
use the same naming pattern and default port 3002. Set `REDMINE_E2E_PORT` to a free port
between 1024 and 65535 before preparation and keep it set for every subsequent command.
This also allows different versions to coexist. The existing 7.0.2 project, state directory,
and default port 3001 remain unchanged. Neither environment uses the development stack's data.

Preparation reuses repository digest pins for 6.0.1 and 7.0.2. For another 6.x release it
pulls `redmine:<version>` once, resolves its repository digest, and saves the immutable image
reference in that release's private `compose.json`. Later preparation reuses that pin.
An optional `REDMINE_E2E_IMAGE=redmine:<version>[-variant]@sha256:<64-hex-digest>` supplies
an explicit official image pin; its tag must match the selected release. Native Ruby guards
also verify the running Redmine version before fixture inspection or mutation. Manifests
and volumes from another release are refused; no automatic reset or volume migration occurs.

To return to the default selection in the same shell:

```bash
unset REDMINE_E2E_VERSION REDMINE_E2E_PORT REDMINE_E2E_IMAGE
```

Tag controls now use the selected owned E2E instance rather than the legacy shared 6.0.5
stack. Positive tag scenarios require working native tag filtering and an existing
`notification` tag fixture; unsupported or absent controls are explicitly skipped.
Preparation does not install tag plugins. A skipped tag case is not compatibility acceptance.

The version-selection change has not been executed against Docker or pytest. Before recording
compatibility, run preparation, the selected E2E suite, cleanup review, and the optional
Inspector/browser checks separately for each intended release. Existing assertions about
permissions and resulting state remain in place and may expose version differences.

Preflight verifies the image pin, synthetic markers, volume ownership, private manifest and
native project identifiers before mutation. Ordinary personal keys exercise the separately
configured writer application. Administrative fixture inspection and cleanup stay separate;
the MCP application never accesses the database directly. Keys and generated configuration remain
in ignored `.local/testing-e2e/`, never command arguments or committed artifacts.

Assertions distinguish write acceptance from matched state, including accepted but ignored fields
under author/tracker restrictions. Uncertain outcomes require reconciliation before a retry.
Cleanup affects only created resources; restored fixture subjects or role grants can leave owned
journal history. Baseline fixtures and containers remain available for reruns; no reset is automatic.

The supplemental script starts a temporary localhost application on port 18081, runs Inspector
2.8.0 discovery and a read call, then uses installed Edge/Node to download an attachment through
its authenticated metadata link and compare content. It stops its application/browser and removes
the created attachment. JSON credential configs, browser profiles and redacted results stay ignored.
For interactive supplemental review:

```bash
uv run --frozen uvicorn tests.e2e.server:create_app --factory --host 127.0.0.1 --port 18081
npx @modelcontextprotocol/inspector@2.8.0
```

Connect privately to `http://127.0.0.1:18081/mcp` with an owned ordinary user's key.
Redmine is at `http://127.0.0.1:3001`; never put keys into URLs or screenshots.

## Baseline history and further work

The [tool workflow](workflows/redmine-tools.md) requires an offline automated
baseline before dependent reader-tool implementation. The baseline uses locked pytest and
pytest-asyncio dependencies, fake settings without `.env`, HTTPX mock/ASGI transports, and MCP SDK
session checks. Run it from Git Bash without Docker or credentials:

```bash
uv run --frozen pytest
```

The historical suite covered the then-current eleven reader tools at the REST boundary and MCP discovery,
invocation, authentication, validation, and error envelopes. Authorized prep-004 work also
covers concurrent identities, bounded upstream reads, readiness, and resource cleanup.
See [the dated acceptance evidence](testing/evidence/prep-004-verification.md) for actual results and
remaining live fixture gaps. Opt-in live synthetic checks remain separate;
coverage thresholds and testing CI remain separate decisions.

Current write verification uses a separate restricted synthetic writer, disposable task-owned
resources, resulting-state checks and isolated cleanup. Existing reader credentials must remain
read-only. See the [MCP tool dashboard](plans/index.md) for dependency and scenario records.

The earlier backlog below identifies areas for further coverage, rather than declaring every
scenario untested. Consult the current ledger and original owner tasks before assigning a gap:

- Unit: service filters/defaults/pagination with fake gateways.
- Integration: mapping, upstream errors, TLS/timeouts, personal-key authentication and forwarding.
- MCP: schemas/names, error responses, shutdown and session cleanup.
- E2E: restricted projects/private issues/private journals, filters and pagination.
- Seed: reruns, interrupted writes, expected counts and access boundaries.
- Backup/restore: fresh volumes, IDs/history/permissions, attachment checksums,
  incompatible/incomplete snapshots, failure recovery.
- Packaging: isolated wheel, non-root image, import boundaries and CI.

Successful basic calls do not establish production readiness.
Operational readiness, audit/metrics, CI/package and owned recovery acceptance remain deferred
outside the current local-development roadmap; final release review remains prep-009.

## Per-user authentication scenarios for a separately authorized test stage

For future coding-only assignments, do not create or run tests without testing authorization.
The three-phase assignment above explicitly authorizes current verification. These original
authentication handoff scenarios remain useful traceability requirements:

- Two distinct keys resolve different Redmine user IDs. Interleaved and concurrent calls forward
  each key only to its own `/users/current.json` and resource requests; `me` remains upstream.
- Missing, blank, duplicate, and rejected keys return 401 before a resource request. MCP
  connection and tool discovery reject invalid keys. No key appears in tool arguments or errors.
- A malformed current-user response, timeout, transport error, and later key revocation yield
  sanitized 502, 504, 502, and 401 responses respectively.
- Visibility scope is `requesting_redmine_user`; existing operation IDs, inputs, pagination, and
  response wrappers remain stable. The write gate remains closed on reader deployments.

