#!/bin/sh
# Record the real output of the commands the demo's Terminal scenes show, into demo/terminal/.
#
# Each runs as the scene says, against the local mock of Qrypt (no request leaves the machine): the
# Python quickstart with a good token, the same program with a token Qrypt refuses (the mock answers
# 401 to mock-401), and `make grader-run`, which times the README's grader quick-start from a fresh
# clone. Run from the repository root after `make bootstrap`: demo/terminal/capture.sh
set -eu

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PYTHON="$ROOT/.venv/bin/python"
OUT="$ROOT/demo/terminal"
WORK_DIRECTORY=$(mktemp -d)
PORT=$("$PYTHON" -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')

"$PYTHON" -m qrypt_quickstart.mock_server --port "$PORT" >/dev/null 2>&1 &
MOCK_PID=$!
trap 'kill "$MOCK_PID" 2>/dev/null; rm -rf "$WORK_DIRECTORY"' EXIT INT TERM
"$PYTHON" -c "
import socket, sys, time
for _attempt in range(50):
    try:
        socket.create_connection(('127.0.0.1', $PORT), timeout=0.1).close()
        sys.exit(0)
    except OSError:
        time.sleep(0.1)
sys.exit('capture: the mock did not start')
"

cp "$ROOT/quickstart/python/quickstart.py" "$WORK_DIRECTORY/"
MOCK_URL="http://127.0.0.1:$PORT/api/v1/quantum-entropy"
(cd "$WORK_DIRECTORY" && env QRYPT_API_URL="$MOCK_URL" QRYPT_API_KEY=mock-200 "$PYTHON" quickstart.py) \
  > "$OUT/quickstart-success.txt" 2>&1
(cd "$WORK_DIRECTORY" && env QRYPT_API_URL="$MOCK_URL" QRYPT_API_KEY=mock-401 "$PYTHON" quickstart.py) \
  > "$OUT/quickstart-401.txt" 2>&1 || true
(cd "$ROOT" && make --no-print-directory grader-run) > "$OUT/grader-run.txt" 2>&1
echo "capture: wrote $(ls "$OUT"/*.txt | wc -l) outputs to demo/terminal/"
