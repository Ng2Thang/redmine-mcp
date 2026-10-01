# Testing roadmap

Current verification includes a credential-free offline baseline and operational smoke checking:
startup, completed seed, tool discovery and one call per tool through Inspector. Testing CI does
not yet exist.

The [tool workflow](workflows/redmine-tools.md) requires an offline automated
baseline before dependent reader-tool implementation. The baseline uses locked pytest and
pytest-asyncio dependencies, fake settings without `.env`, HTTPX mock/ASGI transports, and MCP SDK
session checks. Run it from Git Bash without Docker or credentials:

```bash
uv run --frozen pytest
```

The suite covers the current three tools at the REST boundary and MCP discovery, invocation,
authentication, validation, and error envelopes. Opt-in live synthetic checks remain separate;
coverage thresholds and testing CI remain separate decisions.

Future write verification requires a separate restricted synthetic writer, disposable task-owned
resources, resulting-state checks and isolated cleanup. Existing reader credentials must remain
read-only. See the [MCP tool dashboard](plans/index.md) for dependency and scenario records.

Future work:
- Unit: service filters/defaults/pagination with fake gateways.
- Integration: mapping, upstream errors, TLS/timeouts, personal-key authentication and forwarding.
- MCP: schemas/names, error responses, shutdown and session cleanup.
- E2E: restricted projects/private issues/private journals, filters and pagination.
- Seed: reruns, interrupted writes, expected counts and access boundaries.
- Backup/restore: fresh volumes, IDs/history/permissions, attachment checksums,
  incompatible/incomplete snapshots, failure recovery.
- Packaging: isolated wheel, non-root image, import boundaries and CI.

Successful basic calls do not establish production readiness.

## Per-user authentication scenarios for a separately authorized test stage

Do not create or run automated tests for this change without separate authorization. When
authorized, cover these scenarios with mocked Redmine responses and REST/MCP requests:

- Two distinct keys resolve different Redmine user IDs. Interleaved and concurrent calls forward
  each key only to its own `/users/current.json` and resource requests; `me` remains upstream.
- Missing, blank, duplicate, and rejected keys return 401 before a resource request. MCP
  connection and tool discovery reject invalid keys. No key appears in tool arguments or errors.
- A malformed current-user response, timeout, transport error, and later key revocation yield
  sanitized 502, 504, 502, and 401 responses respectively.
- Visibility scope is `requesting_redmine_user`; existing operation IDs, inputs, pagination, and
  response wrappers remain stable. The write gate remains closed on reader deployments.

