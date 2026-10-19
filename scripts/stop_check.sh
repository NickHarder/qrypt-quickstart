#!/bin/sh
# The check before a turn ends. The Stop hook in .claude/settings.json runs this script each time
# Claude Code is about to hand the turn back:
#
#     scripts/stop_check.sh [<check command>...]     (default: scripts/gate.sh --only lint)
#
# When the turn left tracked files changed or new files beside them (`git status --porcelain`), it
# runs the check. Red (exit 1) keeps the turn going: exit 2, with the check's last lines on stderr,
# which Claude Code hands the model as the reason to go on. It does so up to MAX_BLOCKS times in a
# row; a stop that follows one of its blocks says so (`stop_hook_active` in the JSON on stdin), and
# the count, kept in a file of the session's own in git's folder, starts again at any other stop. After the last
# try the turn ends, and the owner is told the check is still red. A clean tree and a green check
# end the turn. A check that cannot run at all (any other exit: a tool missing, the project not
# bootstrapped) never blocks: it is said to the owner as a system message, and the turn ends.
#
# POSIX sh.
set -u

REPORT_LINES=40
MAX_BLOCKS=3

# Prints a system message for the owner as Claude Code reads it: JSON, with control characters
# dropped, tabs as spaces, and quotes and backslashes escaped.
tell_the_owner() {
  message=$(printf '%s' "$1" |
    tr -d '\000-\010\013-\037' | tr '\t' ' ' |
    sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | awk '{ printf "%s\\n", $0 }')
  printf '{"systemMessage": "%s"}\n' "$message"
}

stop=$(cat)
session=$(printf '%s' "$stop" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0
# The session's id, as a file name: only letters, digits, - and _.
session_name=$(printf '%s' "${session:-unknown}" | tr -c 'A-Za-z0-9_-' '_')
count_file=$(git rev-parse --git-path "stop-check-blocks-$session_name")

blocks_so_far=0
if printf '%s' "$stop" | grep -Eq '"stop_hook_active"[[:space:]]*:[[:space:]]*true' &&
  [ -f "$count_file" ]; then
  blocks_so_far=$(cat "$count_file")
fi
case $blocks_so_far in '' | *[!0-9]*) blocks_so_far=0 ;; esac

if [ -z "$(git status --porcelain)" ]; then
  rm -f "$count_file"
  exit 0
fi

[ $# -gt 0 ] || set -- scripts/gate.sh --only lint
report=$("$@" 2>&1)
code=$?
last_lines=$(printf '%s\n' "$report" | tail -n "$REPORT_LINES")

case $code in
  0)
    rm -f "$count_file"
    exit 0
    ;;
  1)
    try_number=$((blocks_so_far + 1))
    if [ "$try_number" -gt "$MAX_BLOCKS" ]; then
      rm -f "$count_file"
      tell_the_owner "$(printf 'stop check: "%s" is still red after %s tries; the turn ends with it red:\n%s' \
        "$*" "$MAX_BLOCKS" "$last_lines")"
      exit 0
    fi
    printf '%s\n' "$try_number" >"$count_file"
    printf 'stop check: "%s" is red after the changes of this turn (try %s of %s); fix what it names, then hand back:\n%s\n' \
      "$*" "$try_number" "$MAX_BLOCKS" "$last_lines" >&2
    exit 2
    ;;
  *)
    tell_the_owner "$(printf 'stop check: "%s" could not run (exit %s):\n%s' "$*" "$code" "$last_lines")"
    exit 0
    ;;
esac
