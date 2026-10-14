# Development

The reader remains read-only. To develop the separate writer for multiple callers, use
`REDMINE_WRITE_ENABLED=true` and configure `REDMINE_WRITER_OPERATIONS`. Each caller supplies
a personal Redmine API key. No key hash or user ID admission configuration is required. See
[writer configuration](configuration.md#separate-writer-deployment).

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

## Synthetic Redmine versions

For automated E2E version selection, use `REDMINE_E2E_VERSION` and
`scripts/prepare-e2e.py` as described in the
[E2E release instructions](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing-roadmap.md#selecting-a-redmine-release).
E2E seeds its own fixtures inside the existing versioned stacks. Built-in profiles are
6.0.1 and 7.0.2; other exact 6.x.x releases require an explicit custom profile. Fixture
manifests live in `.local/e2e/<project>/` for built-in profiles, separate from Docker seed state.
The development seed below does not substitute for E2E preparation. Use Docker Compose 2.24.4+.

With Docker Desktop running, start and seed the default Redmine 7.0.2 stack or the
separate Redmine 6.0.1 stack from Git Bash:

```bash
bash scripts/dev-up.sh 7.0.2
bash scripts/dev-up.sh 6.0.1
```

Only these two versions are accepted; omitting the argument selects 7.0.2. The argument
selects the self-contained `deploy/compose.test.<version>.yaml`, its project, named Docker
volumes and fixed localhost ports. Configuration and synthetic markers are defined in Compose;
no dotenv file, host state directory or environment toggle is needed. Root `.env` is ignored.
Demo accounts use `redmine-demo-password`; PostgreSQL uses `redmine-local-development`.
The new projects do not adopt or delete old test-project volumes or local state.

| Redmine | Project | Redmine port | PostgreSQL port | MCP reader / optional writer |
|---|---|---|---|---|
| 7.0.2 | `redmine-mcp-dev-7-0-2` | 8001 | 5433 | 8000 / 8004 |
| 6.0.1 | `redmine-mcp-dev-6-0-1` | 3001 | 5436 | 8002 / 8003 |

Before starting containers, the script checks the three required ports and reports the
conflicting service or container. Ports already owned by the selected service are reused
on repeat runs. Both versions can run concurrently. Both Redmine containers listen on 3000
internally. The writer is optional and is not started by `dev-up.sh`.

Verification handoff: this startup refactor has not been exercised with Docker, automated
tests, or static-check tools. Separately authorized verification should cover fresh setup
for both versions, concurrent stacks, reruns, a conflicting Docker container and host listener,
unsupported versions, inherited Compose overrides, retained legacy volumes, and a root `.env`
containing unrelated settings. Check that startup creates no host configuration directories,
that seed manifests stay in the selected Docker volume, and that explicit E2E preparation
still mounts host evidence separately. Reset/backup/restore changes also remain unverified.

Both versions run seed mode `all` by default: the 150-issue baseline followed by the
history dataset with 8 projects, 20 users, 12 versions, 300 additional issues, and
900 time entries. Completed datasets are skipped on subsequent runs; an interrupted
history seed resumes from its saved checkpoints. Existing incomplete baseline seeds
still require the generator's guarded reset workflow.

Synthetic bootstrap grants the `Manager` role every assignable permission registered
by Redmine and the installed plugins. It enables all-tracker access, full issue,
time-entry and user visibility, and management of all project roles. These remain
role-based permissions governed by project membership, enabled modules, and workflow
rules; the demo manager account is not a Redmine administrator. Bootstrap reapplies
these settings on every `dev-up.sh` run, even when dataset generation is skipped.

Lifecycle helpers default to 7.0.2. Set `REDMINE_TEST_VERSION=6.0.1` to select the
6.0.1 profile through `scripts/common.sh`; E2E uses `REDMINE_E2E_VERSION` independently. To stop 6.0.1 without removing its volumes:

```bash
docker compose -p redmine-mcp-dev-6-0-1 -f deploy/compose.test.6.0.1.yaml down
```

## DEBUG logging

Run from the repository root in Git Bash. Stop the Docker MCP service before using local
port 8000. The following starts the local application with detailed diagnostics and disables
Uvicorn access logs, which otherwise include raw request URLs:

```bash
LOG_LEVEL=DEBUG uv run uvicorn redmine_mcp.app:create_app \
  --factory --reload --no-access-log
```

For an existing synthetic Docker deployment, recreate only the selected MCP service so the
updated environment reaches its process. This does not reset or seed Redmine:

```bash
source scripts/common.sh
compose up -d --no-deps --force-recreate mcp-server
compose logs --follow --tail=200 mcp-server
```

Set `LOG_LEVEL: DEBUG` in the selected Compose service environment before recreation.
Use `mcp-writer` instead of `mcp-server` for an already configured writer deployment; retain
its existing writer credentials, admission mode and operation gates. For external Redmine
using the base Compose file:

```bash
LOG_LEVEL=DEBUG docker compose -p redmine-mcp-external \
  --env-file .local/external.env -f deploy/compose.yaml \
  up -d --no-deps --force-recreate mcp-server
docker compose -p redmine-mcp-external \
  --env-file .local/external.env -f deploy/compose.yaml logs --follow --tail=200 mcp-server
```

Use `--build` when the image does not yet contain the logging implementation. Set `LOG_LEVEL`
back to `INFO` in the process settings or selected Compose service and recreate the container
to turn detailed events off. Editing a configuration file alone does not update a running
process. Ordinary `docker compose restart` does not apply changed container environment.

To inspect a completed incident, copy its server-generated correlation from the console or
the `X-Request-ID` response header. Filter a bounded log snapshot, for example:

```bash
compose logs --no-color --tail=2000 mcp-server | rg 'request_id=<request-id>'
compose logs --no-color --tail=2000 mcp-server | rg 'call_id=<call-id>'
```

Replace the placeholders with actual IDs. `request_id` links HTTP and upstream events;
`call_id` separates concurrent tool invocations and discovery within an MCP session. A tool
error returned as a result uses `mcp_call_completed outcome=tool_error`; raised failures use
`failed`, and cancellations use `interrupted`. Upstream `acquired` means bytes were obtained,
not that parsing or the entire tool succeeded. Write `accepted` is the transport receipt;
subsequent tool verification still determines the public result. `response_bytes` counts only
decoded bytes actually consumed, including a chunk that triggers a limit; error bodies are
not read for diagnostics.

Keep diagnostics in lazy `%s` templates under `constants/logs.py`. Use only known operation
names, endpoint templates, numeric timings/counts, fixed reasons, and capability states.
Guard stack inspection and endpoint normalization with `logger.isEnabledFor(logging.DEBUG)`.
Do not use `logger.exception`, `exc_info`, or request/model serialization for application
diagnostics. Vendor records reaching the application console are reduced to a fixed event
because even WARNING/ERROR messages may contain values or raw exceptions.

See [configuration](configuration.md#detailed-debug-logs) for the logging contract and the
[verification handoff](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/plans/debug-logging.md) for scenarios requiring separate authorization.

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
The separately authorized [preparation regression record](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing/evidence/prep-022-026-testing.md)
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
   [changelog](https://github.com/Ng2Thang/redmine-mcp/blob/master/CHANGELOG.md). Keep existing public tool names stable.
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

## Automated tests

The automated baseline is organized into `tests/unit/`, `tests/integration/` and `tests/e2e/`.
Default pytest discovery runs the two offline layers. Live tests require explicit directory
selection, `--run-e2e` and owned fixtures for the selected Redmine 6.x.x or 7.0.2 release.

```bash
uv run --frozen pytest
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e --run-e2e
```

Use the first command for offline verification. Live E2E requires Docker Desktop and
Node.js/npm for Inspector. Pytest automatically prepares PostgreSQL/Redmine and owned fixtures
once per session, including focused E2E runs. `dev-up.sh` and manual preparation are optional
before pytest. Run the live commands sequentially; they use the selected development project,
not another Redmine stack. See [preparation troubleshooting](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing-roadmap.md#preparation-troubleshooting).

Offline tests of supplemental scripts must replace both `ROOT` and the separately imported
`STATE` with temporary paths, and mock subprocess/network calls. Replacing `ROOT` alone does
not redirect private Inspector credentials or evidence out of `.local/e2e/<project>/`.

A coding-without-tests assignment cannot
install test dependencies or create/run fixtures and tests; assign verification separately.
Coverage thresholds and testing CI remain deferred. Follow the
[testing roadmap](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing-roadmap.md) and [coverage matrix](plans/testing-coverage.md).

Current functional evidence is recorded in the
[2026-10-07 ledger](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing/evidence/current-catalog-acceptance.md): 1,086 offline and 21 owned live cases
passed for the 32-operation catalog. Those are dated results, not a claim that future edits or
every historical variant are verified. Operational readiness, CI and recovery remain separate.
