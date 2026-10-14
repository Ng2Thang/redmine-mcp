# Repository and documentation alignment audit

Date: 2026-10-14. Scope: source and prose review of the current first-party repository.
This record describes documentation corrections, not runtime acceptance or a production release.

## Review scope

Reviewed the following sources alongside their maintained documentation:

- Runtime settings, authentication, operation registration and REST route contracts; the
  connected catalog was also inspected during the earlier tool documentation refresh.
- Base and versioned synthetic Compose files, Docker packaging, development launchers,
  local environment selection, plugin installation, seed and backup/reset/restore helpers.
- E2E profile selection and preparation fixtures as source, pytest configuration, and
  contributor/quality-check configuration. No test or preparation code was executed.
- README, security and contributor guidance, current canonical guides, the roadmap and
  coverage summaries, and portal user, contributor, maintenance and verification pages.
- Docsify publication inventory, exported-file selection, routing, logging descriptions,
  and browser-library versions recorded in the bundled asset manifest.

Historical task plans, dated acceptance ledgers, sample exports and third-party plugin/library
documentation are records of their stated scope. They were not rewritten to imply acceptance
of current code. External client interfaces and remote reference URLs were not exercised.

## Findings and corrections

| Area | Mismatch | Correction and source |
| --- | --- | --- |
| Environment template | Comments claimed `dev-up.sh` generates `.env` and secrets and described writer key hashes/user IDs | Align comments with `scripts/local_env.py`, versioned Compose and `config.py`; preserve template values and the example write subset |
| Writer ports | General writer examples used 8001 without distinguishing the 7.0.2 Redmine port or optional synthetic writers | Document base writer 8001, built-in writers 8004/8003, empty synthetic operation ceilings, and a free-port example for a separate writer |
| Configuration forwarding | Retry and membership-budget guidance did not distinguish base Compose from fixed synthetic environments | State which settings base Compose forwards and that built-in stacks ignore dotenv configuration |
| Account admission | Architecture/development/module-map prose still mentioned account admission or writer admission modes | Use authenticated personal-key identity, configured operation gates, and native permissions; distinguish upstream capacity admission |
| Deployment architecture | Architecture still described combining base Compose with a synthetic override | Document standalone versioned synthetic profiles and base Compose for an existing Redmine |
| Backup/restore lifecycle | "Stops MCP" could imply all writers were stopped by the wrappers | State that wrappers manage `mcp-server` and `redmine` only; optional/separate writers need their own maintenance lifecycle |
| Logging | Request-flow prose said vendor exception text and REST error bodies could reach the application console | Align with `observability.py`: vendor records are reduced to `vendor_diagnostic details_omitted=true`; client tool errors are separate |
| Acceptance boundaries | Operations called the 2026-10-07 ledger current acceptance | Label its earlier 17-read/15-write scope and link the later catalog status without changing recorded results |
| Links and ports | Manual/testing links targeted a nonexistent roadmap heading; a mutable E2E summary still named port 3002; contributor links pointed to the wrong guides | Use `catalog-status-2026-10-09`, current 7.0.2 port 8001, the actual module map, and the actual portal checklist |
| Portal checklist | Expected retired-route redirects, copied root/source files, refusal of unmarked output, and outdated menu/screenshot details | Align proposed checks with `portal.py`, current guides, and navigation: retired routes use 404; unmarked output is preserved; only inventoried files are copied |
| Portal publication | Source-only publishing can omit technical pages and generated search paths | Explicitly require `.local/docs-portal/site/` after export; keep source ownership and generated output separate |
| Package metadata | `pyproject.toml` described the entire project as read-only | Describe REST/MCP tools with a read-only default and optional writer; dependencies and wheel contents are unchanged |

## Confirmed source alignment

- The registered catalog still contains 18 reads and 18 writes. The default reader exposes
  no mutations. The full inventory is in the [tool reference](../tool-reference.md#tools-and-inputs).
- Runtime setting defaults match the canonical configuration table, including bounded GET
  retries, reader/membership budgets, and the derived request-body cap. Base Compose does not
  forward `REDMINE_MAX_REQUEST_BODY_BYTES`; the existing caveat remains applicable.
- Built-in development and E2E profiles select separate 6.0.1/7.0.2 projects and fixed ports.
  E2E alone adds the host evidence overlay and automatic fixture preparation.
- Python 3.13 and the FastAPI-MCP 0.4.0/MCP 1.30.0 compatibility pins agree with contributor
  guidance. The wheel and runtime Docker image include the runtime package, not the portal.
- The four commands in `scripts/check.sh`, three opt-in pre-commit hooks, offline default
  pytest discovery, and explicit live E2E gate agree with the maintained instructions.
- Portal publication combines sidebar pages with retained Overview references. Bundled asset
  versions agree with the portal maintenance guide. Source and exported copies remain distinct.

## Verification limits and handoff

Review used file reads, text searches and manual diff/prose/link inspection only. No unit,
integration or E2E tests, quality-check tools, automated link checker, package build, Docker
commands, fixture preparation, services, browser checks, Inspector calls, live Redmine requests,
or deployment were run for this audit. Local static export generation is a separate artifact
step and is not functional verification.

Existing TOOL-040 testing waiver, pending TOOL-041 acceptance and testcase reruns, BUG-001
investigation, version-specific setup gaps, and release/operational/recovery limitations remain
open as recorded in the [roadmap](../plans/index.md). These corrections do not close them.
