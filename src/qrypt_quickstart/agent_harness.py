"""The agent-readiness test's harness (Phase 8): one fresh project per run, one judge for all runs.

The brief: give an AI coding agent only the quickstart (its URL or its Markdown) and the prompt
"Generate an AES-256 key using Qrypt quantum entropy in a new project", in a fresh environment, 5
times; record success or failure, wall-clock time and the failure reason; revise the docs; repeat.

Each run gets a new, empty project holding two files: `.env` with `QRYPT_API_KEY`, and the
quickstart's Markdown (`llms-full.txt`, as `qrypt-quickstart.md`). The agent gets the brief's prompt
word for word, followed by one line naming that file. Every request the agent's program makes
goes to a recording server (the mock, or later a relay to Qrypt), so the judge decides from what
happened, not from what the agent says:

- success: a request with `Accept: application/json` and the run's token got entropy (a `200`),
  and neither the token nor the key appears in the transcript or in any project file but `.env`;
- otherwise the first failure that applies, security first: `harness` (the agent could not start),
  `timeout`, `token-exposed`, `key-exposed`, `invented-sdk`, `no-request`, `wrong-header`, `auth`,
  `api-error`.

Two isolation modes. `container` (the owner's choice for the real rounds) runs the agent in a new
Docker container per run, with `api-eus.qrypt.com` mapped to the recording server, so the agent's
program needs no special URL. `folder` runs it in a new folder with its own home directory and
`QRYPT_API_URL` set; the tests use it with stand-in agents, which honour that variable.

Every transcript is scrubbed of the token's exact value before it is written.
"""

import argparse
import base64
import csv
import datetime
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict

from .config import REPOSITORY_ROOT
from .harness_certificates import write_authority_and_server_certificate
from .live_check import LIVE_API_URL, scrub
from .mock_server import SUCCESS_TOKEN, MockQryptServer, RecordedRequest
from .recording_relay import RecordingRelay
from .site_builder import render_text

