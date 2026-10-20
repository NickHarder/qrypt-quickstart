"""Every command the site documents runs as written (RQ-07).

The test reads every shell block of the site's pages, sets up a folder the way the page says to
(the snippet saved under the name the page gives, the token in the environment), and runs each
command there against the mock. Two kinds of line are checked rather than run, and say so:

- `pip install ...`: running it would reach the network; instead each package it names must be
  installed in the test's environment and declared in pyproject.toml, so the command installs what
  the snippet imports.
- A line with a placeholder path (`/path/to/...`): it is a template the reader fills in; its
  command, with the placeholder's variable unset, still has to run.
"""

import html
import os
import re
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.mock_server import MockQryptServer

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
SITE: Final = REPOSITORY_ROOT / "site"
SNIPPETS: Final = {
    "quickstart.py": REPOSITORY_ROOT / "quickstart" / "python" / "quickstart.py",
    "quickstart.mjs": REPOSITORY_ROOT / "quickstart" / "node" / "quickstart.mjs",
}
IMPORT_NAMES: Final = {"cryptography": "cryptography", "python-dotenv": "dotenv"}
PLACEHOLDER_VARIABLE: Final = re.compile(r"^(?P<name>[A-Z_]+)=/path/to/\S+ ")


def documented_commands() -> list[tuple[str, str]]:
    commands: list[tuple[str, str]] = []
    for page in sorted(SITE.glob("*.html")):
        for block in re.findall(
            r'<code class="language-shell">(.*?)</code>', page.read_text(), re.S
        ):
            commands += [(page.name, line) for line in html.unescape(block).splitlines() if line]
    for page in sorted(SITE.glob("*.md")):
        for block in re.findall(r"```shell\n(.*?)```", page.read_text(), re.S):
            commands += [(page.name, line) for line in block.splitlines() if line]
    return commands


def test_the_site_documents_at_least_the_install_and_both_runs() -> None:
    lines = {line for _, line in documented_commands()}
    assert {
        "pip install cryptography python-dotenv",
        "python quickstart.py",
        "node quickstart.mjs",
    } <= lines


@pytest.mark.parametrize(
    ("page_name", "command"), documented_commands(), ids=lambda value: str(value)[:40]
)
def test_each_documented_command_runs_as_written(
    tmp_path: Path, page_name: str, command: str
) -> None:
    if command.startswith("pip install "):
        declared = (REPOSITORY_ROOT / "pyproject.toml").read_text()
        for package in command.removeprefix("pip install ").split():
            assert find_spec(IMPORT_NAMES[package]) is not None, f"{package} is not installed"
            assert f'"{package}' in declared, f"{package} is not declared in pyproject.toml"
        return
    placeholder = PLACEHOLDER_VARIABLE.match(command)
    runnable_command = command[placeholder.end() :] if placeholder else command
    for file_name, snippet in SNIPPETS.items():
        shutil.copy(snippet, tmp_path / file_name)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("QRYPT_")}
    environment["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{environment['PATH']}"
    with MockQryptServer() as server:
        environment["QRYPT_API_URL"] = server.url
        environment["QRYPT_API_KEY"] = "mock-200"
        completed = subprocess.run(  # noqa: S602  each line runs as a reader's shell runs it
            runnable_command,
            shell=True,
            check=False,
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )
    assert completed.returncode == 0, f"{page_name}: {command!r} failed: {completed.stderr}"
