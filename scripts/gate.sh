#!/usr/bin/env bash
# The gate: the one definition of "may this change go in".
#
#     make gate                 (from the repo root; the same thing)
#     scripts/gate.sh [--only lint,tests] [--keep-logs]
#     scripts/gate.sh --list-checks | --check <name> | --checks <lint|tests>  [--from project|kit]
#
# .githooks/pre-push runs this before a push leaves the machine. It costs nothing and needs no network
# and no API key.
#
# Groups, run side by side (scripts/kit.conf lists the ones this project has):
#   lint     skill frontmatter (scripts/check_skills.sh); the knowledge bundle in docs/, and that no
#            Markdown file sits outside it unlisted (scripts/okf_bundle.py); ruff check, ruff format
#            --check, mypy --strict, and the rules those cannot check
#            (scripts/check_python_rules.py), on the code and on docs/'s attesters
#   tests    pytest
#   lint and tests also run the project's own checks, in any language: one a line,
#            `<group> <name>: <command>`, in scripts/checks.kit.conf (the kit's presets, from this
#            project's answers) and scripts/checks.conf (the project's own, which no update touches).
#            Each runs from the repository's root; a `tests` check gives any project a tests group.
#   evals    the eval suite's core tier, replayed from recordings and compared with evals/baseline.json
#   secrets  gitleaks over the commits a push would send (scripts/secrets_scan.sh)
#
# --list-checks prints the checks; --check runs one by name; --checks runs one group's checks and
# nothing else (CI's job for them). --from reads one file only: project (scripts/checks.conf) or kit
# (scripts/checks.kit.conf). A line of a checks file the gate cannot read is a bad argument.
#
# Exit 0: every group passed. Exit 1: at least one failed; what failed and why is printed.
# Exit 3: the machine is not set up (run `make bootstrap`). Exit 64: bad arguments.

# `--help` prints the comment above, down to the blank line. What follows is for whoever edits this.
# Written for bash 3.2, which is what macOS ships: no `wait -n`, no associative arrays, no mapfile.
# The run_* functions are called by name ("run_$group"), which shellcheck cannot follow (SC2317, and
# SC2329 in newer versions).
# shellcheck disable=SC2317,SC2329
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
CONF="$ROOT/scripts/kit.conf"
[ -f "$CONF" ] || { echo "gate: scripts/kit.conf is missing" >&2; exit 3; }
# shellcheck source=/dev/null
. "$CONF"
SERVICE="$ROOT/${SERVICE_DIR:-.}"
BIN="$SERVICE/.venv/bin"
# Every group this script knows, in the order they are reported.
KNOWN="lint tests evals secrets"
# The groups a project's own check can be in, and the files that list the checks, in the order run.
CHECK_GROUPS="lint tests"
CHECK_FILES="scripts/checks.kit.conf scripts/checks.conf"
CHECK_PATTERN='^([a-z]+)[[:space:]]+([A-Za-z0-9._-]+):[[:space:]]*(.+)$'
TAB=$(printf '\t')

only=""
keep_logs=0
mode=gate
mode_argument=""
while [ $# -gt 0 ]; do
  case "$1" in
    --only)
      [ $# -ge 2 ] || { echo "gate: --only needs a value, e.g. --only lint,tests" >&2; exit 64; }
      only="$2"
      shift 2
      ;;
    --keep-logs) keep_logs=1; shift ;;
    --list-checks) mode=list; shift ;;
    --from)
      [ $# -ge 2 ] || { echo "gate: --from needs project or kit" >&2; exit 64; }
      case "$2" in
        project) CHECK_FILES="scripts/checks.conf" ;;
        kit) CHECK_FILES="scripts/checks.kit.conf" ;;
        *) echo "gate: --from takes project or kit, not '$2'" >&2; exit 64 ;;
      esac
      shift 2
      ;;
    --check | --checks)
      [ $# -ge 2 ] || { echo "gate: $1 needs a value" >&2; exit 64; }
      mode=${1#--}
      mode_argument="$2"
      shift 2
      ;;
    -h | --help)
      awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
      exit 0
      ;;
    *) echo "gate: unknown argument: $1 (try --help)" >&2; exit 64 ;;
  esac
done

