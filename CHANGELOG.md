# Changelog

Changes are recorded here before a release is published. Version metadata alone does not imply
that a release has been published.

## Unreleased

### Added

- Issue requirement analysis, reviewed task backlog, and explicit testing/contract blockers.
- Disabled-by-default write authorization prerequisite and separate writer deployment settings;
  current tools remain read-only. Compose supports a configurable localhost MCP host port.

- Read-only project listing, issue listing, and issue detail tools through REST and MCP.
- Shared-account Redmine access with MCP bearer authentication and paginated results.
- Synthetic Redmine/PostgreSQL development environment and separate data-operation helpers.
- EditorConfig, Python version selection, optional Flake8 compatibility settings, optional
  pre-commit checks, and a shared Git Bash quality-check command.
- Inactive Codecov configuration; automated testing and coverage remain deferred.
- Configuration, tool reference, manual verification, development, and operations guides.
- Security reporting guidance and a project code of conduct.

### Changed

- Organized README and contributor guidance around quick start and task-specific documentation.
- Expanded architecture documentation and Git line-ending rules.
