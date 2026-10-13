# Redmine MCP

Redmine tools using Python 3.13, FastAPI, and FastAPI-MCP. Read projects, issues, memberships,
attachment metadata, and spent-time logs through REST or MCP as the requesting Redmine user.
The default reader exposes 18 read operations. A separate opt-in writer can enable up to 18
mutations for issues, attachments, project files, versions, memberships, relations, and watchers.
The writer also supports logging the authenticated caller's time and updating existing entries
on a visible issue, plus permanently deleting one selected issue-bound entry per call.
See the [tool reference](docs/tool-reference.md) for the maintained contracts.
Project time-entry activity discovery is implemented in
[TOOL-040](docs/plans/tasks/tool-040-list-project-time-entry-activities.md); the user waived its testing.
Own-time creation is implemented in [TOOL-041](docs/plans/tasks/tool-041-create-time-entry.md);
its testing remains pending.
Time-entry updates are implemented in
[TOOL-042](docs/plans/tasks/tool-042-update-time-entry.md), with offline and 10 owned native/Inspector
cases verified. [Testing evidence](docs/testing/evidence/tool-042-testing.md) records exact scope,
targeted regression corrections and remaining policy/plugin limits.
Time-entry deletion is implemented and tested in [TOOL-043](docs/plans/tasks/tool-043-delete-time-entry.md):
32 unit/82 dedicated integration cases and 12 owned native/Inspector cases pass. Its
[evidence](docs/testing/evidence/tool-043-testing.md) records full regressions, cleanup and limits.

