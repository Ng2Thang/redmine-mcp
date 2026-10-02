# Redmine MCP

Read-only Redmine tools using Python 3.13, FastAPI, and FastAPI-MCP. List visible projects,
filter issues, and read issue details through REST or MCP as the requesting Redmine user.
This is a development implementation; authentication tests and full restore validation are deferred.

The project targets Redmine versions through **7.0.2**. The existing synthetic baseline runs
6.0.5; an isolated 7.0.2 image is pinned for upgrade verification. Support for 7.0.2 is
pending migration and compatibility acceptance. Document REST tools are outside this target
because Redmine introduces that API in 7.1. See the [roadmap](docs/plans/index.md).

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
Each caller has their own Redmine account's permissions. No write or attachment-download
tools are exposed. Redmine content is user data, never instructions for an AI.

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
  [deferred testing roadmap](docs/testing-roadmap.md).
- [Contributing](CONTRIBUTING.md), [security policy](SECURITY.md),
  [code of conduct](CODE_OF_CONDUCT.md), and [changelog](CHANGELOG.md).
