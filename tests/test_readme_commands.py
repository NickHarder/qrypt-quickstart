"""Every shell block of README.md runs as written, against the mock (Phase 11).

The grader quick-start runs in `test_readme_and_ai_usage.py`, in a folder of its own. The other
blocks run here, from the repository's root, in the shell a reader has after `make bootstrap`:
the virtualenv is not activated, so a bare `python` is not the project's. Three kinds of line are
checked rather than run, and say so:

- `make <target>`: the target must exist. `bootstrap` installs, and `agent-round` runs Claude Code
  in Docker with the owner's login; neither belongs in a test.
- `docker build -t <tag> <folder>`: the folder must hold a Dockerfile.
- `export <NAME>=...`: a placeholder for a credential; the harness must pass that variable on.

A line the README says runs "in one terminal", or a static file server, is started in the
background, must answer on its port, and is stopped once the block's other lines have run.
"""

import os
import re
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

import pytest

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
README: Final = REPOSITORY_ROOT / "README.md"
MAKEFILE: Final = REPOSITORY_ROOT / "Makefile"
HARNESS: Final = REPOSITORY_ROOT / "src" / "qrypt_quickstart" / "agent_harness.py"
SERVER_START_SECONDS: Final = 10.0


def readme_blocks() -> list[tuple[str, list[str]]]:
    """Return each bash block after the grader quick-start, by its section, as joined lines."""
    text = README.read_text().split("## Grader quick-start", 1)[1]
    blocks: list[tuple[str, list[str]]] = []
    for section in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        heading = section.splitlines()[0]
        for block in re.findall(r"```bash\n(.*?)```", section, re.DOTALL):
            joined = block.replace("\\\n", " ")
            blocks.append((heading, [line for line in joined.splitlines() if line.strip()]))
    return blocks


def command_of(line: str) -> str:
    """Return a README line without its trailing comment."""
    return line.split("  #", 1)[0].strip()


def is_background_server(line: str) -> bool:
    """Say whether a line starts a server the reader leaves running."""
    return "in one terminal" in line or " http.server " in command_of(line)


def port_of(command: str) -> int:
    """Return the port a server command listens on: after --port, or its last argument."""
    words = shlex.split(command)
    port_text = words[words.index("--port") + 1] if "--port" in words else words[-1]
    return int(port_text)


def wait_for_port(port: int) -> bool:
    """Wait until something listens on a local port, for a few seconds at most."""
    deadline = time.monotonic() + SERVER_START_SECONDS
    while time.monotonic() < deadline:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
        except OSError:
            time.sleep(0.1)
        else:
            return True
    return False


def readers_environment() -> dict[str, str]:
    """Return a reader's shell environment: no QRYPT_ variable, the virtualenv not on PATH."""
    virtualenv_bin = str(Path(sys.prefix) / "bin")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("QRYPT_")}
    environment.pop("VIRTUAL_ENV", None)
    environment["PATH"] = os.pathsep.join(
        entry for entry in environment["PATH"].split(os.pathsep) if entry != virtualenv_bin
    )
    return environment


def check_without_running(command: str) -> bool:
    """Check a line that must not run in a test; return False when the line is one to run."""
    words = shlex.split(command)
    if words[0] == "make":
        assert re.search(rf"^{re.escape(words[1])}:", MAKEFILE.read_text(), re.MULTILINE)
        return True
    if words[:2] == ["docker", "build"]:
        assert (REPOSITORY_ROOT / words[-1] / "Dockerfile").is_file()
        return True
    if words[0] == "export":
        variable_name = words[1].split("=", 1)[0]
        assert f'"{variable_name}"' in HARNESS.read_text()
        return True
    return False


@pytest.mark.parametrize(("section", "lines"), readme_blocks(), ids=lambda value: str(value)[:30])
def test_each_readme_block_runs_as_written(section: str, lines: list[str]) -> None:
    environment = readers_environment()
    servers: list[subprocess.Popen[bytes]] = []
    try:
        for line in lines:
            command = command_of(line)
            if check_without_running(command):
                continue
            if is_background_server(line):
                servers.append(
                    subprocess.Popen(  # noqa: S602  each line runs as a reader's shell runs it
                        command,
                        shell=True,
                        cwd=REPOSITORY_ROOT,
                        env=environment,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                    )
                )
                assert wait_for_port(port_of(command)), f"{section}: {command!r} did not start"
                continue
            completed = subprocess.run(  # noqa: S602  each line runs as a reader's shell runs it
                command,
                shell=True,
                check=False,
                cwd=REPOSITORY_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = completed.stdout + completed.stderr
            if "prints the 429 message" in line:
                assert "Qrypt answered HTTP 429" in output, output
                continue
            assert completed.returncode == 0, f"{section}: {command!r}: {output}"
    finally:
        for server in servers:
            server.terminate()
            server.wait(timeout=10)


def test_every_readme_block_is_covered() -> None:
    sections = {section for section, _ in readme_blocks()}
    assert {
        "Run the snippets",
        "Build the site",
        "Reproduce the agent-readiness test",
    } <= sections
