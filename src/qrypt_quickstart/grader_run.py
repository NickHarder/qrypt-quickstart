"""Time the README's grader quick-start from a fresh clone, and write the evidence (RQ-35).

`make grader-run` clones the repository's committed HEAD into an empty folder, then runs the grader
quick-start's commands there, each exactly as README.md writes it, and times each one. It runs
against the local mock until the owner's token is in: the mock's URL and a mock token are in the
environment, which wins over `.env`, so the README's `cp .env.example .env` runs as written and no
token is ever read. `pip` and `python` are a new virtualenv's, with pip's cache off, so the install
downloads as it would on a grader's machine; making that virtualenv is not timed, since a grader
already has a Python.

It writes evidence/grader_quickstart.json (each step's command, seconds, exit code and the end of
its output) and evidence/grader_quickstart.md (the same as a table, and the total against the
5 minutes).
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import venv
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from .config import REPOSITORY_ROOT
from .mock_server import SUCCESS_TOKEN, MockQryptServer

GRADER_TARGET_SECONDS: Final = 300.0
STEP_TIMEOUT_SECONDS: Final = 300
OUTPUT_TAIL_CHARACTERS: Final = 200
EVIDENCE_DIRECTORY: Final = REPOSITORY_ROOT / "evidence"


@dataclass(frozen=True)
class TimedStep:
    """One command of the run: what ran, how long it took, its exit code and its output's end."""

    command: str
    seconds: float
    exit_code: int
    output_tail: str


def grader_quick_start_commands(readme: Path) -> list[str]:
    """Return the grader quick-start's shell commands from a README, without their comments.

    Args:
        readme: The README to read.

    Returns:
        Each command of the section's first bash block, in order.
    """
    section = readme.read_text().split("## Grader quick-start", 1)[1]
    block = re.search(r"```bash\n(.*?)```", section, re.DOTALL)
    if block is None:
        message = f"{readme}: the grader quick-start has no bash block"
        raise ValueError(message)
    return [line.split("  #", 1)[0].strip() for line in block[1].splitlines() if line.strip()]


def run_timed(command: str, *, work_directory: Path, environment: dict[str, str]) -> TimedStep:
    """Run one command in a shell, as a grader's shell runs it, and time it."""
    started_at = time.monotonic()
    completed = subprocess.run(  # noqa: S602  the README's own command, as a grader runs it
        command,
        shell=True,
        check=False,
        cwd=work_directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=STEP_TIMEOUT_SECONDS,
    )
    elapsed_seconds = time.monotonic() - started_at
    output = (completed.stdout + completed.stderr).strip()
    return TimedStep(
        command=command,
        seconds=round(elapsed_seconds, 2),
        exit_code=completed.returncode,
        output_tail=output[-OUTPUT_TAIL_CHARACTERS:],
    )


def render_evidence(steps: list[TimedStep], *, target: str, started_at: str) -> str:
    """Write the run as Markdown: a table of the steps and the total against the target.

    Args:
        steps: The timed steps, in the order they ran.
        target: What the snippets called, in words.
        started_at: When the run started, in UTC.

    Returns:
        The Markdown text of evidence/grader_quickstart.md.
    """
    total_seconds = round(sum(step.seconds for step in steps), 1)
    verdict = "under" if total_seconds < GRADER_TARGET_SECONDS else "over"
    rows = "\n".join(
        f"| `{step.command}` | {step.seconds:.1f} s | {step.exit_code} |" for step in steps
    )
    return f"""# Grader quick-start, timed from a fresh clone

Written by `make grader-run` at {started_at}. Each command is the README's grader quick-start as
written, run in a fresh clone of the committed repository, against {target}. `pip` is a new
virtualenv's, with its cache off, so the install downloads as on a grader's machine. Not timed:
making that virtualenv, and pasting a token into `.env`, which takes a person a few seconds.

| Command | Time | Exit code |
|---|---|---|
{rows}

**Total: {total_seconds} s**, {verdict} the brief's 5 minutes ({GRADER_TARGET_SECONDS:.0f} s).
Each step's output ends as `grader_quickstart.json` shows.
"""


def run_grader_quick_start() -> tuple[list[TimedStep], str]:
    """Clone afresh, run the README's grader commands against the mock, and time each one."""
    started_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    commands = grader_quick_start_commands(REPOSITORY_ROOT / "README.md")
    with tempfile.TemporaryDirectory() as scratch_directory, MockQryptServer() as server:
        clone_directory = Path(scratch_directory) / "qrypt-quickstart"
        virtualenv_directory = Path(scratch_directory) / "grader-venv"
        venv.create(virtualenv_directory, with_pip=True)
        environment = {
            key: value for key, value in os.environ.items() if not key.startswith("QRYPT_")
        }
        environment.pop("VIRTUAL_ENV", None)
        environment["PATH"] = f"{virtualenv_directory / 'bin'}{os.pathsep}{environment['PATH']}"
        environment["PIP_NO_CACHE_DIR"] = "1"
        environment["QRYPT_API_URL"] = server.url
        environment["QRYPT_API_KEY"] = SUCCESS_TOKEN
        clone_step = run_timed(
            f"git clone --quiet file://{REPOSITORY_ROOT} {clone_directory.name}",
            work_directory=Path(scratch_directory),
            environment=environment,
        )
        command_steps = [
            run_timed(command, work_directory=clone_directory, environment=environment)
            for command in commands
        ]
    return [clone_step, *command_steps], started_at


def main() -> int:
    """Run the timed grader quick-start, write its evidence, and return 1 on a miss."""
    steps, started_at = run_grader_quick_start()
    total_seconds = round(sum(step.seconds for step in steps), 1)
    EVIDENCE_DIRECTORY.mkdir(exist_ok=True)
    record = {
        "started_at": started_at,
        "target": "local mock",
        "total_seconds": total_seconds,
        "steps": [asdict(step) for step in steps],
    }
    (EVIDENCE_DIRECTORY / "grader_quickstart.json").write_text(json.dumps(record, indent=2) + "\n")
    (EVIDENCE_DIRECTORY / "grader_quickstart.md").write_text(
        render_evidence(steps, target="the local mock (no token yet)", started_at=started_at)
    )
    for step in steps:
        sys.stdout.write(f"{step.seconds:6.1f} s  exit {step.exit_code}  {step.command}\n")
    sys.stdout.write(f"total {total_seconds} s\n")
    is_failed = total_seconds >= GRADER_TARGET_SECONDS or any(step.exit_code for step in steps)
    return 1 if is_failed else 0


if __name__ == "__main__":
    sys.exit(main())
