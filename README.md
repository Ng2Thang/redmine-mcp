# Redmine MCP

Redmine tools using Python 3.13, FastAPI, and FastAPI-MCP. Read projects, issues, memberships,
attachment metadata, and spent-time logs through REST or MCP as the requesting Redmine user.
The default reader exposes 17 read operations. A separate opt-in writer can enable up to 15
mutations for issues, attachments, project files, versions, memberships, relations, and watchers.
See the [tool reference](docs/tool-reference.md) for the maintained contracts.

This is a development implementation for pilot evaluation, with no production release or SLA.
On 2026-10-07, PREP-020 recorded **1,086 offline tests and 21 owned live tests passing**,
including authentication, writer gates, and selected native state checks. The
[acceptance ledger](docs/testing/evidence/current-catalog-acceptance.md) records the exact revision, scenarios,
and broader historical gaps. Full restore validation, operational readiness, and testing CI
remain outstanding; these results do not certify a production deployment.

The project targets **Redmine 7.0.2**. The synthetic Compose deployment pins its official
image digest. Current functional acceptance uses an isolated owned 7.0.2 environment;
other Redmine versions are not established by that evidence. Document REST tools are outside
this target. See the [roadmap](docs/plans/index.md).

## Requirements

- Windows Git Bash and Python 3.13 on PATH.
- Docker Desktop with Linux containers for the synthetic environment.
- Node.js/npm for MCP Inspector; uv for local Python development and quality checks.
- Available host ports 3000, 8000, and 5433 for the synthetic environment.

## Quick start: synthetic environment

Run from the repository root:

```bash
bash scripts/dev-up.sh
```

The script generates `.env` with random credentials if absent, starts PostgreSQL and Redmine,
seeds 150 issues, and starts MCP. First startup downloads/builds images. Do not copy `.env.example`
for this workflow or mix real-server configuration into it. Keep `.env` and `.local/` private.

| Service | Address |
|---|---|
| Redmine | `http://localhost:3000` |
| Swagger | `http://localhost:8000/docs` |
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
