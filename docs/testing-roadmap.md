# Deferred testing roadmap

Current scope is operational smoke checking only: startup, completed seed, tool discovery,
and one call per tool through Inspector. No automated test suite or testing CI is included.

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

