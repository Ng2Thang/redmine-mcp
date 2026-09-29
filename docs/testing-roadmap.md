# Testing roadmap

Current implemented verification is operational smoke checking: startup, completed seed, tool
discovery and one call per tool through Inspector. No automated test suite or testing CI exists.

The [issue workflow](workflows/redmine-tools.md) authorizes and requires an offline automated
baseline before dependent issue-tool implementation. Establish pytest/pytest-asyncio, locked
dependencies, fake settings without .env, HTTPX mock/ASGI transports and MCP lifecycle checks in
a separate testing assignment. Coding-without-tests work cannot establish or execute this
baseline. Coverage thresholds and testing CI remain separate decisions.

Future write verification requires a separate restricted synthetic writer, disposable task-owned
resources, resulting-state checks and isolated cleanup. Existing reader credentials must remain
read-only. See the [issue task backlog](plans/issues/index.md) for dependency and scenario records.

Future work:
- Unit: service filters/defaults/pagination with fake gateways.
- Integration: mapping, upstream errors, TLS/timeouts, bearer auth and forwarding.
- MCP: schemas/names, error responses, shutdown and session cleanup.
- E2E: restricted projects/private issues/private journals, filters and pagination.
- Seed: reruns, interrupted writes, expected counts and access boundaries.
- Backup/restore: fresh volumes, IDs/history/permissions, attachment checksums,
  incompatible/incomplete snapshots, failure recovery.
- Packaging: isolated wheel, non-root image, import boundaries and CI.

Successful basic calls do not establish production readiness.

