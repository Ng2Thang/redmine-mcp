#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || exit 2
cd "$REPO_ROOT" || exit 2

check_only=false
offline=false
fix_imports=false
verify=false

usage() {
  cat <<'USAGE'
Usage: bash scripts/fix-quality.sh [--check-only] [--fix-imports] [--verify] [--offline]

Apply formatting with a syntax-tree guard, then check convention, typing, architecture,
complexity, security candidates and locked runtime dependency advisories.
Diagnostics and a final summary are displayed directly in the terminal.

  --check-only  Run checks without applying source fixes or formatting.
  --fix-imports Additionally fix import ordering (I001); review import side effects.
  --verify      Explicitly run offline unit/integration tests and build distributions.
                Real-server/container smoke checks and E2E are not included.
  --offline     Disable uv network access and skip the dependency advisory query.
                The skipped query makes the run incomplete (exit 2).
  -h, --help    Show this help without running tools or changing files.

Default edits are formatting only. Other lint fixes are never applied automatically.
Typing, security, architecture and complexity findings require source review.
Tests and builds run only when --verify is explicitly selected.
Exit: 0 = no diagnostics, 1 = review needed, 2 = failed/skipped checks.
USAGE
}

for argument in "$@"; do
  case "$argument" in
    --check-only) check_only=true ;;
    --offline) offline=true ;;
    --fix-imports) fix_imports=true ;;
    --verify) verify=true ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$argument" >&2; usage >&2; exit 2 ;;
  esac
done

if "$check_only" && "$fix_imports"; then
  echo '--check-only cannot be combined with --fix-imports.' >&2
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  echo 'uv is required. Install uv, then run uv sync --frozen --group audit.' >&2
  exit 2
fi

export PYTHONUTF8=1 RADONFILESENCODING=UTF-8
if "$offline"; then
  export UV_OFFLINE=1
fi

# Synchronize once; every tool below uses that same locked environment.
if ! uv sync --frozen --group audit; then
  echo 'Dependency setup failed; no source fixes or checks were attempted.' >&2
  exit 2
fi

targets=(src/redmine_mcp scripts tools/seed)
uv_command=(uv run --frozen --no-sync --group audit)
review_count=0
error_count=0
summary=()
format_guard_passed=true
ast_snapshot=''

cleanup_snapshot() {
  if [[ -n "$ast_snapshot" ]]; then
    rm -f -- "$ast_snapshot"
  fi
}
trap cleanup_snapshot EXIT

run_step() {
  local mode="$1" label="$2" result output message
  shift 2
  printf '\n--- %s ---\n' "$label"

  if [[ "$mode" == metric ]]; then
    # With -n C and no average/header options, Radon emits only review candidates.
    # Capture stderr too: unexpected warnings must not be interpreted as clean.
    output="$("$@" 2>&1)"
    result=$?
    if [[ -n "$output" ]]; then
      printf '%s\n' "$output"
    fi
  else
    "$@"
    result=$?
    output=''
  fi

  if (( result == 0 )); then
    if [[ "$mode" == metric && -n "$output" ]]; then
      message='REVIEW: complexity candidates or diagnostics shown above'
      review_count=$((review_count + 1))
    else
      message='COMPLETED'
    fi
  elif (( result == 1 )) && [[ "$mode" == fix ]]; then
    # Formatting may resolve an outstanding lint diagnostic. Final checks decide status.
    message='FIXES ATTEMPTED: remaining diagnostics will be checked again'
  elif (( result == 1 )) && [[ "$mode" == check ]]; then
    message='REVIEW: nonzero tool result; inspect diagnostics above'
    review_count=$((review_count + 1))
  else
    message="ERROR: command exited with status $result"
    error_count=$((error_count + 1))
  fi
  summary+=("$label: $message")
  printf '%s\n' "$message"
  return "$result"
}

