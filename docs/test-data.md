# Synthetic data

## Quick usage and reading notes

Run from the repository root in Git Bash after the marked Redmine/PostgreSQL services are ready:

```bash
bash scripts/seed.sh base     # Original small dataset; also the default with no argument
bash scripts/seed.sh history  # Add or resume history after a complete baseline
bash scripts/seed.sh all      # Bootstrap, baseline, then history
```

Choose one mode for the dataset you need. `bash scripts/seed.sh --help` explains the modes.
`bash scripts/dev-up.sh 7.0.2` or `bash scripts/dev-up.sh 6.0.1` starts the selected services
and creates both baseline and history datasets. The seed command
does not start services. The existing `bash scripts/seed-history.sh` command forwards to history.
These commands write synthetic data; they do not run application tests or prepare live E2E data.

Seed helpers default to 7.0.2. For example, run
`REDMINE_TEST_VERSION=6.0.1 bash scripts/seed.sh history` for the 6.0.1 development stack.
Development manifests, checkpoints and credentials live in each project's `seed_state`
Docker volume at `/seed-state`; the helpers require no host env file.

E2E uses a separate fixture generator, `tools/testing/e2e_seed.rb`, on the same selected
versioned database. `REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e`
starts and prepares that stack automatically; `dev-up.sh` and the large datasets are optional.
Built-in E2E state lives in `.local/e2e/<project>/`, mounted at `/e2e-state` through the
E2E overlay. Do not copy IDs or credentials between versions, seed manifests, or legacy
E2E directories. See [reset boundaries](testing-roadmap.md#reset-and-migration) before
discarding data: resetting the database also invalidates manifests retained outside it.

All Python dataset logic is in [`tools/seed/generate.py`](../tools/seed/generate.py).
Read it in this order:

1. `STATE`, `KIND` and `save`: container state directory, environment marker and atomic checkpoints.
2. `generate_base`: private projects/memberships, Unicode issues/notes, relation and attachments.
3. `PROJECTS`, `Redmine` and `ensure_*`: history definitions, REST helper and creation stages.
4. `generate_history`: prerequisites, Linux lock, existing-record reconciliation and resume.
5. `main`: mode selection; `all` completes baseline before beginning history.

Edit fixture content and quantities in `generate.py`. The old `generator.py` and `history.py`
were removed after consolidation; `__init__.py` and `__main__.py` provide package entry points.
`bootstrap.rb` stays separate because Redmine configuration requires its Rails runtime.
Python imports do not create data. History execution uses a Linux-only lock inside Docker;
its deferred import lets the generator module be imported on Windows.

For direct container execution, use `python -m tools.seed base`, `python -m tools.seed history`
or `python -m tools.seed all`. The removed `tools.seed.generator` and `tools.seed.history`
module paths are no longer supported. The Git Bash commands above remain the normal workflow.

Baseline generation creates 4 projects and 150 issues. History adds 8 projects, 20 users,
12 versions, 300 issues and 900 time entries: 12 generated projects, 450 issues and 900 time
entries across both datasets. These totals exclude unrelated records and the separate owned
E2E fixture environment described in [the testing roadmap](testing-roadmap.md).

Recovery note: a completed stage skips generation on rerun. An interrupted baseline requires
the existing guarded synthetic reset; interrupted history resumes from its own manifest.
`all` preserves both rules and stops if the baseline is incomplete. No automatic reset is added.
Keep both manifests separate and never edit credentials or progress files by hand.

Implementation note, 2026-10-06: the Python generators were consolidated and reading notes added.
Seed execution and automated tests were not run for this refactor; dataset equivalence and live
resume behavior still require separately authorized verification.

## Baseline dataset

Bootstrap requires redmine-mcp-synthetic-v1 and refuses unknown nonempty instances.
It sets a dedicated application title; Git Bash helpers validate internal Compose and volume markers.

Rails creates default configuration, roles, users and custom fields. Python calls REST
to create four private projects, memberships, 150 issues, comments, transitions, relations
and two attachments. Failed requests stop processing. The manifest becomes complete only
after all operations succeed.

Distribution: 110 main, 20 child, 20 restricted issues. Two accessible-project issues are private.
Expected reader count with status_id=* is 128; this is not an automated permission-test result.
MCP Reader has view_issues, default issue visibility, no private-note permission,
and membership in main/child/empty only.

Vietnamese fixture text intentionally exercises Unicode; documentation remains English.

Artifacts in each project's `seed_state` Docker volume, mounted at `/seed-state` in Redmine:

- `environment.json`: environment marker.
- `credentials.json`: sensitive API keys and configuration IDs.
- `manifest.json`: progress, IDs, privacy cases, attachment names.
- Backups use the separate `backup_data` volume, mounted at `/state/backups` by the ops service.

Completed seeds skip reruns; interrupted seeds require reset rather than resume.
Read IDs from the manifest after reset. Only restore trusted snapshots with matching versions.
Full restore, permission, checksum and failure-recovery validation is deferred.

## Optional three-month history

Run `bash scripts/seed-history.sh` after the base seed to add a larger manual-testing fixture.
It requires the same marked synthetic environment and does not alter the original records.
The command adds two parent projects and six subprojects, 20 users, 12 versions used as sprints,
300 issues, and 900 time entries. Seven new projects are visible to MCP Reader; the eighth,
`History Beta Private`, is restricted. Each parent owns six 15-day versions shared with its
subprojects. Issue schedules and time-entry work dates cover the 90 days before the command's
first run, using the seed container's UTC date. Record creation timestamps remain current.

The Docker-volume file `/seed-state/history-manifest.json` records the date anchor, IDs, progress,
and completion status. A completed command skips reruns. An interrupted run resumes and
reconciles records created just before a checkpoint. A synthetic reset removes this manifest;
backups and restores include it when present. Do not edit it by hand.

For examples, read `projects.alpha-api`, `projects.beta-private`, `versions.alpha:01`,
`issues.001`, and `time_entries.001-1` from the history manifest. IDs change after a reset.
The base manifest's 128 visible issues remain; the expanded fixture adds 263 visible issues,
for 391 total visible issues with `status_id="*"` when no other manual changes have been made.
The restricted project contains 37 of the new issues. Time entries can be checked in Redmine's
Spent time pages and through `list_issue_time_entries` for a visible issue.

