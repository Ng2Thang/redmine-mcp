#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
cd "$REPO_ROOT" || exit 1

failures=0

ok() {
  printf '[OK] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
  failures=$((failures + 1))
}

info() {
  printf '[INFO] %s\n' "$1"
}

printf 'Redmine MCP development doctor\n'
printf 'Repository: %s\n\n' "$REPO_ROOT"

if [[ -n "${MSYSTEM:-}" ]]; then
  ok "Git Bash (${MSYSTEM})"
else
  fail 'Run this script in Git Bash on Windows.'
fi

if command -v git >/dev/null 2>&1; then
  ok "Git ($(git --version))"
else
  fail 'Git is missing from PATH.'
fi

if command -v python >/dev/null 2>&1; then
  python_version="$(python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null)"
  if [[ "$python_version" == 3.13.* ]]; then
    ok "Python $python_version"
  else
    fail "Python 3.13 is required; python on PATH reports ${python_version:-an error}."
  fi
else
  fail 'Python 3.13 is missing from PATH.'
fi

if command -v uv >/dev/null 2>&1; then
  uv_version="$(uv --version 2>/dev/null)"
  if [[ -n "$uv_version" ]]; then
    ok "$uv_version ($(command -v uv))"
  else
    fail 'uv is on PATH but cannot run.'
  fi
else
  fail 'uv is missing from PATH; uv run and scripts/check.sh will fail.'
  if command -v python >/dev/null 2>&1 && python -m pip show uv >/dev/null 2>&1; then
    scripts_dir="$(python -c 'import sysconfig; print(sysconfig.get_path("scripts", scheme="nt_user"))' 2>/dev/null)"
    info 'The uv Python package is installed, but Git Bash cannot find its executable.'
    if [[ -n "$scripts_dir" ]] && command -v cygpath >/dev/null 2>&1; then
      scripts_dir="$(cygpath -u "$scripts_dir")"
      if [[ -f "$scripts_dir/uv.exe" ]]; then
        printf '[INFO] For this session: export PATH="%s:$PATH"\n' "$scripts_dir"
      else
        info 'Check the Python Scripts directory for uv.exe and add it to Git Bash PATH.'
      fi
    fi
  else
    info 'Install uv, then restart Git Bash and rerun this script.'
  fi
fi

for file in .python-version pyproject.toml uv.lock; do
  if [[ -f "$file" ]]; then
    ok "$file exists"
  else
    fail "$file is missing; run the doctor from this repository checkout."
  fi
done

if [[ -f .venv/pyvenv.cfg ]]; then
  info '.venv exists; run uv sync --frozen to confirm locked dependencies.'
else
  info '.venv is absent; run uv sync --frozen after required checks pass.'
fi

if [[ -f .env ]]; then
  info '.env exists; its contents were not read.'
else
  info '.env is absent; it is only needed for configured runtime workflows.'
fi

printf '\nOptional workflow tools:\n'
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  ok "Docker Compose ($(docker compose version --short))"
else
  info 'Docker Compose is unavailable; the synthetic environment cannot start.'
fi

if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  ok "Node.js $(node --version) and npm $(npm --version)"
else
  info 'Node.js/npm is unavailable; MCP Inspector cannot run.'
fi

printf '\n'
if (( failures == 0 )); then
  ok 'Required development prerequisites are ready.'
  info 'Next: uv sync --frozen, then bash scripts/check.sh.'
else
  fail_count="$failures"
  printf '[FAIL] %d required prerequisite(s) need attention.\n' "$fail_count"
  exit 1
fi