# Is $1 in the comma-separated list $2?
in_list() {
  case ",$2," in *",$1,"*) return 0 ;; esac
  return 1
}

want() {
  in_list "$1" "$only"
}

unreadable() {
  echo "gate: $1" >&2
  exit 64
}

# CHECKS holds one line a check: group, name, where it is written (file:line) and command, by tabs.
CHECKS=""
read_checks() {
  local relative_path line_number line place group name command
  for relative_path in $CHECK_FILES; do
    [ -f "$ROOT/$relative_path" ] || continue
    line_number=0
    while IFS= read -r line || [ -n "$line" ]; do
      line_number=$((line_number + 1))
      line="${line#"${line%%[![:space:]]*}"}"
      case "$line" in '' | '#'*) continue ;; esac
      place="$relative_path:$line_number"
      [[ $line =~ $CHECK_PATTERN ]] ||
        unreadable "$place: not a check: '$line' (one a line: <group> <name>: <command>)"
      group=${BASH_REMATCH[1]}
      name=${BASH_REMATCH[2]}
      command=${BASH_REMATCH[3]}
      in_list "$group" "${CHECK_GROUPS// /,}" ||
        unreadable "$place: '$group' is not a group a check can be in (${CHECK_GROUPS// / or })"
      if [ -n "$(check_named "$name")" ]; then
        unreadable "$place: the check '$name' is named twice"
      fi
      CHECKS="$CHECKS$group$TAB$name$TAB$place$TAB$command
"
    done <"$ROOT/$relative_path"
  done
}

# The line of CHECKS for the check of that name, or nothing.
check_named() {
  printf '%s' "$CHECKS" | awk -F "$TAB" -v name="$1" '$2 == name { print; exit }'
}

# Fail closed on a check whose program is not installed: it must not look like a check that passed.
# A command that starts by setting a variable is left to run.
require_check_program() {
  local program=${3%%[[:space:]]*}
  case "$program" in *=*) return 0 ;; esac
  (cd "$ROOT" && command -v "$program" >/dev/null 2>&1) && return 0
  echo "gate: $2: the check '$1' runs '$program', which is not installed" >&2
  echo "gate: install it (scripts/checks.conf says how), then run the gate again." >&2
  return 3
}

# Each check of the groups named (comma-separated) must have its program.
require_check_programs() {
  printf '%s' "$CHECKS" | {
    local group name place command
    while IFS="$TAB" read -r group name place command; do
      in_list "$group" "$1" || continue
      require_check_program "$name" "$place" "$command" || exit 3
    done
  } || exit 3
}

# Run every check of a group, from the repository's root, and stop at the first that fails.
run_checks() {
  local ran=0 group name place command
  while IFS="$TAB" read -r group name place command; do
    [ "$group" = "$1" ] || continue
    echo "check $name: $command"
    if ! (cd "$ROOT" && sh -c "$command" </dev/null); then
      echo "gate: check '$name' failed ($place)" >&2
      return 1
    fi
    ran=$((ran + 1))
  done <<CHECKS_END
$CHECKS
CHECKS_END
  [ "$ran" -eq 0 ] || echo "checks: $ran ok"
}

read_checks
case "$mode" in
  list)
    if [ -z "$CHECKS" ]; then
      echo "gate: no checks yet in ${CHECK_FILES// / or }"
    else
      printf '%s' "$CHECKS" | while IFS="$TAB" read -r group name place command; do
        printf '%-6s %s: %s  (%s)\n' "$group" "$name" "$command" "$place"
      done
    fi
    exit 0
    ;;
  check)
    found=$(check_named "$mode_argument")
    [ -n "$found" ] || unreadable "no check is named '$mode_argument' (make checks lists them)"
    CHECKS="$found
"
    group=${found%%"$TAB"*}
    require_check_programs "$group"
    run_checks "$group" || exit 1
    exit 0
    ;;
  checks)
    in_list "$mode_argument" "${CHECK_GROUPS// /,}" ||
      unreadable "--checks takes ${CHECK_GROUPS// / or }, not '$mode_argument'"
    require_check_programs "$mode_argument"
    run_checks "$mode_argument" || exit 1
    exit 0
    ;;
esac

