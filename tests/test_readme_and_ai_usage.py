"""README.md and AI_USAGE.md say what the brief asks, and the README's commands run as written.

RQ-30: the README documents how to run the snippets, build the site and reproduce the agent test.
RQ-35: its grader quick-start (set a token, run each snippet, see the success line) runs as written;
here against the mock, with the token and the mock's URL in the environment, which win over `.env`.
RQ-36: a one-line description of at most 120 characters. RQ-31: AI_USAGE.md names the tools, what
they did, and the agent-readiness test's exact prompt and agent.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

from qrypt_quickstart.agent_harness import BRIEF_PROMPT, DEFAULT_AGENT_COMMAND, PROMPT
from qrypt_quickstart.mock_server import MockQryptServer

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
README: Final = REPOSITORY_ROOT / "README.md"
AI_USAGE: Final = REPOSITORY_ROOT / "AI_USAGE.md"
DESCRIPTION_LIMIT: Final = 120


def grader_quick_start_commands() -> list[str]:
    section = README.read_text().split("## Grader quick-start", 1)[1]
    block = re.search(r"```bash\n(.*?)```", section, re.DOTALL)
    assert block, "the grader quick-start has no bash block"
    return [line.split("  #", 1)[0].strip() for line in block[1].splitlines() if line.strip()]


def test_the_line_under_the_title_is_a_one_line_description_of_at_most_120_characters() -> None:
    lines = [line for line in README.read_text().splitlines() if line.strip()]
    assert lines[0].startswith("# ")
    assert not lines[1].startswith("#")
    assert len(lines[1]) <= DESCRIPTION_LIMIT, f"{len(lines[1])} characters"


def test_the_readme_covers_what_the_brief_asks() -> None:
    text = README.read_text()
    for section in (
        "## Grader quick-start",
        "## Run the snippets",
        "## Build the site",
        "## Reproduce the agent-readiness test",
    ):
        assert section in text


def test_the_grader_quick_start_runs_as_written_against_the_mock(tmp_path: Path) -> None:
    shutil.copytree(REPOSITORY_ROOT / "quickstart", tmp_path / "quickstart")
    shutil.copy(REPOSITORY_ROOT / ".env.example", tmp_path / ".env.example")
    commands = grader_quick_start_commands()
    assert any(command.startswith("python ") for command in commands)
    assert any(command.startswith("node ") for command in commands)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("QRYPT_")}
    environment["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{environment['PATH']}"
    with MockQryptServer() as server:
        environment.update({"QRYPT_API_URL": server.url, "QRYPT_API_KEY": "mock-200"})
        for command in commands:
            if command.startswith("pip install "):
                declared = (REPOSITORY_ROOT / "pyproject.toml").read_text()
                assert all(f'"{package}' in declared for package in command.split()[2:])
                continue
            completed = subprocess.run(  # noqa: S602  each line runs as a grader's shell runs it
                command,
                shell=True,
                check=False,
                cwd=tmp_path,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert completed.returncode == 0, f"{command!r}: {completed.stderr}"
            if command.startswith(("python ", "node ")):
                assert "Success" in completed.stdout


def test_ai_usage_names_the_tools_and_the_agent_tests_exact_prompt_and_command() -> None:
    text = AI_USAGE.read_text()
    assert "Claude Code" in text
    assert BRIEF_PROMPT in text
    for prompt_line in PROMPT.splitlines():
        assert prompt_line in text
    assert DEFAULT_AGENT_COMMAND in text
    dockerfile = (REPOSITORY_ROOT / "agent-harness" / "Dockerfile").read_text()
    pinned_version = re.search(r"@anthropic-ai/claude-code@(\S+)", dockerfile)
    assert pinned_version
    assert pinned_version[1] in text


def test_ai_usage_reports_the_fact_check_count_the_claims_table_reports() -> None:
    claims = (REPOSITORY_ROOT / "CLAIMS.md").read_text()
    count = re.search(r"\*\*(\d+) AI-drafted claims checked", claims)
    assert count
    assert f"{count[1]} AI-drafted claims" in AI_USAGE.read_text()
