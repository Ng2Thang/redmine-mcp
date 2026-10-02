# Changelog

Changes are recorded here before a release is published. Version metadata alone does not imply
that a release has been published.

## Unreleased

### Added

- Added writer-only `upload_attachment` for bounded temporary uploads with an opaque token and
  separate accepted/uncertain and read-back verification fields.
- Added writer-only `add_project_file` to attach one upload token to a project or its own version,
  with separate empty-success and file-list verification results.

- Added read-only `get_current_user` for the caller's basic profile and visible project
  memberships with roles; credentials and additional account metadata are excluded.

- Added `list_issue_time_entries` for paginated, credited-user attribution of visible direct
  time entries on one issue.

- Added `get_project` for one visible project's details.
- Added the read-only global `list_issue_statuses` catalog.
- Added the read-only global `list_trackers` catalog.
- Added the read-only global `list_issue_priorities` catalog.
- Added the read-only global `list_document_categories` catalog.
- Added `list_project_files` for project and version file metadata.
- Added read-only `get_attachment` for metadata scoped by Redmine container visibility.
- Added `download_attachment` for bounded base64 content; Project or Version download counts
  may increase, so its MCP read-only and idempotent hints are false.
- Added `list_project_versions` with collection-completeness validation.
- Added `list_project_issue_categories` with collection-completeness validation.
- Issue requirement analysis, reviewed task backlog, and explicit testing/contract blockers.
- Disabled-by-default write authorization prerequisite and separate writer deployment settings;
  current tools remain read-only. Compose supports a configurable localhost MCP host port.

- Read-only project listing, issue listing, and issue detail tools through REST and MCP.
- Per-user Redmine API key authentication with request-scoped identity and paginated results.
- Synthetic Redmine/PostgreSQL development environment and separate data-operation helpers.
- EditorConfig, Python version selection, optional Flake8 compatibility settings, optional
  pre-commit checks, and a shared Git Bash quality-check command.
- Inactive Codecov configuration; automated testing and coverage remain deferred.
- Configuration, tool reference, manual verification, development, and operations guides.
- Security reporting guidance and a project code of conduct.

### Changed

- Prepared bounded attachment binary transport with same-origin URL validation, redirect
  rejection, and a configurable decoded-byte limit that defaults to 5 MiB.

- Extended `get_issue` with estimates, attachment content URLs, and journal edit metadata;
  missing estimates are identified in visibility observations.

- Extended `list_issues` with optional attachment and relation expansions, with page visibility
  observations for requested and unrequested associations.

- Pinned the synthetic Redmine deployment to 7.0.2 and removed the separate
  version-transition configurations and instructions. Removed unsupported Document REST drafts.

- Start the MCP session manager before accepting requests and wait for SDK readiness, preventing
  intermittent 500 responses when clients connect simultaneously. Add authorized offline runtime
  and reader acceptance cases, including failed startup and shutdown with an open session.
- Centralized runtime messages, stable error codes, and log templates in typed constants
  grouped by feature and responsibility, preserving existing text. Tool and parameter
  descriptions remain inline in feature routers; schema descriptions remain beside models.
- Expanded descriptions for all ten MCP tools with selection guidance, related-tool lookups,
  pagination behavior, and resource-specific limitations; documented project pagination inputs.
- Declared public feature services in package initializers with explicit `__all__` exports and
  shortened service imports in composition and feature routers.
- Extended public package exports to auth, common, API, MCP, integrations, feature contracts,
  application entry points, and administrative seed entry points. Architecture checks resolve
  re-exported symbols to preserve dependency boundaries.
- Replaced HTTP status literals with FastAPI status constants across runtime and existing test
  assertions; allowed only the status namespace through the domain import boundary.
- Bound identity verification to the same normalized key retained by the authentication context.
- Added per-read HTTP deadlines and streamed decoded-payload limits with guaranteed response
  closure and sanitized oversized-response errors.
- Strengthened MCP startup checks for route authorization, response schemas, hidden/duplicate
  routes, and exact generated tool names; isolated FastAPI route-context compatibility.
- Extended static architecture rules to package roots, nested contracts, and shared-layer direction.
- Organized authentication into `auth/` and moved concrete identity wiring to bootstrap.
- Added strict immutable query contracts and service-level validation for IDs, pagination,
  issue filters, timezone requirements, and expansions.
- Extracted lifecycle ownership with ordered cleanup and checked runtime-client access.
- Published read-only/idempotence MCP hints and added static import-boundary/cycle checks.
- Split framework-independent authentication and explicit read permissions from FastAPI
  dependencies, and isolated Redmine identity lookup and HTTP transport configuration.
- Added bounded HTTP pooling, separate connect/pool timeouts, cookie isolation, and distinct
  rate-limit, pool-exhaustion, and upstream timeout errors.
- Added request correlation, sanitized unexpected-error handling, and metadata-only timing logs.
- Centralized upstream envelope checks across readers, including strict pagination metadata and
  requested-resource identity checks.
- REST and MCP now require each caller's `X-Redmine-API-Key` header. Visibility and `me` refer to
  that Redmine user; shared runtime credentials and bearer token settings are retired.
- Extended `get_issue` with selectable related context while keeping the default expansions.
- Extended `list_issues` with tracker, parent, and inclusive update-time filters and bounded sorting.
- Extended `list_issues` with project category filtering and added nullable category references
  to list and detail issue responses.
- Extended `list_issues` with Target version filtering and exact-project scoping, and added
  nullable Target version references to list and detail issue responses.
- Added nullable issue start/due dates and permission-gated direct and descendant-inclusive
  spent hours to `list_issues` and `get_issue` responses.
- Organized README and contributor guidance around quick start and task-specific documentation.
- Expanded architecture documentation and Git line-ending rules.
