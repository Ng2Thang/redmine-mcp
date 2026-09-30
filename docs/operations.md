# Operations

Run commands from the repository root in Windows Git Bash. Docker Desktop must be running with
Linux containers. These helpers manage the dedicated synthetic environment; external Redmine
uses the separate workflow below. See [configuration](configuration.md) for settings and secrets.

## Start and inspect the synthetic environment

```bash
bash scripts/dev-up.sh
```

The script generates marked local configuration if absent, starts PostgreSQL and Redmine, seeds
sample data, switches to the reader API key, and builds/starts MCP. First startup downloads and
builds images. It requires Python 3.13 on PATH and host ports 3000, 8000, and 5433 to be available.

| Service | Address |
|---|---|
| Redmine | `http://localhost:3000` |
| Swagger | `http://localhost:8000/docs` |
| MCP Streamable HTTP | `http://localhost:8000/mcp` |
| Liveness | `http://localhost:8000/health` |
| PostgreSQL | `localhost:5433`, database/user `redmine` |

For database clients, read `POSTGRES_PASSWORD` privately from `.env`. Synthetic accounts are
`admin`, `demo-manager`, `demo-developer`, `demo-reporter`, and `demo-mcp-reader`; their password
is `TEST_USER_PASSWORD`. The reader account represents MCP visibility.

Wrappers disable Git Bash path rewriting for Docker. For manual Compose operations, set:

```bash
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'
docker compose -p redmine-mcp-test --env-file .env -f deploy/compose.yaml -f deploy/compose.test.yaml ps
```

Do not share `docker compose config` output; it can expose interpolated credentials.

## Stop and restart

Stop all synthetic services while retaining volumes:

```bash
docker compose -p redmine-mcp-test --env-file .env -f deploy/compose.yaml -f deploy/compose.test.yaml stop
```

Restart using `bash scripts/dev-up.sh`. Completed seeds are skipped.
To free port 8000 for local Python while keeping Redmine running:

```bash
docker compose -p redmine-mcp-test --env-file .env -f deploy/compose.yaml -f deploy/compose.test.yaml stop mcp-server
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

Read IDs from `.local/manifest.json` after reset rather than assuming IDs remain the same.
See [synthetic data](test-data.md) for expected counts and visibility cases.

To add three months of project, sprint-version, issue, and spent-time history to an already
seeded synthetic instance, run:

```bash
bash scripts/seed-history.sh
```

This adds 8 projects, 20 users, 12 versions, 300 issues, and 900 time entries. It preserves
the base dataset, skips a completed rerun, and resumes an interrupted run. Read generated IDs
from `.local/history-manifest.json`. Run the command a second time to confirm it reports a skip.
In Redmine, inspect the History Alpha/Beta project trees, memberships, versions, issue schedules,
and Spent time reports. In MCP Inspector, use manifest project and issue IDs to check visible
projects, versions, and issues, then confirm `History Beta Private` is inaccessible to MCP Reader.
The existing MCP tools do not read time entries. See [synthetic data](test-data.md) for counts
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
and a completion marker under `.local/backups/<snapshot-id>/`. Its exit handler attempts to
restart applications even when backup fails. Incomplete snapshots must not be used for restore.
Existing snapshots are not overwritten. Treat every snapshot as sensitive.

Restore replaces the current synthetic database, attachments, and local state:

```bash
bash scripts/restore.sh baseline
```

Only restore trusted snapshots from matching repository and image versions. The helper checks
the synthetic markers, completion marker, Redmine/PostgreSQL image versions, dump listing, and
archive readability. It restores the database, replaces attachments, refreshes the reader key,
and restarts applications on success. These checks do not establish full recovery correctness.

If restore fails, MCP and Redmine remain stopped. Inspect the failure privately, verify snapshot
compatibility and completeness, and correct the cause before retrying a trusted restore. Do not
restart applications into a partially restored state. Reset is only an alternative when the current
synthetic data can be discarded. Full restore, checksum, and failure-recovery validation is deferred.

## External Redmine

Prepare `.local/external.env` as described in [configuration](configuration.md). Stop any MCP
process already occupying port 8000. With the Git Bash Docker exports above in effect:

```bash
docker compose -p redmine-mcp-external --env-file .local/external.env -f deploy/compose.yaml up -d --build
```

This uses base Compose, which runs MCP only. Never add the synthetic override or invoke the
seed/reset/restore helpers for an external instance. Inside Docker, use `host.docker.internal`
for Redmine running on the Windows host. Hosting, HTTPS ingress, OAuth, and individual identities
remain deferred.

## Troubleshooting

| Symptom | Action |
|---|---|
| Docker engine unavailable | Start Docker Desktop with Linux containers. |
| Port occupied | Free 3000, 8000, or 5433 as applicable; stop container MCP before local execution. |
| MCP/REST `401` | Check the MCP bearer token; Inspector's own token is separate. |
| Upstream authentication error | Check the configured Redmine API key and account access. |
| TLS connection failure | Configure trusted certificates; keep verification enabled. |
| Synthetic marker rejected | Verify you selected the synthetic configuration; do not bypass validation. |
| Seed interrupted | Correct the cause, then explicitly reset if synthetic data is disposable. |
| Restore failed | Keep applications stopped and follow the restore recovery guidance above. |

Use the [manual verification guide](manual-verification.md) after startup or relevant changes.