# The groups this project has: those scripts/kit.conf names, and tests when a check is in it.
GROUPS_HERE="${GATE_GROUPS:-}"
if printf '%s' "$CHECKS" | cut -f1 | grep -qx tests && ! in_list tests "$GROUPS_HERE"; then
  GROUPS_HERE="${GROUPS_HERE:+$GROUPS_HERE,}tests"
fi
[ -n "$only" ] || only="$GROUPS_HERE"

# A group named with --only must be one this project has, and one this script runs: a typo, here or
# in scripts/kit.conf, must not look like a pass.
old_ifs=$IFS
IFS=,
for group in $only; do
  if ! in_list "$group" "$GROUPS_HERE"; then
    echo "gate: '$group' is not a group of this project (it has: ${GROUPS_HERE:-none})" >&2
    exit 64
  fi
  if ! in_list "$group" "${KNOWN// /,}"; then
    echo "gate: scripts/kit.conf names '$group', which this script does not run (it runs: $KNOWN)" >&2
    exit 64
  fi
done
IFS=$old_ifs
[ -n "$only" ] || { echo "gate: no groups to run (scripts/kit.conf has GATE_GROUPS empty)" >&2; exit 64; }

not_set_up() {
  echo "gate: $1" >&2
  echo "gate: run 'make bootstrap' from the repo root, then run the gate again." >&2
  exit 3
}

# Fail closed: a gate that cannot run must never look like a gate that passed.
if [ "${PYTHON_SERVICE:-0}" = "1" ] && { want lint || want tests || want evals; }; then
  [ -x "$BIN/python" ] || not_set_up "there is no virtualenv at ${SERVICE_DIR:-.}/.venv"
  for tool in ruff mypy pytest; do
    [ -x "$BIN/$tool" ] || not_set_up "${SERVICE_DIR:-.}/.venv has no '$tool'"
  done
fi
if want evals; then
  [ -x "$BIN/${EVALS_COMMAND:-}" ] || not_set_up "${SERVICE_DIR:-.}/.venv has no '${EVALS_COMMAND:-eval runner}'"
  [ -d "$ROOT/evals/cases" ] || not_set_up "evals/cases is missing"
fi
require_check_programs "$only"
if want secrets && ! command -v gitleaks >/dev/null 2>&1; then
  echo "gate: gitleaks is not installed, so the secret scan cannot run." >&2
  if [ "$(uname -s)" = "Darwin" ]; then how="brew install gitleaks"; else how="make tools"; fi
  echo "gate: install it with '$how', then run the gate again." >&2
  exit 3
fi
# The bundle check runs through uv, from what `make bootstrap` left in uv's cache: here it never
# reaches for the network.
if want lint; then
  command -v uv >/dev/null 2>&1 ||
    not_set_up "'uv' is not installed, so the bundle check (scripts/okf_bundle.py) cannot run"
  UV_OFFLINE=1 "$ROOT/scripts/okf_bundle.py" --version >/dev/null 2>&1 ||
    not_set_up "the bundle check (scripts/okf_bundle.py) is not ready to run offline"
fi

LOGS=$(mktemp -d "${TMPDIR:-/tmp}/gate.XXXXXX")

run_lint() {
  "$ROOT/scripts/check_skills.sh" || return 1
  # With an eval suite, the bundle check also reads what each case guards and which metric it feeds.
  # It is told where the repository is, so that it holds the names in docs/ to their convention and
  # every Markdown file outside docs/ to the list that docs/ keeps.
  if [ "${EVALS:-0}" = "1" ]; then
    (cd "$ROOT" && UV_OFFLINE=1 scripts/okf_bundle.py check docs --evals evals --repository .) || return 1
  else
    (cd "$ROOT" && UV_OFFLINE=1 scripts/okf_bundle.py check docs --repository .) || return 1
  fi
  if [ "${PYTHON_SERVICE:-0}" = "1" ]; then
    (cd "$SERVICE" && "$BIN/ruff" check . && "$BIN/ruff" format --check . && "$BIN/mypy" &&
      "$BIN/python" "$ROOT/scripts/check_python_rules.py" src tests "$ROOT/docs" &&
      lint_attesters) || return 1
  fi
  run_checks lint
}

