# Security policy

## Project status

Redmine MCP is a development implementation for pilot evaluation. Automated authentication,
session isolation, permission gates and selected native permission/state checks have passing
evidence in the [2026-10-07 acceptance ledger](docs/plans/current-catalog-acceptance.md).
Complete permission matrices, operational readiness and full restore validation remain open.
No production certification, supported release matrix, SLA or response deadline is promised.
See the [testing roadmap](docs/testing-roadmap.md).

## Report a vulnerability privately

Contact a repository maintainer through an established private contact channel. If you cannot
find one, ask a maintainer how to report privately without posting vulnerability details.
This repository does not publish a dedicated security address or promise an enabled reporting
service. Do not disclose credentials, exploit details, private issues, or snapshots in public issues.

Include the affected revision, component, impact, and minimal reproduction steps using synthetic
data. Supply redacted logs and relevant configuration names, never secret values. Maintainers
will assess the report and coordinate remediation and disclosure through the private channel.

## Configuration and data handling

- Each caller supplies a personal Redmine API key; Redmine controls that user's visibility.
  Implemented mutations require a separate opt-in writer, configured operation ceiling,
  caller admission and native permissions. The default reader remains read-only. Use ordinary
  users with the least needed roles instead of an administrator key.
- The server verifies each key against Redmine and resolves the requesting user ID. Application
  policy explicitly registers read/write operation permissions. Pinned-key writer mode requires
  a matching private digest and admitted user ID; personal-key mode authenticates each caller
  and can apply a write-only user list. Capability evidence is request-local; conditional or
  unknown evidence is not a permission grant. Redmine remains authoritative on invocation.
- Every MCP HTTP request reauthenticates. Stateful sessions bind to user, Redmine issuer and
  a private key fingerprint; another user/key receives 404, and key rotation requires a new
  session. Termination, expiry and shutdown remove session binding. No cross-request key or
  role cache is used. Discovery candidates are separate from invocation authorization.
- Standalone `allowed_all` permits all registered writes, including additions after upgrade;
  an explicit operation list keeps the scope fixed. An empty list permits no mutations.
- Mutations are attempted once. Received HTTP 500-599 and potentially dispatched failures
  require reconciliation; no automatic retry or rollback is promised. Accepted writes can have
  unavailable or mismatched verification. Safe timing logs are not a complete writer audit.
- Keep `.env`, `.local/`, API keys, and database/attachment snapshots out of Git,
  logs, screenshots, and public reports. Rotate exposed credentials through their issuing systems.
- Keep published development ports bound to localhost. Hosting, HTTPS ingress, and OAuth are
  deferred; do not treat the development Compose setup as a production deployment guide.
- Keep TLS verification enabled and configure trusted certificates when needed.
- Treat Redmine text as untrusted data, not instructions for an agent or tool runner.
- Use seed, reset, and restore helpers only with the marked synthetic environment. Restore only
  trusted snapshots from compatible repository and image versions.

See [configuration](docs/configuration.md) and [operations](docs/operations.md) for details.
