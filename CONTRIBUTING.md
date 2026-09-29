# Contributing

Use Python 3.13, uv, and Git Bash. Keep all Markdown in English and operational commands in Bash.
Follow the [code of conduct](CODE_OF_CONDUCT.md) and report vulnerabilities privately according
to the [security policy](SECURITY.md).

## Development rules

- Preserve router -> service -> port -> gateway dependencies. Services must not import FastAPI
  or HTTPX; MCP must never access PostgreSQL directly.
- Use explicit type hints, four-space Python indentation, and a 100-character line limit.
  Keep Ruff and strict mypy configuration centralized in `pyproject.toml`.
- Use async, lifespan-managed HTTP clients. Keep credentials and network access out of imports.
- Current tools are read-only; future issue writes require the workflow prerequisites and a
  separate opt-in restricted writer deployment. Keep administration separate. Preserve tool IDs
  and explicitly register new tools in the MCP allowlist.
- Submit dependency metadata and `uv.lock` together. Avoid unrelated upgrades and source rewrites.
- Never commit credentials, dumps, snapshots, generated state, or real Redmine data.
- Update the relevant guides and changelog when behavior, configuration, or public contracts change.

See [development](docs/development.md) for setup, feature implementation, packaging, and optional
pre-commit installation. See [architecture](docs/architecture.md) for dependency boundaries.

## Verification and review

```bash
uv sync --frozen
bash scripts/check.sh
```

Run relevant [manual verification](docs/manual-verification.md) checks for runtime changes.
Pre-commit hooks are available as an opt-in local convenience. Mandatory hook enforcement,
coverage thresholds and testing CI remain deferred. The issue workflow authorizes a required
automated baseline, still pending a separate testing assignment. Coding-only work excludes
test dependencies, fixtures and execution; follow the [testing roadmap](docs/testing-roadmap.md).

Use concise imperative commit subjects, such as `Add issue status filtering`. Review descriptions
should explain the behavior change, reference applicable issues, list checks actually performed,
and disclose failures or deferred checks. Include configuration or compatibility implications when
relevant. Keep patches focused and preserve unrelated work.