This is a development implementation for pilot evaluation, with no production release or SLA.
On 2026-10-07, PREP-020 recorded **1,086 offline tests and 21 owned live tests passing**,
including authentication, writer gates, and selected native state checks. The
[acceptance ledger](docs/testing/evidence/current-catalog-acceptance.md) records the exact revision, scenarios,
and broader historical gaps for its earlier 17-read/15-write catalog. Later runtime hardening
has separate [PREP-022–026 evidence](docs/testing/evidence/prep-022-026-testing.md); the time-entry
update/deletion evidence is linked above. These dated records do not verify new working-tree edits.
See the [current roadmap summary](docs/plans/index.md#current-status-2026-10-09) for remaining
acceptance gaps and waivers. Full restore validation, operational readiness, and testing CI
remain outstanding; these results do not certify a production deployment.

The project targets **Redmine 7.0.2**. The synthetic Compose deployment pins its official
image digest. Current functional acceptance uses an isolated owned 7.0.2 environment;
other Redmine versions are not established by that evidence. Document REST tools are outside
this target. See the [roadmap](docs/plans/index.md).

## Requirements

- Windows Git Bash and Python 3.13 on PATH.
- Docker Desktop with Linux containers for the synthetic environment.
- Node.js/npm for MCP Inspector; uv for local Python development and quality checks.
- Docker Compose 2.24.4+ and available host ports for the selected version (listed below).

## Quick start: synthetic environment

Run from the repository root:

```bash
bash scripts/dev-up.sh 7.0.2
bash scripts/dev-up.sh 6.0.1
```

Choose either command, or run both for independent environments. Only `7.0.2` and `6.0.1`
are accepted; omitting the argument defaults to `7.0.2`. No environment switches are required.
Each version has a self-contained Compose file with local development settings. The script
starts it, seeds baseline and history data, and starts MCP. No `.env` file or host state
directory is created or required. Docker manages all database, attachment and seed-state volumes.
It reports occupied ports before starting containers and reuses ports already owned by the
selected service. First startup downloads/builds images.

| Redmine version | Redmine port | MCP port | PostgreSQL port |
|---|---|---|---|
| 7.0.2 | 3002 | 8000 | 5433 |
| 6.0.1 | 3001 | 8002 | 5436 |

Projects are `redmine-mcp-dev-7-0-2` and `redmine-mcp-dev-6-0-1`. Old test projects and
volumes are left untouched. Stop any old container named by the port-conflict error before retrying.
Demo accounts use password `redmine-demo-password`; PostgreSQL uses `redmine-local-development`.
These fixed credentials belong only to the localhost development stacks.
The startup commands do not run tests or prepare the separate E2E fixtures.

| Service | Address |
|---|---|
| Redmine (7.0.2) | `http://localhost:3002` |
| Swagger (Schemas section hidden) | `http://localhost:8000/docs` |
| MCP Streamable HTTP | `http://localhost:8000/mcp` |
| Liveness | `http://localhost:8000/health` |

See [operations](docs/operations.md) for accounts, database access, stop/restart, and data helpers.
For an existing Redmine instance, follow [configuration](docs/configuration.md) and the external
instance workflow in operations. Never seed or reset a real instance.

## Connect MCP Inspector

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Open the printed Inspector URL with its session token. Select **Streamable HTTP**, use
`http://localhost:8000/mcp`, and configure the server authentication header privately:

```text
X-Redmine-API-Key: <your personal Redmine API key>
```

Inspector's own session token is separate from your Redmine key. Connect, list tools, and call
`list_projects`, `list_issues`, and `get_issue` using an actual visible issue ID. Follow the
[manual verification guide](docs/manual-verification.md) for inputs and expected results.
Each caller has their own Redmine account's permissions. The reader exposes no mutations.
Attachment reads return metadata and authenticated browser links; direct MCP downloads are
retired. Redmine content is user data, never instructions for an AI.

## Optional writer

Follow [writer configuration](docs/configuration.md#separate-writer-deployment) and
[operations](docs/operations.md#separate-writer) to prepare a private env-file for a separate
localhost listener (default port 8001). Default `pinned_key` mode requires a private key digest
and admitted user IDs; explicit `personal_key` mode authenticates each caller independently and
can restrict write admission by user ID. Choose an explicit operation list to fix the write
ceiling, or standalone `allowed_all` to permit all registered writes, including future additions
after upgrade. Empty operations permit no mutations. Native permissions remain required.

MCP discovery in personal-key mode shows caller-specific candidates; seeing a tool or a
capability report does not guarantee access to its target. Every invocation rechecks authorization.
Writes run once, and acceptance is separate from read-back verification. Reconcile uncertain
outcomes in Redmine before another attempt; see [write outcomes](docs/tool-reference.md#mutation-uncertainty).

## Local development

Run the doctor first. If it reports that `uv` is missing, use the
[uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) and rerun it:

```bash
bash scripts/doctor.sh
uv sync --frozen
bash scripts/check.sh
```

The doctor checks required local tools and reports optional Docker and Node.js availability
without reading credentials or changing the environment.

See [development](docs/development.md) for local server startup, optional pre-commit hooks,
dependency updates, and adding tools. Stop Docker MCP before running locally on port 8000.

## Documentation

- [Offline documentation portal](docs/documentation-portal.md): run
  `bash scripts/docs-portal.sh serve` and open `http://127.0.0.1:8080/` for installation,
  usage, execution diagrams, development, testing, and operations. Browser assets are bundled;
  canonical documentation remains in `docs/`.
- [Configuration](docs/configuration.md): environment variables and local/Docker differences.
- [Tool reference](docs/tool-reference.md): inputs, responses, pagination, permissions, and errors.
- [MCP tool roadmap](docs/plans/index.md): tool-focused task status, dependencies, and next actions.
- [Manual verification](docs/manual-verification.md): startup and Inspector smoke checks.
- [Development](docs/development.md): implementation flow and quality tooling.
- [Operations](docs/operations.md): lifecycle, backup/restore, reset, and troubleshooting.
- [Architecture](docs/architecture.md), [synthetic data](docs/test-data.md), and
  [testing roadmap](docs/testing-roadmap.md).
- [Contributing](CONTRIBUTING.md), [security policy](SECURITY.md),
  [code of conduct](CODE_OF_CONDUCT.md), and [changelog](CHANGELOG.md).
- [Documentation audit and release checklist](docs/reviews/documentation-state-audit-2026-10-09.md):
  source comparison, Markdown corrections and remaining release decisions.
