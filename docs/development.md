# Development

## Environment

Use Python 3.13, uv, and Git Bash on Windows. `.python-version` selects the Python minor version;
`pyproject.toml` restricts runtime compatibility to 3.13. Run from the repository root:

```bash
uv sync --frozen
bash scripts/check.sh
```

Configure a reachable Redmine instance as described in [configuration](configuration.md).
Stop the Docker MCP service before starting locally on port 8000; see [operations](operations.md).

```bash
uv run --frozen uvicorn redmine_mcp.app:create_app --factory --host 127.0.0.1 --port 8000 --reload --no-access-log
```

Settings load at app creation. HTTP clients are managed by application lifespan; imports must not
read credentials or contact upstream services. See the [architecture](architecture.md).

## Quality checks

`scripts/check.sh` can be invoked by its path from any working directory. It checks the whole
repository with Ruff and runtime code with mypy, runs all three checks even when one fails,
and exits nonzero if any fails. It does not rewrite source or require Docker or credentials.
Frozen uv commands may install missing locked dependencies into the local environment.

Equivalent individual commands:

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src
```

Ruff is the primary linter and formatter; its rules and strict mypy settings live in
`pyproject.toml`. EditorConfig defines editor whitespace defaults, and Git attributes define
line endings. The Python line limit is 100 characters. `.flake8` supplies optional compatibility
settings only: Flake8 is not installed or run by the project checks, and it is not a replacement
for Ruff. Codecov has status checks and PR comments disabled; no coverage is collected or uploaded.

To apply formatting intentionally and review the diff:

```bash
uv run --frozen ruff format .
```

### Optional pre-commit hooks

Installing dependencies does not install Git hooks. Opt in explicitly:

```bash
uv run --frozen pre-commit validate-config
uv run --frozen pre-commit install
uv run --frozen pre-commit run --all-files
```

Hooks run the same three commands for Python or tooling-configuration changes. Each command runs
once over its full scope and receives no staged filenames. Hooks check formatting without fixing
it and require `uv` on PATH. They are an optional local convenience, not mandatory CI enforcement.
Pre-commit checks staged content by temporarily stashing unstaged tracked changes.

To remove the optional hook:

```bash
uv run --frozen pre-commit uninstall
```

## Add a read-only tool

1. Define the feature's typed request/response models and Protocol port under `features/`.
2. Implement business behavior in a service depending on the port. Keep FastAPI and HTTPX out
   of services; preserve the router -> service -> port -> gateway flow.
3. Implement Redmine access in `integrations/redmine/` using the shared async client and sanitized
   error mapping. MCP must never access PostgreSQL directly.
4. Wire concrete dependencies in `bootstrap.py` and expose service dependencies to the router.
5. Add a validated, bearer-protected REST route with a stable, unique `operation_id`. Register
   the router before MCP is created, and explicitly add the operation to the MCP allowlist.
6. Update the [tool reference](tool-reference.md), relevant configuration documentation, and
   [changelog](../CHANGELOG.md). Keep existing public tool names stable.
7. Run quality checks and the relevant [manual verification](manual-verification.md) steps.
   Record deferred checks and any limitations instead of claiming unperformed verification.

Services should remain small and feature-focused. Avoid introducing a generic CRUD or connector
framework. Administrative seed/restore functionality stays separate from runtime read-only tools.

## Dependencies and packaging

Use uv to update dependency metadata and resolution together, for example:

```bash
uv add --dev pre-commit
uv lock --check
uv build
```

The pre-commit dependency is already included; use the actual package name for future changes.
Review both `pyproject.toml` and `uv.lock` and submit them together. Avoid unrelated dependency
upgrades. Never hand-edit resolved hashes. Only `src/redmine_mcp` is packaged as runtime code.

Automated tests, coverage thresholds, and testing CI remain deferred. Follow the
[testing roadmap](testing-roadmap.md) when that scope is explicitly adopted.
