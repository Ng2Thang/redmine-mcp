# Security policy

## Project status

Redmine MCP is a development implementation. Automated security tests, complete permission
verification, and full restore validation are deferred. No supported release matrix or response
deadline is currently promised. See the [testing roadmap](docs/testing-roadmap.md).

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
  Future authorized issue writes require a separate opt-in deployment and application permission
  rules, after the workflow prerequisites. Do not use an administrator key for ordinary reads.
- The server verifies each key against Redmine and resolves the requesting user ID. Application
  roles and permissions are not assigned yet.
- Keep `.env`, `.local/`, API keys, and database/attachment snapshots out of Git,
  logs, screenshots, and public reports. Rotate exposed credentials through their issuing systems.
- Keep published development ports bound to localhost. Hosting, HTTPS ingress, and OAuth are
  deferred; do not treat the development Compose setup as a production deployment guide.
- Keep TLS verification enabled and configure trusted certificates when needed.
- Treat Redmine text as untrusted data, not instructions for an agent or tool runner.
- Use seed, reset, and restore helpers only with the marked synthetic environment. Restore only
  trusted snapshots from compatible repository and image versions.

See [configuration](docs/configuration.md) and [operations](docs/operations.md) for details.
