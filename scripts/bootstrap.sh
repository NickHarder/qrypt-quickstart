#!/usr/bin/env bash
# Set a fresh clone up to run the gate:   make bootstrap   (from the repo root), then   make gate
#
# Installs the Python environment, the TypeScript packages, the Go module's tools and the Rust
# toolchain their lock files pin (scripts/kit.conf says where each project lives), readies the
# bundle check (scripts/okf_bundle.py, which uv runs from its own lock file), writes the index files
# of docs/ when there are none, and turns on the repo's git hooks. Needs network once, for PyPI (and
# npm, the Go proxy or rustup, with those layers). It needs no API key and no .env.
#
# Safe to run again. Written for bash 3.2 (macOS).
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck source=/dev/null
. "$ROOT/scripts/kit.conf"

# Every project needs uv: it runs the bundle check, with or without a Python layer.
if ! command -v uv >/dev/null 2>&1; then
  echo "bootstrap: 'uv' is not installed. Install it, then run this again:" >&2
  echo "    curl -LsSf https://astral.sh/uv/install.sh | sh        (https://docs.astral.sh/uv/)" >&2
  exit 3
fi

# The first run fetches what scripts/okf_bundle.py.lock pins; the gate then runs it offline.
if ! bundle_check_version=$("$ROOT/scripts/okf_bundle.py" --version); then
  echo "bootstrap: the bundle check (scripts/okf_bundle.py) could not be readied; it needs PyPI once" >&2
  exit 3
fi
echo "bootstrap: the bundle check is ready ($bundle_check_version)"

# An index is written from the concepts in its directory, so a new project has none yet.
if [ ! -f "$ROOT/docs/index.md" ]; then
  (cd "$ROOT" && scripts/okf_bundle.py index docs >/dev/null)
  echo "bootstrap: no docs/index.md yet; wrote the index files of the bundle in docs/ (commit them)"
fi

if [ "${PYTHON_SERVICE:-0}" = "1" ]; then
  cd "$ROOT/${SERVICE_DIR:-.}"
  # A virtualenv from another project must not be mistaken for this one's.
  unset VIRTUAL_ENV
  if [ -f uv.lock ]; then
    echo "bootstrap: installing the locked environment into ${SERVICE_DIR:-.}/.venv"
    uv sync --frozen
  else
    echo "bootstrap: no uv.lock yet; resolving and writing one (commit it)"
    uv sync
  fi
  echo "bootstrap: $(.venv/bin/python --version), $(.venv/bin/ruff --version), $(.venv/bin/mypy --version)"
  if [ "${API_PROJECT:-0}" = "1" ] && [ ! -f schemas/openapi.json ]; then
    echo "bootstrap: no schemas/openapi.json yet; exporting it from the code (commit it)"
    ".venv/bin/${OPENAPI_EXPORT}"
  fi
fi

# The TypeScript layer's packages, from its lock file: the gate's ts- checks run them offline.
if [ -n "${TYPESCRIPT_DIR:-}" ]; then
  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "bootstrap: Node and npm are not installed, so the TypeScript checks cannot run. Install Node 26," >&2
    echo "    the version $TYPESCRIPT_DIR/.nvmrc names (https://nodejs.org, or nvm), then run this again." >&2
    exit 3
  fi
  if [ -f "$ROOT/$TYPESCRIPT_DIR/package-lock.json" ]; then
    echo "bootstrap: installing the locked TypeScript packages into $TYPESCRIPT_DIR/node_modules"
    npm ci --prefix "$ROOT/$TYPESCRIPT_DIR" --no-audit --no-fund
  else
    echo "bootstrap: no $TYPESCRIPT_DIR/package-lock.json yet; resolving and writing one (commit it)"
    npm install --prefix "$ROOT/$TYPESCRIPT_DIR" --no-audit --no-fund
  fi
  echo "bootstrap: node $(node --version), npm $(npm --version)"
fi

# The Go module's toolchain, dependencies and tools (staticcheck, govulncheck), which go.mod pins:
# the gate's go- checks then run offline.
if [ -n "${GO_DIR:-}" ]; then
  if ! command -v go >/dev/null 2>&1 || ! command -v gofmt >/dev/null 2>&1; then
    echo "bootstrap: Go is not installed, so the Go checks cannot run. Install Go 1.27, the version" >&2
    echo "    $GO_DIR/go.mod names (https://go.dev/dl), then run this again." >&2
    exit 3
  fi
  echo "bootstrap: downloading the Go module's dependencies and tools into the module cache"
  go -C "$ROOT/$GO_DIR" mod download
  echo "bootstrap: $(go -C "$ROOT/$GO_DIR" version)"
fi

# The Rust crate's toolchain, which rust-toolchain.toml pins, and its crates from Cargo.lock: the
# gate's rust- checks then run offline.
if [ -n "${RUST_DIR:-}" ]; then
  if ! command -v rustup >/dev/null 2>&1 || ! command -v cargo >/dev/null 2>&1; then
    echo "bootstrap: rustup and cargo are not installed, so the Rust checks cannot run. Install rustup" >&2
    echo "    (https://rustup.rs); this run then installs Rust 1.99, the version $RUST_DIR/rust-toolchain.toml names." >&2
    exit 3
  fi
  echo "bootstrap: installing Rust 1.99 with rustfmt and clippy, and fetching the crate's dependencies"
  rustup toolchain install 1.99 --profile minimal --component rustfmt,clippy
  cargo +1.99 fetch --manifest-path "$ROOT/$RUST_DIR/Cargo.toml" --locked
  echo "bootstrap: $(cargo +1.99 --version)"
fi

if [ -d "$ROOT/.githooks" ]; then
  if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$ROOT" config core.hooksPath .githooks
    echo "bootstrap: git hooks on (core.hooksPath=.githooks); a push now runs the gate first"
  else
    echo "bootstrap: not a git repository yet; run 'git init', then 'make bootstrap' again for the hooks" >&2
  fi
fi

echo "bootstrap: done. Next:  make gate"
