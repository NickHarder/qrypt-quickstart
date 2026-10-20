"""Every command the site documents runs as written (RQ-07).

The test reads every shell block of the site's pages, sets up a folder the way the page says to
(the snippet saved under the name the page gives, the token in the environment), and runs each
command there against the mock. Two kinds of line are checked rather than run, and say so:

- `pip install ...`: running it would reach the network; instead each package it names must be
  installed in the test's environment and declared in pyproject.toml, so the command installs what
  the snippet imports.
- A line with a placeholder path (`/path/to/...`): it is a template the reader fills in; its
  command, with the placeholder's variable unset, still has to run.
- `cargo add ...`: running it would reach the network; instead each crate it names, at the version
  and with the features it names, must be what `rust/Cargo.toml` pins, so the reader's project
  builds what CI tested.

`cargo run` runs in a copy of the Rust crate, the reader's project after those steps, offline and
with the crate's own build directory, after one build of the crate has fetched its crates.
"""

import html
import os
import re
import shutil
import subprocess
import sys
import tomllib
from importlib.util import find_spec
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.mock_server import MockQryptServer
from snippet_runner import built_rust_quickstart

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
SITE: Final = REPOSITORY_ROOT / "site"
SNIPPETS: Final = {
    "quickstart.py": REPOSITORY_ROOT / "quickstart" / "python" / "quickstart.py",
    "quickstart.mjs": REPOSITORY_ROOT / "quickstart" / "node" / "quickstart.mjs",
}
IMPORT_NAMES: Final = {"cryptography": "cryptography", "python-dotenv": "dotenv"}
RUST_CRATE: Final = REPOSITORY_ROOT / "rust"
RUST_PROJECT_FILES: Final = ("Cargo.toml", "Cargo.lock", "rust-toolchain.toml", "src/main.rs")
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


def check_cargo_add(command: str) -> None:
    """Assert that a `cargo add` line names exactly the crates, versions and features pinned."""
    pinned = tomllib.loads((RUST_CRATE / "Cargo.toml").read_text())["dependencies"]
    arguments = command.removeprefix("cargo add ").split()
    features = arguments[arguments.index("-F") + 1 :] if "-F" in arguments else []
    crates = arguments[: arguments.index("-F")] if "-F" in arguments else arguments
    for crate in crates:
        name, version = crate.split("@")
        pin = pinned[name]
        pinned_version = pin if isinstance(pin, str) else pin["version"]
        assert pinned_version == f"={version}", f"{crate}: rust/Cargo.toml pins {pinned_version}"
        pinned_features = [] if isinstance(pin, str) else pin.get("features", [])
        named_features = features if crate == crates[-1] else []
        assert named_features == pinned_features, f"{crate}: features {pinned_features}"


def copy_rust_project(project_directory: Path) -> dict[str, str]:
    """Copy the crate as the reader's project, and return the environment that builds it fast."""
    # Building the crate first fetches its crates, as the reader's `cargo add` does, so the
    # offline run finds them on a fresh machine too.
    built_rust_quickstart()
    for file_name in RUST_PROJECT_FILES:
        (project_directory / file_name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(RUST_CRATE / file_name, project_directory / file_name)
    return {"CARGO_NET_OFFLINE": "true", "CARGO_TARGET_DIR": str(RUST_CRATE / "target")}


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
    if command.startswith("cargo add "):
        check_cargo_add(command)
        return
    placeholder = PLACEHOLDER_VARIABLE.match(command)
    runnable_command = command[placeholder.end() :] if placeholder else command
    for file_name, snippet in SNIPPETS.items():
        shutil.copy(snippet, tmp_path / file_name)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("QRYPT_")}
    environment["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{environment['PATH']}"
    if runnable_command == "cargo run":
        environment.update(copy_rust_project(tmp_path))
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
            timeout=300,
        )
    assert completed.returncode == 0, f"{page_name}: {command!r} failed: {completed.stderr}"
    if runnable_command == "cargo run":
        assert "Success" in completed.stdout
