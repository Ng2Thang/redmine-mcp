# Detailed DEBUG logging

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../configuration.md#separate-writer-deployment).

## Implementation contract

Implemented on 2026-10-09 under the user's approved console-only logging plan. Existing
`LOG_LEVEL` is the sole switch, defaults to `INFO`, and requires process restart/container
recreation to apply. No dependencies, tool schemas, operation IDs, writer gates, retry
policies, managed log files, or deployment defaults are added or changed.

Application DEBUG events trace MCP/REST, authentication and authorization, capability
evidence, upstream attempts/admission, retry decisions, pagination, read budgets and write
receipts. Each MCP tool invocation and discovery request receives a fresh server-generated
`call_id`, including catalog rejection. The compatibility facade supplies the original HTTP
request correlation; internal REST and upstream work inherit it through context variables.
Context is restored in `finally`, including cancellation paths.

Templates live in `constants/logs.py`. Endpoint normalization and bounded stack inspection
run only at DEBUG. Stack diagnostics contain at most 20 file/function/line locations, without
source, locals or exception values. Logging never consumes additional request/response data,
performs network requests, retries writes or adds per-chunk events. Unknown operation names
and endpoints use fixed placeholders. HTTP/MCP vendor loggers stay at WARNING and their
records reaching the application console omit vendor message/exception contents.

The existing INFO request/upstream/retry events remain. `call_id` is an additive console
field, with `-` outside logical MCP calls. Authentication before SDK dispatch is HTTP-level
work and can therefore have `call_id=-`. A catalog rejection inside a decoded SDK call has
its own call ID. No call ID is added to public responses.

Activation and filtering commands are documented in [development](../development.md#debug-logging).
The complete metadata policy is in [configuration](../configuration.md#detailed-debug-logs).

## Verification handoff

This assignment authorizes code review and static checks only. No automated tests are
created or run, no application is started, and no Inspector, Docker deployment or live
Redmine operation is invoked. Functional acceptance remains pending separate authorization.

Use the existing offline fixtures and log capture facilities for future unit/integration
verification; no new packages are required. Live verification requires the owned synthetic
environment, separate reader/writer deployments and admitted personal keys. Writes must use
owned fixtures with cleanup, and failure injection must stay offline or in that environment.

| Scenario | Expected evidence |
|---|---|
| INFO/DEBUG and repeated configuration | DEBUG events appear only when enabled; no duplicate handlers, filters or console records; preconfigured root handlers format correlation fields correctly |
| Concurrent MCP tool calls and discovery | Distinct call IDs, HTTP correlation recovered through the compatibility facade, matching internal REST/upstream IDs, and context restored afterward |
| Unknown/disabled calls and invalid arguments | A call ID and truthful completion outcome; caller-supplied operation text and arguments absent from logs |
| Authentication and deployment gates | Fixed reasons for missing/duplicate headers, invalid/pinned keys, user gates, reader-only writes and disabled operations; no key or hash logged |
| Capability decisions | `conditional`, `unknown` and `denied` remain distinct without claiming native authorization |
| Upstream and retry branches | Attempt/status/timing/byte/dispatch metadata, admission wait/timeout, retry/stop reasons, and no additional requests |
| Pagination and budgets | Limit/offset/depth events, request/byte/deadline exhaustion, one budget summary per owned scope, and no per-chunk log flood |
| Writes | Accepted/uncertain/rejected transport receipts remain truthful for native rejection, server errors and connection/cleanup failures; no mutation retry |
| Sensitive sentinel values | Values placed in headers, cookies, keys/hashes, arguments, URLs, filenames, bodies and exception messages/locals never appear, including vendor ERROR records |
| Error stack metadata | At most 20 code locations with truncation indicator; no exception message, source lines, locals or raw traceback; no stack inspection at INFO |
| Cancellation and streaming errors | Context reset, streams closed and permits released with unchanged cancellation/error responses |
| Local and Docker deployments | Reader/writer honor the same level, container recreation applies changes, and returning to INFO disables diagnostics |

## Static review results (2026-10-09)

- `bash scripts/doctor.sh`: passed through Git Bash outside the sandbox after sandboxed Bash
  startup failed with Windows `CreateFileMapping` access denial.
- Ruff lint and formatting checks: passed for all 13 modified Python files.
- `mypy src/redmine_mcp`: passed for all 129 application source files.
- Architecture check: passed, reporting 131 modules checked.
- `git diff --check`: passed.
- Full `bash scripts/check.sh`: not clean because unchanged files have four Ruff lint errors,
  five formatting failures, and seven mypy errors. Lint findings are in API dependencies,
  the attachment router, the user capability service, and the retry helper; formatting also
  affects body limits, MCP compatibility and documentation portal tools. Mypy findings are
  limited to `src/redmine_mcp_docs/tools/portal.py` and `vendor_assets.py`.

These unrelated baseline files were not modified. Static review checked correlation restoration,
endpoint/operation allowlists, guarded stack extraction, vendor sanitization, receipt handling
and preservation of request/stream/budget control flow. No functional tests or live verification
were performed, and these results do not establish runtime acceptance.
