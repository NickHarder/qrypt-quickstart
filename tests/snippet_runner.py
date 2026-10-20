"""Run a quickstart snippet the way a developer runs it, against the mock, for the tests.

Each run copies the snippet into an empty directory, so no `.env` of this repository is found,
and points `QRYPT_API_URL` at the URL given, so no request can reach the live API.
"""

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

QUICKSTART_DIRECTORY: Final = Path(__file__).resolve().parents[1] / "quickstart"
SNIPPETS: Final = {
    "python": QUICKSTART_DIRECTORY / "python" / "quickstart.py",
    "node": QUICKSTART_DIRECTORY / "node" / "quickstart.mjs",
}
TRACEBACK_MARKERS: Final = ("Traceback (most recent call last)", "    at ", "node:internal")


@dataclass(frozen=True)
class SnippetRun:
    """What one run of a snippet printed, how it exited and how long it took."""

    exit_code: int
    stdout: str
    stderr: str
    elapsed_seconds: float

    @property
    def shows_a_traceback(self) -> bool:
        """Say whether the run printed a stack trace instead of a message."""
        return any(marker in self.stdout + self.stderr for marker in TRACEBACK_MARKERS)


def run_snippet(
    language: str,
    work_directory: Path,
    *,
    api_url: str,
    token: str | None,
    extra_environment: dict[str, str] | None = None,
) -> SnippetRun:
    """Copy the snippet into the work directory and run it there with the given environment."""
    snippet = SNIPPETS[language]
    copied_snippet = work_directory / snippet.name
    shutil.copy(snippet, copied_snippet)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("QRYPT_")}
    environment["QRYPT_API_URL"] = api_url
    environment.update(extra_environment or {})
    if token is not None:
        environment["QRYPT_API_KEY"] = token
    interpreter = sys.executable if language == "python" else shutil.which("node")
    assert interpreter, f"no interpreter for {language}"
    started_at = time.monotonic()
    completed = subprocess.run(
        [interpreter, str(copied_snippet)],
        check=False,
        cwd=work_directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return SnippetRun(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        elapsed_seconds=time.monotonic() - started_at,
    )
