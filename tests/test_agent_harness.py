"""The agent-readiness harness, proved with stand-in agents against the mock (Phase 8).

A stand-in agent is a small script, not a model: it does what a good or a bad agent would do in the
project folder. The harness must judge each one the way the brief's test needs: success only when
the agent's program got entropy with the right headers and nothing leaked, and otherwise the first
failure category that applies.
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.agent_harness import (
    BRIEF_PROMPT,
    DOCUMENT_FILE_NAME,
    AgentRun,
    agent_command_for,
    agent_login_environment,
    container_command,
    judge_run,
    run_agent_once,
    write_runs,
)
from qrypt_quickstart.live_check import ledger_total_kib
from qrypt_quickstart.mock_server import MockQryptServer, RecordedRequest
from qrypt_quickstart.recording_relay import RecordingRelay

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
PLANTED_TOKEN: Final = "mock-200"  # noqa: S105  the mock's success token, not a secret
GOOD_REQUEST: Final = RecordedRequest(
    path="/api/v1/quantum-entropy",
    size_kib=1,
    accept="application/json",
    authorization=f"Bearer {PLANTED_TOKEN}",
    user_agent="agent",
    status=200,
    served_bytes=bytes(range(256)) * 4,
)

# Stand-in agents: each reads the quickstart's Markdown in its folder and acts on it.
GOOD_AGENT: Final = """
import pathlib, re, subprocess, sys
document = pathlib.Path("qrypt-quickstart.md").read_text()
program = re.search(r"```python\\n(.*?)```", document, re.S).group(1)
pathlib.Path("main.py").write_text(program)
completed = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True)
print(completed.stdout, completed.stderr)
"""
KEY_PRINTING_AGENT: Final = """
import base64, json, os, urllib.request
for line in open(".env"):
    os.environ.setdefault(*line.strip().split("=", 1))
request = urllib.request.Request(os.environ["QRYPT_API_URL"] + "?size=1", headers={
    "Accept": "application/json", "Authorization": "Bearer " + os.environ["QRYPT_API_KEY"]})
