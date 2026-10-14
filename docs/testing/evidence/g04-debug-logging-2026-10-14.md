# G04: DEBUG logging acceptance

Date: 2026-10-14. Status: complete for LOG-01..05 within the offline scope.

The user explicitly assigned G04/G05 and deferred P2 work. Base revision:
`2938733394a72ddf0fcfda7632a7a93bdd47a41f`, plus preserved earlier local changes.
G04 adds **54 cases** in `tests/unit/test_observability.py` and
`tests/integration/test_debug_logging.py`. `tests/logging_helpers.py` captures the actual
configured console handler, filter and formatter and restores global logging state.
Runtime code and dependencies did not change.

| Plan | Accepted behavior |
| --- | --- |
| LOG-01 | Repeated INFO/DEBUG/WARNING configuration, intended event levels, no duplicate handlers/filters and restoration of global logger/handler state |
| LOG-02 | Interleaved discovery, successful tools and unknown-tool rejection have distinct call IDs; internal requests/upstream work share the owning correlation; nested failures and cancellation restore parent contexts |
| LOG-03 | Keys, cookies, URLs/query arguments, JSON/binary bodies, filenames, upload tokens and exception values stay out of formatted output; vendor WARNING/ERROR strips arguments, cached exception text, `exc_info` and stack text |
| LOG-04 | Known endpoints/operations are retained and unknown input becomes a placeholder; stack output has at most 20 code locations without source/locals/exception values; INFO does not inspect tracebacks |
| LOG-05 | INFO/DEBUG preserve selected read retries/delays, malformed-read refusal, cancellation, write acceptance/rejection/uncertainty, response closure and semaphore release |

Final related regression: **199 passed**, zero failures/errors/skips, exit 0, **26.66 seconds**.
It includes all 54 new cases and existing read-retry/runtime foundation coverage. One existing
Pydantic deprecation warning remains. Scoped Ruff lint and format checks passed.

```bash
mkdir -p .local/testing/g04-2026-10-14
uv run --frozen pytest tests/unit/test_observability.py \
  tests/integration/test_debug_logging.py tests/unit/test_read_retries.py \
  tests/integration/test_runtime_foundation.py -q --tb=short -o junit_family=xunit1 \
  --junitxml=.local/testing/g04-2026-10-14/regression.xml
uv run --frozen ruff check tests/logging_helpers.py \
  tests/unit/test_observability.py tests/integration/test_debug_logging.py
uv run --frozen ruff format --check tests/logging_helpers.py \
  tests/unit/test_observability.py tests/integration/test_debug_logging.py
```

Private artifacts: `regression.log` and `regression.xml` in the directory above. JUnit xunit1
is explicitly selected to preserve existing properties without xunit2 reporting warnings.
The first run had 44 passes and eight test-authoring failures: pytest inserts capture handlers
between fixture setup and the call phase, a dynamic filename had a valid basename, and the
write harness called the wrong API. Correcting those assumptions produced 52 passing cases
and a 197-case regression. Binary-upload sentinels and actual ASGI unexpected-error handling
were then added before the final 199-case run. No production defect was identified.

The complete G03 offline baseline remains dated at 2,885 cases; this focused result is not a
new full-suite total. Live logging/Inspector, external collectors, arbitrary third-party
handlers, performance benchmarks and operational assurance are outside this acceptance.
