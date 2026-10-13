# Operations

Run commands from the repository root in Windows Git Bash. Docker Desktop must be running with
Linux containers. These helpers manage the dedicated synthetic environment; external Redmine
uses the separate workflow below. See [configuration](configuration.md) for settings and secrets.

## Start and inspect the synthetic environment

```bash
bash scripts/dev-up.sh 7.0.2
bash scripts/dev-up.sh 6.0.1
```

Choose either command, or run both to start independent environments. Only 7.0.2 and 6.0.1
are accepted; omitting the argument selects 7.0.2. Each Compose file includes its local settings
and markers. The script starts PostgreSQL and Redmine, seeds baseline and history data,
and builds/starts MCP. No environment switches are required. First startup downloads/builds
images. Python 3.13 and Docker Compose 2.24.4+ must be on PATH. No `.env` file or host state
directory is created or required; Docker manages persistent state in named volumes.

Startup checks the selected ports before starting containers. A conflicting container or host
listener produces an error identifying the port and service. Reruns reuse ports owned by the
selected service. Ports are fixed by the versioned Compose files; inherited Compose settings
cannot redirect the helper to another environment. The commands do not run tests or prepare
the separate owned E2E fixtures.

| Service | Address |
|---|---|
| Redmine (7.0.2) | `http://localhost:3002` |
| Swagger | `http://localhost:8000/docs` |
| MCP Streamable HTTP | `http://localhost:8000/mcp` |
| Liveness | `http://localhost:8000/health` |
| PostgreSQL | `localhost:5433`, database/user `redmine` |

### Choose a Redmine version

Two self-contained local Compose files are available. Select one without `deploy/compose.yaml`:

| Redmine | Compose file | Compose project | Seed-state volume |
|---|---|---|---|
| 7.0.2 | `deploy/compose.test.7.0.2.yaml` | `redmine-mcp-dev-7-0-2` | `redmine-mcp-dev-7-0-2_seed_state` |
| 6.0.1 | `deploy/compose.test.6.0.1.yaml` | `redmine-mcp-dev-6-0-1` | `redmine-mcp-dev-6-0-1_seed_state` |

`deploy/compose.test.yaml` remains an equivalent 7.0.2 configuration for existing helpers.
It uses the same project and data as `deploy/compose.test.7.0.2.yaml`; select one of these
files, not both. Keep the two 7.0.2 configurations synchronized when changing deployment settings.

