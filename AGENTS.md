# Repository Guidelines

## Project Structure & Architecture

Runtime code lives in `src/redmine_mcp/`. Features under `features/projects/` and
`features/issues/` contain models, Protocol ports, services, and routers. Redmine
adapters belong in `integrations/redmine/`; `bootstrap.py` wires dependencies.
Keep the flow router → service → port → gateway. Services must not import FastAPI
or HTTPX. MCP reuses REST routes and never accesses PostgreSQL directly.

`deploy/` contains Docker definitions; `scripts/` contains Git Bash helpers;
`tools/seed/` generates synthetic data. Documentation lives in `docs/`.
Generated credentials, manifests, attachments in snapshots, and dumps belong in
ignored `.local/`. No automated test directory currently exists.

## Development & Build Commands

Run commands from the repository root using Git Bash on Windows:

```bash
bash scripts/doctor.sh                  # Check local prerequisites before implementation
uv sync --frozen                         # Install locked dependencies
bash scripts/check.sh                    # Run lint, formatting, and type checks
uv build                                # Build source and wheel distributions
uv run uvicorn redmine_mcp.app:create_app --factory --reload
bash scripts/dev-up.sh                   # Start Docker and seed sample data
uv run ruff check .                      # Lint code and imports
uv run ruff format --check .             # Check formatting
uv run mypy src                         # Check runtime types
npx @modelcontextprotocol/inspector@2.8.0 # Inspect MCP tools
```

Stop the Docker MCP service before running locally on port 8000.

## Coding Style & Naming

Use Python 3.13, four-space indentation, explicit type hints, and a 100-character
line limit. Use `snake_case` for modules/functions and `PascalCase` for classes.
Use async HTTP calls and lifespan-managed clients. Keep tool `operation_id` values
stable and register new tools explicitly in the MCP allowlist. Commit dependency
changes with `uv.lock`. All Markdown must be English; provide Bash commands only.

## Testing Guidelines

The tool workflow requires automated testing as a prerequisite for future
reader capabilities; its baseline is not implemented yet. Coverage thresholds and
testing CI remain deferred. Coding-without-tests assignments must hand off testing
dependencies, fixtures, and execution separately. For relevant changes, check service startup and call
the affected tools through Inspector. Record verification limitations; follow
`docs/testing-roadmap.md` when testing work begins.
Track proposed MCP capabilities and task status in `docs/plans/index.md`.

Pre-commit hooks are opt-in; do not install them automatically. See `CONTRIBUTING.md`,
`docs/development.md`, and `docs/manual-verification.md` for contributor rules and checks.

## Commits & Pull Requests

There are no existing commits establishing a convention. Use concise imperative
subjects, such as `Add issue status filtering`. PRs should describe behavior,
reference applicable issues, list validation performed, and disclose deferred checks.
Update documentation when configuration or public tool contracts change.

## Security & Configuration

Keep API keys, bearer tokens, and snapshots out of Git and logs. Current tools remain
read-only. Future issue writes are authorized only through an explicitly enabled
separate writer deployment with its own restricted key/token and required workflow
prerequisites; administrative seeding stays separate. Bind published ports to localhost;
PostgreSQL uses host port 5433. Reset/restore helpers must validate the synthetic
environment marker before replacing data.
