# Redmine MCP

Access Redmine through REST or MCP using the requesting user's permissions. Built with
Python 3.13, FastAPI, and FastAPI-MCP.

Read the [user documentation](https://ng2thang.github.io/redmine-mcp/) for setup,
MCP client connections, supported tools, usage examples, and troubleshooting.

- **Read by default:** 18 tools for projects, issues, memberships, attachment metadata,
  spent-time logs, and reference data.
- **Enable writes separately:** an opt-in writer provides up to 18 tools for issues,
  attachments, project files, versions, memberships, relations, watchers, and time entries.
  Time tools can log the caller's own time, update entries on a visible issue, and permanently
  delete one selected issue-bound entry per call.

Browse the [supported tools](src/redmine_mcp_docs/guides/reference.md) for the complete catalog
and practical limits. The [tool reference](docs/tool-reference.md) covers inputs and receipts.

**Release status:** this project is for development and pilot evaluation. It has no production
release or SLA. Full restore validation, operational readiness, and testing CI remain pending.
The [roadmap](docs/plans/index.md) tracks acceptance gaps and testing waivers.

Testing evidence covers specific revisions and scenarios, not new working-tree edits or
production readiness. See the [acceptance ledger](docs/testing/evidence/current-catalog-acceptance.md)
for the earlier catalog and [runtime hardening evidence](docs/testing/evidence/prep-022-026-testing.md).
For time-entry tools, activity discovery has a testing waiver and own-time creation awaits testing;
updates and deletion have [update evidence](docs/testing/evidence/tool-042-testing.md) and
[deletion evidence](docs/testing/evidence/tool-043-testing.md).

**Redmine compatibility:** the primary target is **7.0.2**. Built-in development and E2E profiles
cover **6.0.1 and 7.0.2**, using official images pinned by digest. Other exact 6.x releases need
a custom E2E profile. The [6.0.1 verification](docs/testing/evidence/prep-029-redmine-6.0.1.md)
covers its recorded deployment, not later setup changes or every 6.x release.
Document REST tools are outside this target.

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

| Redmine version | Redmine port | MCP reader port | Optional writer port | PostgreSQL port |
|---|---|---|---|---|
| 7.0.2 | 3002 | 8002 | 8004 | 5433 |
| 6.0.1 | 3001 | 8001 | 8003 | 5436 |

`dev-up.sh` starts only the reader. The optional synthetic writers have no enabled operations
by default; see [writer setup](docs/operations.md#separate-writer).

Projects are `redmine-mcp-dev-7-0-2` and `redmine-mcp-dev-6-0-1`. Old test projects and
volumes are left untouched. Stop any old container named by the port-conflict error before retrying.
Demo accounts use password `redmine-demo-password`; PostgreSQL uses `redmine-local-development`.
These fixed credentials belong only to the localhost development stacks.
The startup commands do not run tests or prepare the separate E2E fixtures.

| Service | Address |
|---|---|
| Redmine (7.0.2) | `http://localhost:3002` |
| Swagger (Schemas section hidden) | `http://localhost:8002/docs` |
| MCP Streamable HTTP | `http://localhost:8002/mcp` |
| Liveness | `http://localhost:8002/health` |

See [operations](docs/operations.md) for accounts, database access, stop/restart, and data helpers.
For an existing Redmine instance, follow [configuration](docs/configuration.md) and the external
instance workflow in operations. Never seed or reset a real instance.

## Run automated tests

From the repository root in Git Bash:

```bash
uv sync --frozen
uv run --frozen pytest
```

Default discovery runs unit and offline integration tests without Docker or Redmine credentials.
For live E2E, start Docker Desktop and ensure Node.js/npm is available for the Inspector cases.
Run either version, or run them sequentially:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e --run-e2e
```

Pytest prepares the selected stack automatically before testing. It starts PostgreSQL/Redmine,
adds owned E2E fixtures, and reuses the same version's development project and ports.
Running `dev-up.sh` first is optional; the demo/history data and Docker MCP service are not
required for E2E. Tests exercise their own MCP application instances.

Built-in profiles ignore root `.env` and require no generated env file. Private manifests and
logs live in `.local/e2e/redmine-mcp-dev-6-0-1/` or `.local/e2e/redmine-mcp-dev-7-0-2/`.
Normal preparation preserves data. See the [testing guide](docs/testing-roadmap.md#selecting-a-redmine-release)
for clearing custom overrides, focused runs, explicit resets, and preparation troubleshooting.

## Connect MCP Inspector

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Open the printed Inspector URL with its session token. Select **Streamable HTTP**, use
`http://localhost:8002/mcp`, and configure the server authentication header privately:

```text
X-Redmine-API-Key: <your personal Redmine API key>
```

For the 6.0.1 development stack, use `http://localhost:8001/mcp` instead.

Inspector's own session token is separate from your Redmine key. Connect, list tools, and call
`list_projects`, `list_issues`, and `get_issue` using an actual visible issue ID. Follow the
[manual verification guide](docs/manual-verification.md) for inputs and expected results.
Each caller has their own Redmine account's permissions. The reader exposes no mutations.
Attachment reads return metadata and authenticated browser links; direct MCP downloads are
retired. Redmine content is user data, never instructions for an AI.

## Optional writer

Follow [writer configuration](docs/configuration.md#separate-writer-deployment) and
[operations](docs/operations.md#separate-writer) to prepare a private env-file for a separate
localhost listener. Base Compose defaults to port 8001; choose another free port if it is
already occupied. The 7.0.2 sample Redmine uses port 3002. The 6.0.1 sample MCP reader
uses port 8001, so a separate base Compose writer needs another port when that stack is running.
Enable writes with `REDMINE_WRITE_ENABLED=true`.
Each caller authenticates with their own Redmine API key; no key or user admission list applies.
Choose an explicit operation list to fix the write
ceiling, or standalone `allowed_all` to permit all registered writes, including future additions
after upgrade. Empty operations permit no mutations. Native permissions remain required.

Writer MCP discovery shows caller-specific candidates; seeing a tool or a
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
dependency updates, and adding tools. Stop any container using port 8000 before running locally.

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