Both images are pinned by digest. The 6.0.1 digest comes from the official
[Docker image metadata](https://hub.docker.com/layers/library/redmine/6.0.1/images/sha256-499ba60895598e9a8556d412d851d39e8faf9108b6270114ec0d2dcbc6ebd285).
The projects use separate database and attachment volumes, with matching version labels.
Keep the project names shown above; do not reuse a project's volumes with another version.
Both versions can run concurrently with these fixed localhost ports:

| Redmine | Redmine port | PostgreSQL port | MCP reader / optional writer |
|---|---|---|---|
| 7.0.2 | 3002 | 5433 | 8000 / 8001 |
| 6.0.1 | 3001 | 5436 | 8002 / 8003 |

The development files contain fixed local credentials and synthetic markers. Root `.env` is
ignored. Old `redmine-mcp-test*` containers, volumes and `.local/` files are not adopted,
modified or deleted. Stop an old container if startup reports that it occupies a required port.
The new projects start independent datasets. Backups live in each project's `backup_data`
volume and are retained by the guarded reset helper.

Both versions install plugins and seed automatically. Lifecycle helpers default to 7.0.2;
prefix a helper command with `REDMINE_TEST_VERSION=6.0.1` to select 6.0.1. E2E fixture
preparation remains separate; see the [testing roadmap](testing-roadmap.md).

### Install local Redmine plugins

The Redmine service in both local Compose variants installs plugin directories from
`deploy/redmine-plugins` at startup. Each directory must contain `init.rb`.
`deploy/redmine/install-plugins.sh` copies the read-only host sources into the container
and hands startup to the official Redmine entrypoint. That entrypoint installs missing
Gemfile dependencies and runs core and plugin database migrations before serving requests.
First installation requires network access to fetch missing gems. Installation or migration
errors stop startup and appear in the Redmine container logs.

The installer sets Bundler's local `without` configuration to `development test` and
`deployment` to `false`, matching the supplied Agile and Tags installation options without
using the legacy command flags. See [Bundler configuration](https://bundler.io/man/bundle-config.1.html).
Dependency installation and migrations run from `/usr/src/redmine`, where Redmine's Gemfile
and Rakefile live; `/usr/src/redmine/plugins` contains the copied plugin directories.
The installer sets `RAILS_ENV=production` and `REDMINE_PLUGINS_MIGRATE=1` so the official
entrypoint migrates all installed plugins, including Agile, Tags, and Work Time.
The migration task is `redmine:plugins:migrate`; an individual Agile migration would use
`NAME=redmine_agile`, while Tags uses `NAME=redmineup_tags`. See the
[Redmine plugin installation guide](https://www.redmine.org/projects/redmine/wiki/Plugins).

After adding, updating, or removing plugin sources, recreate the Redmine container so it gets
a fresh set of plugin files. For the default 7.0.2 deployment:

```bash
source scripts/common.sh
compose up -d --no-deps --force-recreate redmine
compose logs --follow --tail=100 redmine
```

Recreation preserves the database and uploaded files. Removing a source directory does not
uninstall its database tables. Enable installed modules and grant the required role permissions
in Redmine administration. The base `deploy/compose.yaml` connects MCP to an external Redmine;
plugin installation applies only to the local Redmine service in the selected version file.
Plugin compatibility with the pinned Redmine 7.0.2 image still requires separately authorized
startup verification; Work Time's bundled changelog only declares support through Redmine 6.1.

For database clients, database/user are `redmine` and password is `redmine-local-development`.
Synthetic accounts are
`admin`, `demo-manager`, `demo-developer`, `demo-reporter`, and `demo-mcp-reader`; their password
is `redmine-demo-password`. These are localhost development credentials. Use each account's
personal key to inspect its visibility.

Wrappers disable Git Bash path rewriting for Docker. For manual Compose operations, set:

```bash
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'
source scripts/common.sh
compose ps
```

Do not share `docker compose config` output; it can expose interpolated credentials.

## Stop and restart

Stop all synthetic services while retaining volumes:

```bash
source scripts/common.sh
compose stop
```

Restart using `bash scripts/dev-up.sh`. Completed seeds are skipped.
To free port 8000 for local Python while keeping Redmine running:

```bash
source scripts/common.sh
compose stop mcp-server
```

## Seed and reset

With the synthetic database and Redmine running:

```bash
bash scripts/seed.sh
```

A completed seed is skipped. An interrupted seed is not resumed; resolve the original failure
before performing an explicit reset if the synthetic data can be discarded.

The following command deletes the dedicated synthetic database and attachment volumes, clears
generated local state, and recreates the environment. Backups are preserved. It requires valid
synthetic markers; do not bypass marker checks or use it against real data.

```bash
bash scripts/reset-test-env.sh --confirm-reset
```

Read IDs from `/seed-state/manifest.json` in the Redmine container after reset:

```bash
source scripts/common.sh
compose exec -T redmine cat /seed-state/manifest.json
```
See [synthetic data](test-data.md) for expected counts and visibility cases.

To add three months of project, sprint-version, issue, and spent-time history to an already
seeded synthetic instance, run:

```bash
bash scripts/seed-history.sh
```

This adds 8 projects, 20 users, 12 versions, 300 issues, and 900 time entries. It preserves
the base dataset, skips a completed rerun, and resumes an interrupted run. Read generated IDs
from `/seed-state/history-manifest.json` in the Redmine container.
In Redmine, inspect the History Alpha/Beta project trees, memberships, versions, issue schedules,
and Spent time reports. In MCP Inspector, use manifest project and issue IDs to check visible
projects, versions, and issues, then confirm `History Beta Private` is inaccessible to MCP Reader.
The MCP tools can read visible time entries. See [synthetic data](test-data.md) for counts
and the date window.

## Backup and restore

These are development helpers, not a validated production recovery procedure. Snapshot IDs must
start with a letter or digit and contain only letters, digits, underscores, or hyphens, up to
64 characters. The example `baseline` is a snapshot ID; choose an unused ID when backing up.

```bash
bash scripts/backup.sh baseline
```

Backup validates the environment and stops MCP and Redmine. It stores a database dump,
attachments archive, environment marker, manifest, test credentials, image-version metadata,
and a completion marker under `/state/backups/<snapshot-id>/` in the project's `backup_data`
volume. Its exit handler attempts to
restart applications even when backup fails. Incomplete snapshots must not be used for restore.
Existing snapshots are not overwritten. Treat every snapshot as sensitive.

Restore replaces the current synthetic database, attachments, and local state:

```bash
bash scripts/restore.sh baseline
```

Only restore trusted snapshots from matching repository and image versions. The helper checks
the synthetic markers, completion marker, Redmine/PostgreSQL image versions, dump listing, and
archive readability. It restores the database and replaces attachments,
and restarts applications on success. These checks do not establish full recovery correctness.

If restore fails, MCP and Redmine remain stopped. Inspect the failure privately, verify snapshot
compatibility and completeness, and correct the cause before retrying a trusted restore. Do not
restart applications into a partially restored state. Reset is only an alternative when the current
synthetic data can be discarded. Full restore, checksum, and failure-recovery validation is deferred.

## External Redmine

The synthetic environments use pinned Redmine images in their versioned Compose files.
The backup and restore wrappers operate on the selected marked synthetic project. Use a
snapshot created under that version when restoring it. `dev-up.sh` refuses an existing
database or attachments volume unless its Docker labels identify the selected version and
project. New volumes receive these labels from Compose.

Prepare `.local/external.env` as described in [configuration](configuration.md). Stop any MCP
process already occupying port 8000. With the Git Bash Docker exports above in effect:

```bash
docker compose -p redmine-mcp-external --env-file .local/external.env -f deploy/compose.yaml up -d --build
```

This uses base Compose, which runs MCP only. Never add the synthetic override or invoke the
seed/reset/restore helpers for an external instance. Inside Docker, use `host.docker.internal`
for Redmine running on the Windows host. Hosting, HTTPS ingress, and OAuth remain deferred.

## Separate writer

For the separate restricted writer, prepare an ignored `.local/writer.env` using
[configuration](configuration.md#separate-writer-deployment). Keep its Redmine URL and caller
restrictions private. Default pinned-key mode requires a key digest and admitted user IDs;
personal-key mode requires an empty digest and supports an optional write-only user list.
Use ordinary users with the least native permissions for the intended projects.

Choose the needed IDs from the [tool reference](tool-reference.md), for example
`create_project_version` with `manage_versions` or membership writers with `manage_members`.
An empty `REDMINE_WRITER_OPERATIONS` permits no mutations. Standalone `allowed_all` expands to
all 18 registered writes and future registered writes after upgrade; use explicit CSV IDs for
a fixed ceiling. No configuration choice bypasses native permissions or per-request gates.

Once the configuration and intended write scope have been reviewed, start only the writer
profile with its own Compose project:

```bash
docker compose -p redmine-mcp-writer --env-file .local/writer.env -f deploy/compose.yaml --profile writer up -d --build mcp-writer
```

It listens on `127.0.0.1:8001` unless `MCP_WRITER_HOST_PORT` is set. The reader deployment
continues to use port 8000; base Compose forces its `REDMINE_WRITE_ENABLED=false`.
Changing the env-file requires recreating the writer service with the startup command above;
refresh client connections and tool lists afterward. Personal-key discovery is caller-specific
and reports candidates, not guaranteed target access. Direct/cached calls still enforce current gates.
Do not share `docker compose config` output because it includes the writer key digest.

For a synthetic writer, use the already marked synthetic instance with its own ignored writer
configuration and a reachable Redmine URL. Do not add the synthetic override to this separate
writer project: the existing synthetic instance owns its database and files. For an external
writer, use only the base Compose file and the external instance's ordinary user permissions;
seed/reset/restore helpers remain inapplicable.

Writes have one upstream attempt and separate acceptance/verification fields. A timeout,
lost response, interruption, or mutation HTTP 500-599 may leave an uncertain outcome.
Reconcile the actual target in Redmine before attempting again, preserving already accepted
batch peers. A failed read-back does not undo acceptance. See
[write semantics](tool-reference.md#mutation-uncertainty) and membership batch contracts.

The [2026-10-07 ledger](testing/evidence/current-catalog-acceptance.md) records current functional acceptance.
`/health` remains process liveness and does not contact Redmine. Complete writer audit, metrics,
CI, deployment/rollback and recovery acceptance remain deferred outside the current
local-development roadmap. Existing logs and Compose healthchecks do not establish these
guarantees.

## Troubleshooting

| Symptom | Action |
|---|---|
| Docker engine unavailable | Start Docker Desktop with Linux containers. |
| Port occupied | Free the port reported for the selected version; stop container MCP before local execution. |
| MCP/REST `401` | Check the personal Redmine API key header; Inspector's own token is separate. |
| Redmine key rejected | Check the requesting user's API key and account access. |
| TLS connection failure | Configure trusted certificates; keep verification enabled. |
| Synthetic marker rejected | Verify you selected the synthetic configuration; do not bypass validation. |
| Seed interrupted | Correct the cause, then explicitly reset if synthetic data is disposable. |
| Restore failed | Keep applications stopped and follow the restore recovery guidance above. |

Use the [manual verification guide](manual-verification.md) after startup or relevant changes.
