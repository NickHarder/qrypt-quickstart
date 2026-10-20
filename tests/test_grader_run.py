"""The committed timed grader run meets the brief's 5 minutes (RQ-35).

`make grader-run` clones the repository afresh, runs the README's grader quick-start in it, each
command as written, and writes evidence/grader_quickstart.json and .md; these tests read what was
committed, so a run that missed the target, failed a step, or no longer matches the README fails
the gate.
"""

import json
import os
import re
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.grader_run import (
    GRADER_TARGET_SECONDS,
    TimedStep,
    grader_quick_start_commands,
    render_evidence,
    run_timed,
)

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
EVIDENCE: Final = REPOSITORY_ROOT / "evidence"


def committed_run() -> dict[str, object]:
    loaded: dict[str, object] = json.loads((EVIDENCE / "grader_quickstart.json").read_text())
    return loaded


def test_the_readme_commands_are_read_without_their_comments() -> None:
    commands = grader_quick_start_commands(REPOSITORY_ROOT / "README.md")
    assert commands[0].startswith("cp ")
    assert any(command.startswith("python ") for command in commands)
    assert all("#" not in command for command in commands)


def test_a_plain_command_runs_without_a_shell(tmp_path: Path) -> None:
    step = run_timed("echo 'one key'", work_directory=tmp_path, environment=dict(os.environ))
    assert step.exit_code == 0
    assert step.output_tail == "one key"


@pytest.mark.parametrize(
    "command", ["echo a && echo b", "echo $HOME", "cat x | head", "echo a > b"]
)
def test_a_command_that_needs_a_shell_is_refused(tmp_path: Path, command: str) -> None:
    with pytest.raises(ValueError, match="shell"):
        run_timed(command, work_directory=tmp_path, environment=dict(os.environ))


def test_the_evidence_names_each_step_its_time_and_the_total() -> None:
    steps = [
        TimedStep(command="git clone", seconds=1.25, exit_code=0, output_tail="done"),
        TimedStep(
            command="python quickstart/python/quickstart.py",
            seconds=0.5,
            exit_code=0,
            output_tail="Success: ...",
        ),
    ]
    evidence = render_evidence(steps, target="the local mock", started_at="2026-10-20T04:00:00Z")
    assert "| `git clone` | 1.2 s | 0 |" in evidence
    assert "**Total: 1.8 s**" in evidence
    assert "the local mock" in evidence


def test_the_committed_run_used_the_readmes_commands_as_they_are() -> None:
    run = committed_run()
    steps = run["steps"]
    assert isinstance(steps, list)
    commands = [step["command"] for step in steps]
    assert commands[0].startswith("git clone ")
    assert commands[1:] == grader_quick_start_commands(REPOSITORY_ROOT / "README.md")


def test_the_committed_run_succeeded_under_five_minutes() -> None:
    run = committed_run()
    steps = run["steps"]
    assert isinstance(steps, list)
    assert all(step["exit_code"] == 0 for step in steps)
    total_seconds = sum(float(step["seconds"]) for step in steps)
    assert total_seconds < GRADER_TARGET_SECONDS
    assert run["total_seconds"] == round(total_seconds, 1)
    success_lines = [step for step in steps if "Success:" in str(step["output_tail"])]
    assert len(success_lines) == 2


def test_the_markdown_agrees_with_the_json() -> None:
    run = committed_run()
    markdown = (EVIDENCE / "grader_quickstart.md").read_text()
    total = re.search(r"\*\*Total: ([\d.]+) s\*\*", markdown)
    assert total
    assert float(total[1]) == run["total_seconds"]


def test_the_readme_quotes_the_committed_total() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text()
    quoted = re.search(r"these four commands took ([\d.]+) s against the mock", readme)
    assert quoted
    assert float(quoted[1]) == committed_run()["total_seconds"]
