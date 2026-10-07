# Changelog

Changes are recorded here before a release is published. Version metadata alone does not imply
that a release has been published.

## Unreleased

### Changed

- Raise default upstream concurrency to 50 and admission wait to 30 seconds. Logical reads now
  allow 30 upstream attempts within a 90-second aggregate deadline. Code defaults, `.env.example`
  and both Compose services use the same values; query pages remain 10 and read bytes remain
  10 MiB. Existing explicit environment values still override these defaults.

### Fixed

- Classify received HTTP 500-599 as uncertain across all registered JSON and binary mutations
  through the shared writer transport. Remove the membership-only opt-in; preserve individual
  and batch result schemas, GET error mapping, authorization, single dispatch, and independent
  read-back behavior. Callers must reconcile before retrying. Prep-019 offline acceptance,
  owned Redmine 7.0.2 commit/HTTP-500 reconciliation and cleanup, and Inspector compatibility pass.

- Preserve the `list_time_entries.user_id` MCP input union so both positive numeric user IDs
  and `"me"` are supported. Remove FastAPI-MCP's conflicting scalar type before SDK caching.

- Preserve `estimated_hours` and `total_estimated_hours` in `list_issues`, with visibility
  observations for missing upstream estimates. Issue detail estimates retain their contract.
- Add task 034/035 service, gateway, REST and MCP SDK regressions, owned Redmine 7.0.2
  reporting acceptance, and a repeatable reader-only Inspector check. Cover estimate absence,
  decimal client totals, project-only logs, credited-user/date filters, own-log visibility,
  bounded pagination and the numeric/`me` MCP schema regression.

- Normalize repeated native project membership role IDs while retaining any inherited source;
  keep other selected projects readable after a project-specific pagination scope error.
- Recheck active operation deadlines after upstream admission and release expired requests'
  permits before dispatch, preventing queued membership writes after the batch deadline.

- Preserve nullable description and due-date MCP input schemas for `create_project_version`;
  explicit null now follows the same omission contract as REST. Offline regression tests cover it.
- Correct the public Redmine URL classmethod validator signature, which prevented Pydantic
  from constructing settings during application import.
- Align time-entry tool descriptions and aggregation examples with pagination policy. Blocked
  or incomplete collections require partial/unavailable totals. Concurrency acceptance now
  follows the configured semaphore limit, including the default of 50.
- Preserve sanitized aggregate read timeouts when synchronous response conversion expires before
  REST headers are sent. Preserve environment proxy and `NO_PROXY` routing with the admitted
  upstream transport; direct and proxy connections share the same semaphore.

### Added

- Add read-only `list_time_entries` for spent-time logs across caller-visible projects, credited
  users and inclusive log-date ranges, including entries without an issue. Project filters
  explicitly select exact-project or descendant scope. Totals remain client calculations over
  complete permitted pagination; testing and live acceptance are pending.

- Support standalone `REDMINE_WRITER_OPERATIONS=allowed_all` to permit all registered write
  operations through the existing writer catalog and authorization gates. Explicit operation
  lists and the empty default retain their behavior; mixed `allowed_all` lists are rejected.

- Add offline unit/service/gateway and REST/MCP tests for all four project membership tools,
  including whole-batch preflight, writer gates, duplicates, protected roles, bounded absence
  proofs, partial execution, uncertainty, cancellation and queued deadline regressions.

- Added `list_project_members` and writer-only `add_project_members`, `update_project_members`
  and `delete_project_members`, with up to ten selected projects/items, whole-batch preflight,
  user-only writes, project permission checks and separate acceptance/read-back outcomes.
  Preserves native inherited/protected-role behavior and supports MCP DELETE batch bodies.
  Ruff/mypy validation and documentation are included; offline and 7.0.2 acceptance remain pending.

- Writer-only `create_project_version` creates open, unshared Target versions with optional
  description and due date. Readable same-project duplicates return their existing data with
  `version_already_exists`; acceptance, read-back verification, and uncertainty remain separate.
  Requires explicit writer configuration and `manage_versions`. Runtime acceptance is pending.

- Shared upstream request semaphore, bounded admission, aggregate logical-read request/byte/time
  budgets, and stateless pagination policy. Large collections return a first-page preview but
  require narrower scope before continuation; capability inventory scans are bounded.
- Optional `REDMINE_PUBLIC_URL` mapping for validated attachment browser links. Attachment
  retrieval is metadata/link-only: `download_attachment` is removed from MCP discovery and cached
  invocations plus the retired REST content route are rejected. No generated exports or query
  state are introduced. Runtime acceptance for prep-015 remains pending separately authorized testing.

- Read-only `list_my_project_capabilities` with paginated caller-visible projects, membership
  roles deduplicated by ID, sorted unique project permissions merged across all readable roles,
  explicit known/partial/unknown permission evidence, and conditional/unknown tool candidates.
  Permissions are reported at project level instead of repeated under each role.
  Global tools are separate;
  deployment-disabled, account-restricted and denied writes are omitted.
  Centralized read rules cover project details, issues, versions, categories, files, issue
  time entries and attachment containers, including OR/AND permission requirements and
  explicit administrator evidence. Resource visibility remains subject to Redmine.
  Tool entries contain only `operation_id` and `state` by default; `include_reasons=true`
  adds explanations for project and global tools.
  Optional project and operation filters return scoped capabilities, with filtering before
  pagination and conditional matches by default; `include_unknown=true` retains unknowns.

- Added caller-specific personal-writer MCP tool discovery with an immutable deployment schema
  superset, bounded project inventory, known-denial filtering and conditional/unknown candidates.
  Direct and cached calls retain authoritative per-request REST permission checks.

- Added request-local personal-writer capability evidence and project/resource permission checks
  for all eleven write operations, with same-key role/target reads and authoritative upstream
  handling of tracker, workflow, field, ownership and partial metadata conditions.

- Added explicit personal-key writer authentication for multiple callers, optional write-only
  user admission, legacy pinned-key compatibility, and credential-bound MCP sessions using the
  now-pinned MCP SDK 1.30.0. Reader deployments remain read-only.

- Added writer-only `remove_issue_watcher` for one direct principal membership, with visible
  issue preflight, destructive hints, and absence verification separate from acceptance.

- Added writer-only `add_issue_watcher` with a single strict principal ID, visible issue
  preflight, and membership verification separate from empty upstream acceptance.

- Added writer-only `delete_issue_relation` with visible endpoint/context checks,
  destructive hints, and independent absence observations from both issues.

- Added writer-only `create_issue_relation` for a single visible destination, normalized
  relation direction, validated scheduling delay, and independent same-ID read-back.

- Added writer-only `update_issue_note` with visible issue/journal membership checks,
  supplied text/privacy updates, and independent same-journal read-back.

- Added writer-only `update_issue` for supplied fields, uploads, and notes-only updates,
  with independent per-field verification and new-journal observations.

- Added writer-only `create_issue` with validated issue fields, native `copy_from`, destination
  project selection, upload/custom-field/watcher inputs, and independent per-field read-back.

- Added writer-only `delete_attachment` with declared-container membership checks,
  destructive MCP annotations, and independent visible-absence verification.

- Added writer-only `upload_attachment` for bounded temporary uploads with an opaque token and
  separate accepted/uncertain and read-back verification fields.
- Added writer-only `add_project_file` to attach one upload token to a project or its own version,
  with separate empty-success and file-list verification results.
- Added writer-only `update_attachment` with declared-container membership checks, supplied-field
  metadata patches, and separate write acceptance and read-back verification.

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