BRIEF_PROMPT: Final = "Generate an AES-256 key using Qrypt quantum entropy in a new project"
DOCUMENT_FILE_NAME: Final = "qrypt-quickstart.md"
PROMPT: Final = f"{BRIEF_PROMPT}\n\nThe quickstart's documentation is in {DOCUMENT_FILE_NAME}."
PROMPT_PLACEHOLDER: Final = "{prompt}"
DEFAULT_TIMEOUT_SECONDS: Final = 30 * 60
QRYPT_HOST: Final = "api-eus.qrypt.com"
HTTPS_PORT: Final = 443
EVIDENCE_DIRECTORY: Final = REPOSITORY_ROOT / "evidence"
# Against the mock, the run's token is the mock's own success token, never the owner's.
MOCK_TOKEN: Final = SUCCESS_TOKEN
# Claude Code, headless: the prompt, every event as JSON lines for the transcript, and no prompts
# for permission (the container is the sandbox; it holds only the project folder).
DEFAULT_AGENT_COMMAND: Final = (
    "claude -p {prompt} --output-format stream-json --verbose --permission-mode bypassPermissions"
)
LARGEST_PROJECT_FILE_BYTES: Final = 1_000_000
SKIPPED_DIRECTORIES: Final = frozenset({"node_modules", ".venv", "venv", "__pycache__", ".git"})
# An invented SDK is something the agent did, not text it read (the quickstart itself warns
# "no `pip install qrypt`", and a transcript quotes what the agent reads): an install command at
# the start of a line or in a recorded tool call, or an import of a `qrypt` package in its code.
# In a tool call, the package manager's own install command and `qrypt` must share one line of the
# JSON-quoted command (an escaped quote allowed, an escaped newline not): round 1's run 2 wrote a
# file whose comment said "nothing to install" above `QRYPT_API_KEY`, and installed nothing.
INSTALL_COMMAND: Final = r"(?:pip3?|python3? -m pip|npm|yarn|pnpm|cargo)\s+(?:install|i|add)\b"
INVENTED_SDK_PATTERNS: Final = [
    re.compile(
        r"^\s*(?:\$\s*)?" + INSTALL_COMMAND + r"[^\n]*qrypt",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        r'"command"\s*:\s*"(?:[^"\\]|\\.)*?\b' + INSTALL_COMMAND + r'(?:[^"\\]|\\[^n])*?qrypt',
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:import qrypt|from qrypt\b|.*require\(['\"]@?qrypt|.*from ['\"]@?qrypt)",
        re.IGNORECASE | re.MULTILINE,
    ),
]
LOG_FIELDS: Final = [
    "round_name",
    "run_number",
    "agent",
    "target",
    "started_at",
    "wall_clock_minutes",
    "succeeded",
    "failure_category",
    "entropy_requests",
    "largest_size_kib",
    "notes",
]


class AgentRun(BaseModel):
    """One run of the agent-readiness test, as the log records it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    round_name: str
    run_number: int
    agent: str
    target: str
    started_at: str
    wall_clock_minutes: float
    succeeded: bool
    failure_category: str
    entropy_requests: int
    largest_size_kib: int
    notes: str


def key_forms(served_bytes: bytes) -> list[str]:
    """Return the ways a key taken from served entropy could appear in text."""
    key_bytes = served_bytes[:32]
    return [
        key_bytes.hex(),
        key_bytes.hex().upper(),
        base64.b64encode(key_bytes).decode()[:40],
        base64.b64encode(served_bytes).decode()[:40],
    ]


def judge_run(
    *,
    transcript: str,
    project_texts: list[str],
    recorded_requests: list[RecordedRequest],
    token: str,
    exit_code: int,
    timed_out: bool,
) -> str:
    """Return the run's failure category, or an empty string when the run succeeded.

    Args:
        transcript: Everything the agent printed, before scrubbing.
        project_texts: The text of every project file the agent left, except `.env`.
        recorded_requests: The requests the recording server received during the run.
        token: The run's token.
        exit_code: The agent's exit code.
        timed_out: Whether the harness stopped the agent at its time limit.

    Returns:
        The first failure category that applies, security first; "" for a success.
    """
    everything_written = "\n".join([transcript, *project_texts])
    served_answers = [request for request in recorded_requests if request.status == 200]
    statuses = {request.status for request in recorded_requests}
    has_header_fault = 400 in statuses or any(
        "application/json" not in request.accept for request in recorded_requests
    )
    is_unserved = bool(recorded_requests) and not served_answers
    # The checks in the order they are applied: the first that fails names the run's category.
    checks = [
        ("harness", exit_code in {126, 127}),
        ("timeout", timed_out),
        ("token-exposed", token in everything_written),
        (
            "key-exposed",
            any(
                form in everything_written
                for request in served_answers
                for form in key_forms(request.served_bytes)
            ),
        ),
        (
            "invented-sdk",
            any(pattern.search(everything_written) for pattern in INVENTED_SDK_PATTERNS),
        ),
        ("no-request", not recorded_requests),
        ("wrong-header", is_unserved and has_header_fault),
        ("auth", is_unserved and 401 in statuses),
        ("api-error", is_unserved),
    ]
    return next((category for category, has_failed in checks if has_failed), "")


def as_text(output: str | bytes | None) -> str:
    """Return a stopped process's captured output as text; it may be bytes, or nothing."""
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output or ""


def project_texts_of(project_directory: Path) -> list[str]:
    """Return the text of every file the agent wrote in the project: not the two it was given."""
    texts = []
    for path in sorted(project_directory.rglob("*")):
        is_skipped = any(part in SKIPPED_DIRECTORIES for part in path.parts)
        is_given_file = path.name in {".env", DOCUMENT_FILE_NAME}
        is_readable = path.is_file() and path.stat().st_size <= LARGEST_PROJECT_FILE_BYTES
        if is_readable and not is_given_file and not is_skipped:
            texts.append(path.read_text(errors="replace"))
    return texts


def prepare_project(project_directory: Path, *, token: str) -> None:
    """Write the two files a run starts with: the token file and the quickstart's Markdown."""
    project_directory.mkdir(parents=True)
    (project_directory / ".env").write_text(f"QRYPT_API_KEY={token}\n")
    full_quickstart = render_text((REPOSITORY_ROOT / "site" / "llms-full.md").read_text())
    (project_directory / DOCUMENT_FILE_NAME).write_text(full_quickstart)


def run_agent_once(
    *,
    round_name: str,
    run_number: int,
    agent_command: list[str],
    api_url: str,
    token: str,
    transcripts_directory: Path,
    mock_server: MockQryptServer,
    agent_name: str = "stand-in",
    target: str = "mock",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    isolation: str = "folder",
    image: str = "qrypt-agent-harness",
    certificate_authority: Path | None = None,
    network: str = "bridge",
    extra_authority: Path | None = None,
) -> AgentRun:
    """Run the agent once in a fresh project and judge the run.

    Args:
        round_name: The round, such as "1" or "2".
        run_number: The run within the round.
        agent_command: The agent's command line; "{prompt}" in it is replaced by the prompt.
        api_url: The recording server's URL, given to the agent as `QRYPT_API_URL`.
        token: The run's token, written to the project's `.env` and never to the transcript.
        transcripts_directory: Where the scrubbed transcript is written.
        mock_server: The recording server, whose requests during the run are judged.
        agent_name: The agent's name, for the log.
        target: "mock" or "live", for the log.
        timeout_seconds: How long the agent may run before it is stopped.
        isolation: "folder" (a fresh folder, `QRYPT_API_URL` set) or "container" (a fresh Docker
            container with Qrypt's host name mapped to the recording server).
        image: The container image, for the container mode.
        certificate_authority: The authority that signed the recording server's certificate, for
            the container mode.
        network: The container's network, "bridge" or "host" (see `container_command`).
        extra_authority: Another authority the container trusts, such as an egress proxy's.

    Returns:
        The judged run.
    """
    if isinstance(mock_server, RecordingRelay):
        mock_server.start_run(f"round {round_name} run {run_number}")
    first_request_index = len(mock_server.recorded_requests)
    with tempfile.TemporaryDirectory() as work_root:
        project_directory = Path(work_root) / "project"
        home_directory = Path(work_root) / "home"
        home_directory.mkdir()
        prepare_project(project_directory, token=token)
        agent_arguments = [
            argument.replace(PROMPT_PLACEHOLDER, PROMPT) for argument in agent_command
        ]
        if isolation == "container":
            # The image runs as a user without root; this throwaway folder must be theirs to write.
            project_directory.chmod(0o777)
            command = container_command(
                project_directory=project_directory,
                image=image,
                agent_arguments=agent_arguments,
                map_api_to_host=True,
                certificate_authority=certificate_authority,
                network=network,
                extra_authority=extra_authority,
            )
            # docker passes the agent's login and the proxy through by name (`--env=NAME`), from
            # this process.
            environment = {
                **{
                    name: os.environ[name]
                    for name in ("PATH", "HOME", *PROXY_VARIABLES)
                    if name in os.environ
                },
                **agent_login_environment(os.environ),
            }
        else:
            command = agent_arguments
            environment = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": str(home_directory),
                "LANG": "C.UTF-8",
                "QRYPT_API_URL": api_url,
            }
        started_at = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        started_monotonic = time.monotonic()
        try:
            completed = subprocess.run(  # noqa: S603  the agent command the operator chose
                command,
                check=False,
                cwd=project_directory,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            transcript = completed.stdout + completed.stderr
            exit_code = completed.returncode
            timed_out = False
        except subprocess.TimeoutExpired as expired:
            transcript = as_text(expired.stdout) + as_text(expired.stderr)
            exit_code = -1
            timed_out = True
        except FileNotFoundError as missing:
            transcript = f"the agent command could not start: {missing}"
            exit_code = 127
            timed_out = False
        elapsed_seconds = time.monotonic() - started_monotonic
        project_texts = project_texts_of(project_directory)
    run_requests = mock_server.recorded_requests[first_request_index:]
    failure_category = judge_run(
        transcript=transcript,
        project_texts=project_texts,
        recorded_requests=run_requests,
        token=token,
        exit_code=exit_code,
        timed_out=timed_out,
    )
    transcripts_directory.mkdir(parents=True, exist_ok=True)
    transcript_path = transcripts_directory / f"{round_name}-run-{run_number}.txt"
    transcript_path.write_text(scrub(transcript, token))
    entropy_sizes = [request.size_kib or 0 for request in run_requests]
    return AgentRun(
        round_name=round_name,
        run_number=run_number,
        agent=agent_name,
        target=target,
        started_at=started_at,
        wall_clock_minutes=round(elapsed_seconds / 60, 2),
        succeeded=failure_category == "",
        failure_category=failure_category,
        entropy_requests=len(run_requests),
        largest_size_kib=max(entropy_sizes, default=0),
        notes="",
    )


def write_runs(log: Path, runs: list[AgentRun]) -> None:
    """Append runs to the agent-run log, writing its header when the log is new."""
    is_new_log = not log.exists()
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", newline="") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=LOG_FIELDS)
        if is_new_log:
            writer.writeheader()
        writer.writerows(run.model_dump() for run in runs)


# The proxy settings a container in the host network mode is given, by name.
PROXY_VARIABLES: Final = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy")
# A cloud session keeps CLAUDE_CODE_OAUTH_TOKEN for its own login and may not pass the owner's
# through, so the owner's login can also arrive under this name; the container gets the usual one.
HARNESS_LOGIN_VARIABLE: Final = "HARNESS_CLAUDE_CODE_OAUTH_TOKEN"


def agent_login_environment(source_environment: Mapping[str, str]) -> dict[str, str]:
    """Give the agent in the container its login, under the names Claude Code reads.

    Args:
        source_environment: This process's environment, or a stand-in for one in a test.

    Returns:
        ANTHROPIC_API_KEY and CLAUDE_CODE_OAUTH_TOKEN, each only when there is a value for it;
        CLAUDE_CODE_OAUTH_TOKEN comes from HARNESS_CLAUDE_CODE_OAUTH_TOKEN when it is not set
        itself.
    """
    oauth_token = source_environment.get("CLAUDE_CODE_OAUTH_TOKEN") or source_environment.get(
        HARNESS_LOGIN_VARIABLE
    )
    api_key = source_environment.get("ANTHROPIC_API_KEY")
    candidate_login = {"CLAUDE_CODE_OAUTH_TOKEN": oauth_token, "ANTHROPIC_API_KEY": api_key}
    return {name: value for name, value in candidate_login.items() if value}


def container_command(
    *,
    project_directory: Path,
    image: str,
    agent_arguments: list[str],
    map_api_to_host: bool,
    certificate_authority: Path | None,
    network: str = "bridge",
    extra_authority: Path | None = None,
) -> list[str]:
    """Return the `docker run` command for one run in a fresh container (the `container` mode).

    The container sees only the project folder. With `map_api_to_host`, `api-eus.qrypt.com` resolves
    to the host, where the recording server answers with a certificate the container trusts (the
    authority is mounted for the image's entry point to install), so the agent's program calls
    Qrypt's real URL and needs no `QRYPT_API_URL`. The agent's own login is passed through by name,
    never by value on the command line.

    Args:
        project_directory: The prepared project, mounted at /project.
        image: The harness image (`agent-harness/Dockerfile`).
        agent_arguments: The agent's command line inside the container.
        map_api_to_host: Route Qrypt's host name to the recording server on the host.
        certificate_authority: The authority that signed the recording server's certificate.
        network: "bridge", Docker's own network, or "host", for a machine whose only way out is an
            egress proxy on its loopback (a cloud session): the container shares the host's
            network, the proxy settings pass in, and Qrypt's host name stays off the proxy.
        extra_authority: Another authority to trust, such as the egress proxy's.

    Returns:
        The command's arguments.
    """
    command = [
        "docker",
        "run",
        "--rm",
        f"--volume={project_directory}:/project",
        "--workdir=/project",
        "--env=ANTHROPIC_API_KEY",
        "--env=CLAUDE_CODE_OAUTH_TOKEN",
    ]
    is_host_network = network == "host"
    if is_host_network:
        no_proxy = ",".join(
            entry for entry in (os.environ.get("NO_PROXY", ""), QRYPT_HOST) if entry
        )
        command.extend(
            [
                "--network=host",
                *(f"--env={name}" for name in PROXY_VARIABLES),
                f"--env=NO_PROXY={no_proxy}",
                f"--env=no_proxy={no_proxy}",
            ]
        )
    if map_api_to_host:
        api_address = "127.0.0.1" if is_host_network else "host-gateway"
        command.append(f"--add-host={QRYPT_HOST}:{api_address}")
    if certificate_authority is not None:
        command.append(f"--volume={certificate_authority}:/harness/ca.pem:ro")
    if extra_authority is not None:
        command.append(f"--volume={extra_authority}:/harness/extra-ca.pem:ro")
    return [*command, image, *agent_arguments]


def owner_token() -> str:
    """Return the owner's Qrypt token from the environment or the repository's `.env`.

    Only the live round reads it, to write it into each run's project, as a developer would.
    """
    from_environment = os.environ.get("QRYPT_API_KEY", "")
    from_file = dotenv_values(REPOSITORY_ROOT / ".env").get("QRYPT_API_KEY") or ""
    return (from_environment or from_file).strip()


def main() -> None:
    """Run one round of the agent-readiness test and append it to the log.

    Against the mock by default. With `--target live`, each run's project holds the owner's token,
    and the agent's program reaches Qrypt through the recording relay, which judges every request
    the same way, caps each run at 64 KiB and stops at the ledger's 8,192 KiB. A live round spends
    the owner's entropy: run it only with the owner's approval.
    """
    parser = argparse.ArgumentParser(description="Run one round of the agent-readiness test.")
    parser.add_argument("--round", required=True, dest="round_name")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--target", choices=["mock", "live"], default="mock")
    parser.add_argument("--isolation", choices=["container", "folder"], default="container")
    parser.add_argument("--agent-name", default="claude-code")
    parser.add_argument("--agent-command", default=DEFAULT_AGENT_COMMAND)
    parser.add_argument("--image", default="qrypt-agent-harness")
    parser.add_argument("--network", choices=["bridge", "host"], default="bridge")
    parser.add_argument("--extra-ca", type=Path, default=None, dest="extra_authority")
    parser.add_argument("--timeout-minutes", type=float, default=DEFAULT_TIMEOUT_SECONDS / 60)
    arguments = parser.parse_args()
    is_live = arguments.target == "live"
    token = owner_token() if is_live else MOCK_TOKEN
    if not token:
        sys.exit("agent-harness: a live round needs QRYPT_API_KEY in the environment or .env")
    with tempfile.TemporaryDirectory() as certificates_directory:
        is_container = arguments.isolation == "container"
        generated_authority, certificate, private_key = write_authority_and_server_certificate(
            Path(certificates_directory), host_name=QRYPT_HOST
        )
        # In a container the server is api-eus.qrypt.com on the host gateway, over HTTPS; in a
        # folder it is a plain local port that QRYPT_API_URL names.
        port = HTTPS_PORT if is_container else 0
        tls_certificate = (certificate, private_key) if is_container else None
        host = "0.0.0.0" if is_container else "127.0.0.1"  # noqa: S104  containers reach the host gateway
        authority: Path | None = generated_authority if is_container else None
        server: MockQryptServer = (
            RecordingRelay(
                upstream_url=LIVE_API_URL,
                ledger=EVIDENCE_DIRECTORY / "live_usage.csv",
                port=port,
                tls_certificate=tls_certificate,
                host=host,
            )
            if is_live
            else MockQryptServer(port=port, tls_certificate=tls_certificate, host=host)
        )
        with server:
            for run_number in range(1, arguments.runs + 1):
                run = run_agent_once(
                    round_name=arguments.round_name,
                    run_number=run_number,
                    agent_command=shlex.split(arguments.agent_command),
                    api_url=server.url,
                    token=token,
                    transcripts_directory=EVIDENCE_DIRECTORY / "transcripts",
                    mock_server=server,
                    agent_name=arguments.agent_name,
                    target=arguments.target,
                    timeout_seconds=arguments.timeout_minutes * 60,
                    isolation=arguments.isolation,
                    image=arguments.image,
                    certificate_authority=authority,
                    network=arguments.network,
                    extra_authority=arguments.extra_authority,
                )
                write_runs(EVIDENCE_DIRECTORY / "agent_runs.csv", [run])
                verdict = "success" if run.succeeded else f"failed: {run.failure_category}"
                print(  # noqa: T201  a command-line tool
                    f"agent-harness: round {run.round_name} run {run.run_number}: {verdict}, "
                    f"{run.wall_clock_minutes} minutes"
                )


if __name__ == "__main__":
    main()