if ! "$check_only"; then
  if "$fix_imports"; then
    # Restrict both diagnostics and fixes; never use the entire project rule set to fix.
    run_step fix 'Apply import ordering fixes only' \
      "${uv_command[@]}" ruff check "${targets[@]}" \
        --select I001 --fixable I001 --fix --no-unsafe-fixes
  fi
  if mkdir -p .local/code-quality && \
    ast_snapshot="$(mktemp .local/code-quality/format-ast.XXXXXX)"; then
    # Capture after opt-in import fixes, so only formatter changes are compared.
    if run_step required 'Capture pre-format syntax trees' \
      "${uv_command[@]}" python scripts/check_format_semantics.py \
        snapshot "$ast_snapshot" "${targets[@]}"; then
      run_step required 'Apply Ruff formatting' \
        "${uv_command[@]}" ruff format "${targets[@]}"
      if ! run_step required 'Confirm formatting preserved syntax trees' \
        "${uv_command[@]}" python scripts/check_format_semantics.py \
          compare "$ast_snapshot" "${targets[@]}"; then
        format_guard_passed=false
      fi
    else
      format_guard_passed=false
      summary+=('Formatting: SKIPPED (syntax-tree snapshot failed)')
    fi
  else
    format_guard_passed=false
    error_count=$((error_count + 1))
    summary+=('Formatting: ERROR (cannot create syntax-tree snapshot)')
  fi
fi

run_step check 'Ruff convention' \
  "${uv_command[@]}" ruff check "${targets[@]}" --no-fix
run_step check 'Ruff formatting' \
  "${uv_command[@]}" ruff format --check "${targets[@]}"
run_step check 'Strict mypy (all src)' "${uv_command[@]}" mypy src
run_step check 'Architecture boundaries and cycles' \
  "${uv_command[@]}" python scripts/check_architecture.py
run_step metric 'Radon runtime complexity above 10' \
  "${uv_command[@]}" radon cc src/redmine_mcp -s -n C
run_step metric 'Radon support complexity above 10' \
  "${uv_command[@]}" radon cc scripts tools/seed -s -n C
run_step check 'Bandit runtime candidates' "${uv_command[@]}" bandit -r src/redmine_mcp
run_step check 'Bandit support candidates' "${uv_command[@]}" bandit -r scripts tools/seed

if "$offline"; then
  summary+=('Runtime dependency advisories: SKIPPED (offline mode)')
  error_count=$((error_count + 1))
elif ! mkdir -p .local/code-quality; then
  summary+=('Runtime dependency advisories: ERROR (cannot create input directory)')
  error_count=$((error_count + 1))
else
  if run_step required 'Export locked runtime requirements' \
    uv export --locked --no-dev --no-default-groups --no-emit-project \
      --no-hashes --no-header --no-annotate --format requirements-txt \
      --output-file .local/code-quality/runtime-requirements.txt; then
    run_step check 'Runtime dependency advisories' \
      "${uv_command[@]}" pip-audit \
        --requirement .local/code-quality/runtime-requirements.txt \
        --no-deps --disable-pip --progress-spinner off --timeout 15
  else
    summary+=('Runtime dependency advisories: SKIPPED (requirements export failed)')
  fi
fi

if "$verify"; then
  if "$format_guard_passed"; then
    # --verify is explicit opt-in. Never select live E2E or service startup here.
    run_step required 'Offline unit and integration regression' \
      "${uv_command[@]}" pytest tests/unit tests/integration
    run_step required 'Build source and wheel distributions' \
      uv build --no-sources --out-dir .local/code-quality/build
  else
    summary+=('Tests/build: SKIPPED (formatting syntax-tree guard failed)')
  fi
else
  summary+=('Tests/build: NOT REQUESTED (use --verify to opt in)')
fi

printf '\nQuality check summary\n'
printf '  %s\n' "${summary[@]}"
printf '\nReview the diagnostics and source diff before accepting changes.\n'
printf 'No broad lint fixes, suppression edits or project dependency upgrades were performed.\n'
printf 'Syntax-tree checks and offline verification do not establish real deployment acceptance.\n'

if (( error_count > 0 )); then
  echo 'Result: incomplete checks or execution errors (exit 2).'
  exit 2
fi
if (( review_count > 0 )); then
  echo 'Result: remaining diagnostics or complexity candidates need review (exit 1).'
  exit 1
fi
echo 'Result: configured static commands reported no remaining diagnostics (exit 0).'
exit 0
