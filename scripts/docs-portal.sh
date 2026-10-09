#!/usr/bin/env bash
set -euo pipefail

DOCS_REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DOCS_REPO_ROOT"

if ! command -v python >/dev/null 2>&1; then
  printf 'Python 3.13 is required on PATH.\n' >&2
  exit 1
fi

case "${1:-}" in
  export)
    [[ $# -eq 1 ]] || { printf 'Usage: bash scripts/docs-portal.sh export\n' >&2; exit 2; }
    python src/redmine_mcp_docs/tools/portal.py export
    ;;
  serve)
    [[ $# -le 2 ]] || { printf 'Usage: bash scripts/docs-portal.sh serve [port]\n' >&2; exit 2; }
    python src/redmine_mcp_docs/tools/portal.py serve "${2:-8080}"
    ;;
  *)
    printf 'Usage: bash scripts/docs-portal.sh {export|serve [port]}\n' >&2
    exit 2
    ;;
esac