# The attesters are the Python files under docs/: code that decides whether a number stands, so
# they are held to what the project's own code is held to. docs/ is outside the Python layer when
# that is a subdirectory, so ruff is told which settings to use. Each attester is read on its own:
# two may share a file name, and no two are one program.
lint_attesters() {
  find "$ROOT/docs" -name '*.py' -print | sort | while IFS= read -r attester; do
    "$BIN/ruff" check --config pyproject.toml "$attester" || exit 1
    "$BIN/ruff" format --check --config pyproject.toml "$attester" || exit 1
    "$BIN/mypy" --strict "$attester" || exit 1
  done
}

run_tests() {
  if [ "${PYTHON_SERVICE:-0}" = "1" ]; then
    (cd "$SERVICE" && "$BIN/pytest" -q) || return 1
  fi
  run_checks tests
}

run_evals() {
  # GATE_EVALS_OUT keeps results.json, summary.md and junit.xml somewhere of the caller's choosing
  # (CI publishes them); otherwise they go with the gate's logs.
  cd "$SERVICE" && "$BIN/$EVALS_COMMAND" --mode replay --tier core --compare-baseline \
    --out "${GATE_EVALS_OUT:-$LOGS/evals/results}"
}

run_secrets() {
  # The pre-push hook sets GATE_RANGE to the commits being pushed; without it the script works out
  # what a push would send.
  if [ -n "${GATE_RANGE:-}" ]; then
    "$ROOT/scripts/secrets_scan.sh" "$GATE_RANGE"
  else
    "$ROOT/scripts/secrets_scan.sh"
  fi
}

started=$(date +%s)
groups=""
pids=""
for group in $KNOWN; do
  want "$group" || continue
  mkdir -p "$LOGS/$group"
  (
    begin=$(date +%s)
    "run_$group" >"$LOGS/$group/out.log" 2>"$LOGS/$group/err.log"
    code=$?
    echo "$code" >"$LOGS/$group/exit"
    echo $(($(date +%s) - begin)) >"$LOGS/$group/seconds"
    exit "$code"
  ) &
  groups="$groups $group"
  pids="$pids $!"
done

echo "gate: running$groups"
for pid in $pids; do
  wait "$pid" || true
done

# What a person needs to see to act on a red group, and nothing else.
explain() {
  group=$1
  out="$LOGS/$group/out.log"
  err="$LOGS/$group/err.log"
  case "$group" in
    evals)
      # Each failing case once, then the totals, what tripped, and the versions that were under test.
      # An id has the shape the trace gives it (scripts/okf/trace.py): up to five capitals.
      grep -hE '^[A-Z]{1,5}-[0-9]{2,} +FAIL' "$out" 2>/dev/null | head -25
      grep -hE '^[0-9]+ cases:' "$out" 2>/dev/null
      grep -hE '^(VIOLATION|runner error|versions:|A cassette miss)' "$err" 2>/dev/null | head -20
      ;;
    *)
      # pytest ends its output with what failed and the totals; what stopped it before any test ran
      # is in the error log.
      tail -40 "$out"
      tail -20 "$err"
      ;;
  esac
}

failed=""
for group in $groups; do
  code=$(cat "$LOGS/$group/exit" 2>/dev/null || echo 99)
  seconds=$(cat "$LOGS/$group/seconds" 2>/dev/null || echo "?")
  if [ "$code" = "0" ]; then
    summary=$(grep -hE '^([0-9]+ passed|[0-9]+ cases:|skills:|Success:|secrets:|checks:)' "$LOGS/$group/out.log" | tail -1)
    printf 'gate: %-7s ok      %4ss  %s\n' "$group" "$seconds" "$summary"
  else
    printf 'gate: %-7s FAILED  %4ss  (exit %s)\n' "$group" "$seconds" "$code"
    failed="$failed $group"
  fi
done

if [ -z "$failed" ]; then
  echo "gate: green in $(($(date +%s) - started))s"
  if [ "$keep_logs" = "1" ]; then echo "gate: logs kept in $LOGS"; else rm -rf "$LOGS"; fi
  exit 0
fi

echo
for group in $failed; do
  echo "---- why '$group' failed ----"
  explain "$group"
  echo
done
if [ "${GATE_CONTEXT:-}" = "pre-push" ]; then
  echo "==== PUSH BLOCKED: the gate is red (${failed# }) ===="
else
  echo "==== GATE RED: ${failed# } ===="
fi
echo "Full logs: $LOGS"
exit 1
