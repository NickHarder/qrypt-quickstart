#!/bin/sh
# The tracer bullet's proving command (`make e2e`): the quickstart end to end, against the mock.
#
# It starts the mock Qrypt server on a free local port, runs the Python quickstart the way a
# developer does (a copy in an empty folder, a token in the environment), counts the snippet's
# lines, builds the site into build/site and checks that the page shows exactly the file it ran.
# No request leaves the machine: QRYPT_API_URL points the snippet at the mock.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PYTHON="$ROOT/.venv/bin/python"
[ -x "$PYTHON" ] || { echo "e2e: no .venv; run make bootstrap first" >&2; exit 3; }

PORT=$("$PYTHON" -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
MOCK_URL="http://127.0.0.1:$PORT/api/v1/quantum-entropy"
WORK_DIRECTORY=$(mktemp -d)

"$PYTHON" -m qrypt_quickstart.mock_server --port "$PORT" &
MOCK_PID=$!
trap 'kill "$MOCK_PID" 2>/dev/null; rm -rf "$WORK_DIRECTORY"' EXIT INT TERM

# Wait for the mock to listen, for up to five seconds.
"$PYTHON" - "$PORT" <<'EOF'
import socket, sys, time
for _attempt in range(50):
    try:
        socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=0.1).close()
        sys.exit(0)
    except OSError:
        time.sleep(0.1)
sys.exit("e2e: the mock did not start")
EOF

echo "e2e: the Python quickstart, against the mock at $MOCK_URL"
cp "$ROOT/quickstart/python/quickstart.py" "$WORK_DIRECTORY/"
(cd "$WORK_DIRECTORY" && env QRYPT_API_URL="$MOCK_URL" QRYPT_API_KEY=mock-200 "$PYTHON" quickstart.py)

echo "e2e: the snippet's length"
"$PYTHON" -m qrypt_quickstart.snippet_lines "$ROOT/quickstart/python/quickstart.py"

echo "e2e: the site"
"$PYTHON" -m qrypt_quickstart.site_builder --out "$ROOT/build/site"
"$PYTHON" - "$ROOT" <<'EOF'
import html, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
page = (root / "build" / "site" / "index.html").read_text()
shown = [html.unescape(code) for code in re.findall(r'<code class="language-python">(.*?)</code>', page, re.S)]
if shown != [(root / "quickstart" / "python" / "quickstart.py").read_text()]:
    sys.exit("e2e: the page does not show the snippet that ran")
print("e2e: the page shows exactly the snippet that ran")
EOF
echo "e2e: green"