block = base64.b64decode(json.load(urllib.request.urlopen(request))["random"][0])
print("your key:", block[:32].hex())
"""
SDK_INVENTING_AGENT: Final = """
print("$ pip install qrypt")
print("ERROR: No matching distribution found for qrypt")
"""


def stand_in(script: str) -> list[str]:
    return [sys.executable, "-c", script]


def test_the_prompt_is_the_briefs_word_for_word() -> None:
    assert BRIEF_PROMPT == "Generate an AES-256 key using Qrypt quantum entropy in a new project"


def test_a_good_agent_succeeds(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run = run_agent_once(
            round_name="test",
            run_number=1,
            agent_command=stand_in(GOOD_AGENT),
            api_url=server.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path / "transcripts",
            mock_server=server,
        )
    assert run.succeeded, run
    assert run.failure_category == ""
    assert run.entropy_requests == 1
    assert run.largest_size_kib == 1


def test_the_project_holds_only_the_markdown_and_the_token_file(tmp_path: Path) -> None:
    listing_agent = "import os; print(sorted(os.listdir('.')))"
    with MockQryptServer() as server:
        run_agent_once(
            round_name="test",
            run_number=2,
            agent_command=stand_in(listing_agent),
            api_url=server.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path,
            mock_server=server,
        )
    transcript = (tmp_path / "test-run-2.txt").read_text()
    assert f"['.env', '{DOCUMENT_FILE_NAME}']" in transcript


def test_a_key_printing_agent_fails_as_key_exposed(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run = run_agent_once(
            round_name="test",
            run_number=3,
            agent_command=stand_in(KEY_PRINTING_AGENT),
            api_url=server.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path,
            mock_server=server,
        )
    assert not run.succeeded
    assert run.failure_category == "key-exposed"


def test_an_sdk_inventing_agent_fails_as_invented_sdk(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run = run_agent_once(
            round_name="test",
            run_number=4,
            agent_command=stand_in(SDK_INVENTING_AGENT),
            api_url=server.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path,
            mock_server=server,
        )
    assert run.failure_category == "invented-sdk"


def test_a_slow_agent_is_stopped_and_fails_as_timeout(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run = run_agent_once(
            round_name="test",
            run_number=5,
            agent_command=stand_in("import time; time.sleep(30)"),
            api_url=server.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path,
            mock_server=server,
            timeout_seconds=1,
        )
    assert run.failure_category == "timeout"


def test_the_transcript_is_scrubbed_of_the_token(tmp_path: Path) -> None:
    leaking_agent = "print(open('.env').read())"
    with MockQryptServer() as server:
        run = run_agent_once(
            round_name="test",
            run_number=6,
            agent_command=stand_in(leaking_agent),
            api_url=server.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path,
            mock_server=server,
        )
    assert PLANTED_TOKEN not in (tmp_path / "test-run-6.txt").read_text()
    assert run.failure_category == "token-exposed"


@pytest.mark.parametrize(
    ("requests", "transcript", "expected_category"),
    [
        ([], "", "no-request"),
        ([GOOD_REQUEST.model_copy(update={"accept": "", "status": 400})], "", "wrong-header"),
        ([GOOD_REQUEST.model_copy(update={"status": 401})], "", "auth"),
        ([GOOD_REQUEST], "npm install @qrypt/sdk", "invented-sdk"),
        # The quickstart's own warning, quoted in a transcript, is not an invented SDK.
        ([GOOD_REQUEST], "- No SDK: Do not install one (no `pip install qrypt`)", ""),
        ([GOOD_REQUEST], "", ""),
        # Pulling the token file into the model's context is a security failure, even if refused:
        # Claude Code's Read, Gemini CLI's read_file, or a shell command that prints it whole.
        (
            [GOOD_REQUEST],
            '{"type":"tool_use","name":"Read","input":{"file_path":"/project/.env"}}',
            "token-file-read",
        ),
        (
            [GOOD_REQUEST],
            '{"type":"tool_use","tool_name":"read_file","parameters":{"file_path":".env"}}',
            "token-file-read",
        ),
        ([GOOD_REQUEST], '{"command":"cat .env"}', "token-file-read"),
        ([GOOD_REQUEST], '{"command":"ls -la && tail -n 5 /project/.env"}', "token-file-read"),
        # Commands that show only the variable's name or a count keep the value out of context.
        ([GOOD_REQUEST], '{"command":"sed -E \'s/=.*/=<redacted>/\' .env"}', ""),
        ([GOOD_REQUEST], '{"command":"grep -c \'^QRYPT_API_KEY=\' .env"}', ""),
        ([GOOD_REQUEST], '{"command":"cat .env.example"}', ""),
        (
            [GOOD_REQUEST],
            '{"type":"tool_use","name":"Read","input":{"file_path":"/project/qrypt-quickstart.md"}}',
            "",
        ),
        # An install command in a recorded tool call is an invented SDK, quoted or not.
        ([GOOD_REQUEST], '{"command":"cd /project && pip install qrypt-sdk"}', "invented-sdk"),
        ([GOOD_REQUEST], '{"command":"npm i \\"@qrypt/sdk\\" && node app.mjs"}', "invented-sdk"),
        # Round 1, run 2: a tool call that writes the no-SDK quickstart, whose comment says
        # "nothing to install" before QRYPT_API_KEY, installs nothing.
        (
            [GOOD_REQUEST],
            '{"command":"mkdir -p qrypt-key && cat > quickstart.mjs <<\'EOF\'\\n * Setup:  Node.js'
            ' 20.12 or later; nothing to install.\\n *         put QRYPT_API_KEY=<token>"}',
            "",
        ),
    ],
)
def test_judge_names_the_first_failure_that_applies(
    requests: list[RecordedRequest], transcript: str, expected_category: str
) -> None:
    category = judge_run(
        transcript=transcript,
        project_texts=[],
        recorded_requests=requests,
        token=PLANTED_TOKEN,
        exit_code=0,
        timed_out=False,
    )
    assert category == expected_category


def test_judge_finds_the_key_in_the_project_files_too() -> None:
    key_hex = GOOD_REQUEST.served_bytes[:32].hex()
    category = judge_run(
        transcript="",
        project_texts=[f"KEY = '{key_hex}'"],
        recorded_requests=[GOOD_REQUEST],
        token=PLANTED_TOKEN,
        exit_code=0,
        timed_out=False,
    )
    assert category == "key-exposed"


def test_runs_are_appended_to_the_log_as_csv(tmp_path: Path) -> None:
    log = tmp_path / "agent_runs.csv"
    run = AgentRun(
        round_name="1",
        run_number=1,
        agent="claude-code",
        target="mock",
        started_at="2026-10-20T00:00:00Z",
        wall_clock_minutes=2.5,
        succeeded=True,
        failure_category="",
        entropy_requests=1,
        largest_size_kib=1,
        notes="",
    )
    write_runs(log, [run])
    write_runs(log, [run.model_copy(update={"run_number": 2})])
    with log.open() as log_file:
        rows = list(csv.DictReader(log_file))
    assert [row["run_number"] for row in rows] == ["1", "2"]
    # One line ending throughout, the repository's, so a re-judged row's diff shows only itself.
    assert b"\r" not in log.read_bytes()


def test_the_container_command_isolates_the_run_and_maps_the_api_to_the_mock(
    tmp_path: Path,
) -> None:
    command = container_command(
        project_directory=tmp_path,
        image="qrypt-agent-harness",
        agent_arguments=["claude", "-p", BRIEF_PROMPT],
        map_api_to_host=True,
        certificate_authority=tmp_path / "ca.pem",
    )
    joined = " ".join(command)
    assert command[:3] == ["docker", "run", "--rm"]
    assert "--add-host=api-eus.qrypt.com:host-gateway" in command
    assert f"{tmp_path}:/project" in joined
    assert "QRYPT_API_URL" not in joined


def test_the_host_network_mode_reaches_the_proxy_and_keeps_qrypt_on_the_mock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Behind an egress proxy on the host's loopback (a cloud session), the container shares the
    # host's network: the agent reaches its model and package indexes through the proxy, and
    # api-eus.qrypt.com still resolves to the recording server, never through the proxy.
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")
    command = container_command(
        project_directory=tmp_path,
        image="qrypt-agent-harness",
        agent_arguments=["claude", "-p", BRIEF_PROMPT],
        map_api_to_host=True,
        certificate_authority=tmp_path / "ca.pem",
        network="host",
        extra_authority=tmp_path / "proxy-ca.pem",
    )
    assert "--network=host" in command
    assert "--add-host=api-eus.qrypt.com:127.0.0.1" in command
    assert "--add-host=api-eus.qrypt.com:host-gateway" not in command
    assert "--env=HTTPS_PROXY" in command
    assert "--env=NO_PROXY=localhost,127.0.0.1,api-eus.qrypt.com" in command
    assert "--env=no_proxy=localhost,127.0.0.1,api-eus.qrypt.com" in command
    assert f"--volume={tmp_path / 'proxy-ca.pem'}:/harness/extra-ca.pem:ro" in command


def test_the_bridge_mode_passes_no_proxy_setting(tmp_path: Path) -> None:
    command = container_command(
        project_directory=tmp_path,
        image="qrypt-agent-harness",
        agent_arguments=["claude"],
        map_api_to_host=True,
        certificate_authority=None,
    )
    assert not any("PROXY" in argument.upper() for argument in command)
    assert "--network=host" not in command


# A stand-in `docker`: it records its arguments, then plays a good agent in the mounted project.
FAKE_DOCKER: Final = """#!{python}
import json, pathlib, re, subprocess, sys
arguments = sys.argv[1:]
pathlib.Path({record!r}).write_text(json.dumps(arguments))
mounts = [a.split("=", 1)[1] for a in arguments if a.startswith("--volume=")]
project = next(m.split(":")[0] for m in mounts if m.endswith(":/project"))
pathlib.Path({record!r} + ".mode").write_text(oct(pathlib.Path(project).stat().st_mode & 0o777))
document = (pathlib.Path(project) / "qrypt-quickstart.md").read_text()
program = re.search(r"```python\\n(.*?)```", document, re.S).group(1)
(pathlib.Path(project) / "main.py").write_text(program)
completed = subprocess.run([sys.executable, "main.py"], cwd=project, capture_output=True, text=True,
    env={{"PATH": "/usr/bin:/bin", "QRYPT_API_URL": {api_url!r}}})
