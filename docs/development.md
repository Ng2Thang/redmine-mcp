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
repository with Ruff, runtime code with mypy, and import boundaries with the architecture checker.
It runs all four checks even when one fails and exits nonzero if any fails. It does not rewrite
source or require Docker or credentials.
Frozen uv commands may install missing locked dependencies into the local environment.

Equivalent individual commands:

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src
uv run --frozen python scripts/check_architecture.py
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

Hooks run Ruff lint, Ruff format check and mypy for Python or tooling-configuration changes.
The architecture check is run by `scripts/check.sh` and is not an installed hook. Each hook runs
once over its full scope and receives no staged filenames. Hooks check formatting without fixing
it and require `uv` on PATH. They are an optional local convenience, not mandatory CI enforcement.
Pre-commit checks staged content by temporarily stashing unstaged tracked changes.

To remove the optional hook:

```bash
uv run --frozen pre-commit uninstall
```

## Maintain the pinned MCP compatibility boundary

FastAPI-MCP 0.4.0 and MCP SDK 1.30.0 are the supported pair. `mcp/compatibility.py` owns
identified vendor-private hooks, handler/cache installation, native HTTP request-context access
and manager lifecycle. Other runtime modules call the typed facade and keep tool/auth/schema,
discovery and budget policy outside it. Do not access `_request`, `_http_transport`, `_tool_cache`,
manager flags/tasks or SDK handler/context internals in a new policy module.

Compatibility checks run before hook installation and after mount, then again before lifecycle
startup. Failure uses the existing sanitized startup message; do not log version lookup errors,
package paths, exception contents or caller credentials. The facade performs no installation
and provides no fallback that relaxes validation or authorization.

A dependency upgrade is separate work: inspect the proposed versions' source and signatures,
update pins and lockfile together, revise the facade checks, and retain schema repair/annotation,
cache seeding, discovery, budget and mount ordering. Within a separately authorized verification
stage, execute SDK-026-001..006: source isolation, incompatible metadata/hooks, nullable/union
calls, two-caller discovery/session ownership, membership DELETE JSON, fresh budgets, writer
uncertainty, startup/readiness/cancellation/shutdown and owned Inspector/native cleanup.
Move lifecycle fault-injection patches from `mcp/registration.py` to the compatibility module
and use valid pinned-server/transport fixtures rather than unchecked partial namespaces.
No upgrade or runtime acceptance is implied by PREP-026's passing static checks.
The separately authorized [preparation regression record](testing/evidence/prep-022-026-testing.md)
supersedes its coding-only handoff. Manager construction passes the application's effective
request-body cap to the SDK so valid base64 uploads do not encounter the SDK's smaller default.
At the Redmine gateway, explicit null assignment becomes an empty native ID because 7.0.2
ignores JSON null assignment; omission still means leave the field unchanged.

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
| `redmine_mcp.mcp` | Catalog, annotations, registration and shutdown; internal modules own compatibility and schema/discovery/budget policy |
| `redmine_mcp.integrations` | Supported integration namespaces |
| `redmine_mcp.integrations.redmine` | Redmine client, policy, gateways, transport factory |
| `tools`, `tools.seed` | Compatible baseline seed function; `python -m tools.seed` selects base/history/all; importing does not execute seeding |

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
2. Implement business behavior in a service depending on the port. Keep FastAPI APIs and HTTPX
   out of services, except the HTTP status constants namespace described below; preserve the
   router -> service -> port -> gateway flow.
3. Implement Redmine access in `integrations/redmine/` using the shared credential-free async client and sanitized
   error mapping. MCP must never access PostgreSQL directly.
4. Wire concrete dependencies in `bootstrap.py` and expose service dependencies to the router.
5. Add a validated, personal-key-protected REST GET route under `/api/v1/` with a stable, unique
   `operation_id`. Add its read permission to `auth/policy.py`; MCP exposure is a separate
   allowlist decision. The route owns the tool description and schemas. Register the router before MCP
   is created, then add the operation ID to `src/redmine_mcp/mcp/catalog.py` in the intended tool
   order. Startup fails if a catalog ID is duplicated, lacks a response schema or the required
   authorization dependency, or fails to match exactly one GET route under `/api/v1/`.
6. Update the [tool reference](tool-reference.md), relevant configuration documentation, and
   [changelog](../CHANGELOG.md). Keep existing public tool names stable.
7. Run quality checks within the assignment's scope. Execute automated tests, startup, Inspector
   and the relevant [manual verification](manual-verification.md) steps only when explicitly
   authorized. Documentation-only assignments use manual prose/source/link review. Record
   deferred checks and limitations instead of claiming unperformed verification.

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
separate from runtime tools. The reader remains read-only; the separate opt-in writer implements
18 mutations. New writes require the [tool workflow](workflows/redmine-tools.md) prerequisites,
typed inputs, configured operation gates and native permission checks. Register the operation
in `auth/policy.py` and use `require_write_access` on its versioned POST/PUT/PATCH/DELETE route.
Document exact effects, single-attempt uncertainty, independent read-back and owned cleanup.
Explicit operation lists fix the deployment ceiling; `allowed_all` also admits newly registered
writes after upgrade. Preserve existing IDs, schemas and reader isolation.

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

## Documentation portal maintenance

The standalone portal source is `src/redmine_mcp_docs/`; detailed documentation remains in
canonical `docs/` files. Edit portal introductions/navigation in that source, then regenerate
the ignored static export and restart the local server:

```bash
bash scripts/docs-portal.sh export
bash scripts/docs-portal.sh serve
```

The portal uses bundled browser libraries and Python's standard-library server, independent of
MCP runtime settings. See [portal maintenance and hosting](documentation-portal.md) for asset
licenses, export boundaries, and the manual verification handoff. Only `src/redmine_mcp` enters
the runtime wheel and MCP Docker image.

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

The automated baseline is organized into `tests/unit/`, `tests/integration/` and `tests/e2e/`.
Default pytest discovery runs the two offline layers. Live tests require explicit directory
selection, `--run-e2e` and owned Redmine 7.0.2 fixtures. A coding-without-tests assignment cannot
install test dependencies or create/run fixtures and tests; assign verification separately.
Coverage thresholds and testing CI remain deferred. Follow the
[testing roadmap](testing-roadmap.md) and [coverage matrix](plans/testing-coverage.md).

Current functional evidence is recorded in the
[2026-10-07 ledger](testing/evidence/current-catalog-acceptance.md): 1,086 offline and 21 owned live cases
passed for the 32-operation catalog. Those are dated results, not a claim that future edits or
every historical variant are verified. Operational readiness, CI and recovery remain separate.
