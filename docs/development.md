# Development

The reader remains read-only. To develop the separate writer for multiple callers, use
`REDMINE_WRITER_AUTH_MODE=personal_key`, clear `REDMINE_WRITER_KEY_SHA256`, and optionally restrict
write admission with `REDMINE_WRITER_USER_IDS`. Each caller supplies a personal Redmine key.
Default pinned-key mode retains the existing single-key configuration. See
[configuration](configuration.md#separate-writer-deployment) for migration and session behavior.

## Environment

Use Python 3.13, uv, and Git Bash on Windows. `.python-version` selects the Python minor version;
`pyproject.toml` restricts runtime compatibility to 3.13. Run from the repository root:

```bash
bash scripts/doctor.sh
uv sync --frozen
bash scripts/check.sh
```

Run `scripts/doctor.sh` first to check Git Bash, Git, Python 3.13, `uv`, and repository files.
It also reports optional Docker Compose and Node.js/npm availability. It does not read `.env`
values, install packages, contact services, or change files. A missing required tool returns a
nonzero exit code; optional tools do not affect readiness for Python development.

Configure a reachable Redmine instance as described in [configuration](configuration.md).
Stop the Docker MCP service before starting locally on port 8000; see [operations](operations.md).

```bash
uv run --frozen uvicorn redmine_mcp.app:create_app --factory --host 127.0.0.1 --port 8000 --reload --no-access-log
```

Settings load at app creation. HTTP clients are managed by application lifespan; imports must not
read credentials or contact upstream services. See the [architecture](architecture.md).

## Request concurrency

REST routes and Redmine gateway calls are async. While one request awaits Redmine through the
shared `httpx.AsyncClient`, Uvicorn can handle other requests; MCP calls use the same REST routes.
The client shares connections, while each request supplies its own Redmine API key. Keep network
and other blocking I/O asynchronous in request handlers. If CPU-heavy work is added later,
measure its effect and move only that work off the event loop when needed. Do not put entire async
requests in worker threads to achieve concurrency.

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

Packages declare their public interfaces in `__init__.py` with explicit `__all__` exports.
External callers use package imports for published symbols. Implementation modules keep direct
imports within their own package to avoid importing a partially initialized public interface.
Feature packages publish models, ports, queries, and services; `features` groups service exports.
Keep feature routers out of package initializers to avoid API/composition import cycles.

| Package | Public interface |
|---|---|
| `redmine_mcp` | `Settings`, lazily imported `create_app` |
| `redmine_mcp.auth` | Identity/context, identity port, authentication, permission policy, key normalization |
| `redmine_mcp.common` | Errors, pagination, visibility, validation helpers |
| `redmine_mcp.api` | HTTP dependencies, security adapters, middleware, error handlers, route inspection, health router |
| `redmine_mcp.mcp` | Catalog, annotations, registration, shutdown |
| `redmine_mcp.integrations` | Supported integration namespaces |
| `redmine_mcp.integrations.redmine` | Redmine client, policy, gateways, transport factory |
| `tools`, `tools.seed` | Baseline synthetic seed entry point; importing does not execute seeding |

The root app factory is loaded on access, allowing domain imports without loading HTTP adapters.
Architecture checks resolve public re-exports back to their defining modules before evaluating
boundaries and import cycles. Re-exporting a symbol does not change its architectural ownership.

```python
from redmine_mcp.features import IssueService, ProjectService, ReferenceService, TimeEntryService
from redmine_mcp.features.issues import IssueService
from redmine_mcp.auth import AuthContext, AuthenticationService
from redmine_mcp.common import ApplicationError, Page
from redmine_mcp.integrations.redmine import RedmineClient, RedmineIssues
from redmine_mcp.mcp import register_mcp
```

1. Define the feature's typed request/response models and Protocol port under `features/`.
2. Implement business behavior in a service depending on the port. Keep FastAPI and HTTPX out
   of services; preserve the router -> service -> port -> gateway flow.
3. Implement Redmine access in `integrations/redmine/` using the shared credential-free async client and sanitized
   error mapping. MCP must never access PostgreSQL directly.
4. Wire concrete dependencies in `bootstrap.py` and expose service dependencies to the router.
5. Add a validated, personal-key-protected REST GET route under `/api/v1/` with a stable, unique
   `operation_id`. Add its read permission to `auth/policy.py`; MCP exposure is a separate
   allowlist decision. The route owns the tool description and schemas. Register the router before MCP
   is created, then add the operation ID to `src/redmine_mcp/mcp/catalog.py` in the intended tool
   order. Startup fails if a catalog ID is duplicated or does not match exactly one GET route.
6. Update the [tool reference](tool-reference.md), relevant configuration documentation, and
   [changelog](../CHANGELOG.md). Keep existing public tool names stable.
7. Run quality checks and the relevant [manual verification](manual-verification.md) steps.
   Record deferred checks and any limitations instead of claiming unperformed verification.

Use `http_status.HTTP_*` constants imported from `fastapi.status` through
`from fastapi import status as http_status` for HTTP statuses. The architecture gate permits
this constants namespace in domain code while continuing to reject other FastAPI APIs there.
Do not replace unrelated numeric values, such as pagination limits, with HTTP constants.

Services own business validation for direct and HTTP callers. Define strict query contracts and
validate IDs and cross-field relationships before port dispatch; routers decode HTTP syntax.
Use named arguments for port calls. `scripts/check_architecture.py` runs with the normal static
checks to enforce import boundaries and detect cycles without running application code or tests.

Services should remain small and feature-focused. Start a new tool from the client's outcome and
the [tool dashboard](plans/index.md), using Redmine REST only as implementation evidence. Avoid
introducing a generic CRUD or connector framework. Administrative seed/restore functionality stays
separate from runtime tools. Future issue writes require the
[tool workflow](workflows/redmine-tools.md) prerequisites and a separate opt-in writer deployment;
current tools remain read-only.

## Shared text constants

Runtime-owned error messages, error codes, and log templates live in
`src/redmine_mcp/constants/`. Import a public namespace from its
initializer, for example:

```python
from redmine_mcp.common import InvalidInputError
from redmine_mcp.constants import issues as issues_text

raise InvalidInputError(issues_text.PROJECT_REQUIRED_FOR_CATEGORY)
```

Each constant is annotated as `Final[str]`. Group messages by ownership: `auth`, `api`,
`runtime`, `redmine`, or a feature such as `issues`.
Shared validation text belongs in `common`, stable machine-readable error codes in `codes`,
MCP catalog diagnostics in `mcp`, and logging format strings in `logs`.

Keep tool and parameter descriptions inline in `features/{feature}/router.py`, so readers
can see the tool contract beside its route and inputs. Keep response schema descriptions
beside their model declarations. Do not move these descriptions into shared constants.

Use named `.format(...)` placeholders for dynamic diagnostic messages, such as
`common_text.POSITIVE_INTEGER_REQUIRED.format(name="issue_id")`. Keep log placeholders in
logging's `%s` style and pass values as separate arguments. Never interpolate credentials,
request bodies, or upstream error content into public messages or logs.

Constants must not import runtime layers or framework libraries; the architecture check
enforces this boundary. Wire field names, URLs, permission identifiers, schema literals,
and empty defaults stay with their contracts. Framework-generated validation messages are
still managed by FastAPI and Pydantic. Changing a constant changes all of its consumers;
review public wording and stable error codes accordingly.

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

Automated testing is authorized and required as a shared prerequisite for future reader tools,
but its baseline is not yet implemented. A coding-without-tests assignment cannot install test
dependencies or create/run fixtures and tests; assign that baseline separately. Coverage
thresholds and testing CI remain deferred. Follow the [testing roadmap](testing-roadmap.md).