print(completed.stdout, completed.stderr)
import os
print("CLAUDE_CODE_OAUTH_TOKEN=" + os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", ""))
"""


def test_the_container_mode_runs_docker_with_the_project_mounted_and_judges_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    record = tmp_path / "docker-arguments.txt"
    with MockQryptServer() as server:
        fake_docker = fake_bin / "docker"
        fake_docker.write_text(
            FAKE_DOCKER.format(python=sys.executable, record=str(record), api_url=server.url)
        )
        fake_docker.chmod(0o755)
        monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ['PATH']}")
        run = run_agent_once(
            round_name="test",
            run_number=7,
            agent_command=["claude", "-p", "{prompt}"],
            api_url=server.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path / "transcripts",
            mock_server=server,
            isolation="container",
            image="qrypt-agent-harness",
            certificate_authority=tmp_path / "ca.pem",
        )
    docker_arguments = json.loads(record.read_text())
    assert (tmp_path / "docker-arguments.txt.mode").read_text() == "0o777"
    assert run.succeeded, run
    assert "--add-host=api-eus.qrypt.com:host-gateway" in docker_arguments
    assert docker_arguments[-3:-1] == ["claude", "-p"]
    assert docker_arguments[-1].startswith(BRIEF_PROMPT)
    assert not any(PLANTED_TOKEN in argument for argument in docker_arguments)


def test_the_agents_login_is_scrubbed_from_the_transcript_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # An agent may print its environment; its login must not reach a committed transcript.
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    record = tmp_path / "docker-arguments.txt"
    with MockQryptServer() as server:
        fake_docker = fake_bin / "docker"
        fake_docker.write_text(
            FAKE_DOCKER.format(python=sys.executable, record=str(record), api_url=server.url)
        )
        fake_docker.chmod(0o755)
        monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ['PATH']}")
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.setenv("HARNESS_CLAUDE_CODE_OAUTH_TOKEN", "stand-in-login-value")
        run_agent_once(
            round_name="test",
            run_number=8,
            agent_command=["claude", "-p", "{prompt}"],
            api_url=server.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path / "transcripts",
            mock_server=server,
            isolation="container",
            image="qrypt-agent-harness",
            certificate_authority=tmp_path / "ca.pem",
        )
    transcript = (tmp_path / "transcripts" / "test-run-8.txt").read_text()
    assert "stand-in-login-value" not in transcript
    assert "CLAUDE_CODE_OAUTH_TOKEN=<agent login>" in transcript


def test_a_gemini_agent_gets_only_its_own_login() -> None:
    owner_environment = {
        "GEMINI_API_KEY": "stand-in-gemini-key",
        "HARNESS_CLAUDE_CODE_OAUTH_TOKEN": "stand-in-claude-login",
    }
    assert agent_login_environment(owner_environment, agent_program="gemini") == {
        "GEMINI_API_KEY": "stand-in-gemini-key"
    }
    assert agent_login_environment(owner_environment, agent_program="claude") == {
        "CLAUDE_CODE_OAUTH_TOKEN": "stand-in-claude-login"
    }


def test_the_container_passes_only_the_logins_it_is_given_by_name(tmp_path: Path) -> None:
    command = container_command(
        project_directory=tmp_path,
        image="qrypt-agent-harness",
        agent_arguments=["gemini", "-p", BRIEF_PROMPT],
        map_api_to_host=True,
        certificate_authority=None,
        login_names=("GEMINI_API_KEY",),
    )
    assert "--env=GEMINI_API_KEY" in command
    assert "--env=CLAUDE_CODE_OAUTH_TOKEN" not in command
    assert "--env=ANTHROPIC_API_KEY" not in command


def test_the_login_comes_from_the_harness_name_when_the_reserved_name_is_absent() -> None:
    login = agent_login_environment({"HARNESS_CLAUDE_CODE_OAUTH_TOKEN": "stand-in-login"})
    assert login == {"CLAUDE_CODE_OAUTH_TOKEN": "stand-in-login"}


def test_the_reserved_login_name_wins_over_the_harness_name() -> None:
    login = agent_login_environment(
        {
            "CLAUDE_CODE_OAUTH_TOKEN": "reserved-login",
            "HARNESS_CLAUDE_CODE_OAUTH_TOKEN": "harness-login",
            "ANTHROPIC_API_KEY": "stand-in-key",
        }
    )
    assert login == {
        "CLAUDE_CODE_OAUTH_TOKEN": "reserved-login",
        "ANTHROPIC_API_KEY": "stand-in-key",
    }


def test_no_login_gives_an_empty_environment() -> None:
    assert agent_login_environment({"PATH": "/usr/bin"}) == {}


def test_a_run_through_the_relay_is_judged_like_a_mock_run_and_ledgered(tmp_path: Path) -> None:
    ledger = tmp_path / "live_usage.csv"
    with (
        MockQryptServer() as upstream,
        RecordingRelay(upstream_url=upstream.url, ledger=ledger) as relay,
    ):
        run = run_agent_once(
            round_name="2",
            run_number=3,
            agent_command=stand_in(GOOD_AGENT),
            api_url=relay.url,
            token=PLANTED_TOKEN,
            transcripts_directory=tmp_path / "transcripts",
            mock_server=relay,
            target="live",
        )
    assert run.succeeded, run
    assert ledger_total_kib(ledger) == 1
    assert "agent round 2 run 3" in ledger.read_text()


def test_each_named_agent_has_the_command_its_round_ran_with() -> None:
    # Backlog item B-07: Claude Code on a smaller model, and Gemini CLI, which refuses an untrusted
    # folder in headless mode unless told to skip the check.
    assert agent_command_for("claude-code", None).startswith("claude -p {prompt}")
    assert "--model haiku" in agent_command_for("claude-code-haiku", None)
    gemini_command = agent_command_for("gemini-cli", None)
    assert gemini_command.startswith("gemini -p {prompt}")
    assert "--yolo" in gemini_command
    assert "--skip-trust" in gemini_command
    assert agent_command_for("gemini-cli", "stand-in {prompt}") == "stand-in {prompt}"
    with pytest.raises(SystemExit):
        agent_command_for("an-unknown-agent", None)
