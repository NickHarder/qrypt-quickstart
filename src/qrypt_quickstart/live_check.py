"""The live check (Phase 7): the only code here that calls Qrypt's API with the owner's token.

It runs each quickstart 5 times against the live endpoint and times it (the brief's "snippet
runtime under 3 s, 5 runs"), then makes four probes that settle what Qrypt's docs leave open:

- `answer_shape`: one ordinary request, recording the answer's shape (never its entropy).
- `without_accept`: one request without `Accept: application/json`, recording Qrypt's real answer,
  which the mock has only guessed (docs/PLAN.md, review item D1).
- `bad_token_named_client` and `bad_token_python_default_client`: a deliberately wrong token, once
  with the snippets' `User-Agent` and once with Python's default one, recording the real 401 and
  whether the edge in front of the API refuses either client first (audit finding ARCH-02). A bad
  token is refused before any entropy is served: 0 KiB.

Its guards: it refuses before the first request when the ledger (`evidence/live_usage.csv`) plus
this run's 12 KiB would pass the 8,192 KiB stop the plan sets under the brief's 10,240 KiB budget;
it appends a ledger row for every request as it is made; and it writes the token's value nowhere,
scrubbing everything it writes by the token's exact value.

Run `make live-check`, only with the owner's approval. It reads `QRYPT_API_KEY` from the
environment or the repository's `.env`; the tests run it against the mock with a planted token.
"""

import base64
import csv
import datetime
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Final

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict

from .config import ENV_FILE, REPOSITORY_ROOT

LIVE_API_URL: Final = "https://api-eus.qrypt.com/api/v1/quantum-entropy"
EVIDENCE_DIRECTORY: Final = REPOSITORY_ROOT / "evidence"
RUNS_PER_SNIPPET: Final = 5
SNIPPETS: Final = {
    "python": REPOSITORY_ROOT / "quickstart" / "python" / "quickstart.py",
    "node": REPOSITORY_ROOT / "quickstart" / "node" / "quickstart.mjs",
}
# 10 snippet runs and 2 probes that may be served entropy, at 1 KiB each; bad tokens are free.
PLANNED_KIB: Final = len(SNIPPETS) * RUNS_PER_SNIPPET + 2
LEDGER_STOP_KIB: Final = 8192
LEDGER_FIELDS: Final = ["occurred_at", "purpose", "kib_requested", "status"]
WRONG_TOKEN: Final = "deliberately-wrong-token-for-the-401-probe"  # noqa: S105  not a secret
NAMED_USER_AGENT: Final = "qrypt-quickstart-python/1.0"
RUNTIME_TARGET_SECONDS: Final = 3.0
TOKEN_PLACEHOLDER: Final = "[token]"  # noqa: S105  the placeholder that replaces a token
HEADERS_RECORDED: Final = ("content-type", "retry-after", "server", "cf-ray")


class LiveCheckRefusedError(Exception):
    """The live check would not start: no token, or a ledger too close to the stop."""


class SnippetRun(BaseModel):
    """One timed run of a quickstart against the endpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snippet: str
    run_number: int
    seconds: float
    exit_code: int
    succeeded: bool
    message: str


def scrub(text: str, token: str) -> str:
    """Replace every copy of the token in a text with a placeholder.

    Raises:
        ValueError: If the token is empty, which would scrub nothing and hide the mistake.
    """
    if not token:
        message = "scrub needs the token's value; an empty token scrubs nothing"
        raise ValueError(message)
    return text.replace(token, TOKEN_PLACEHOLDER)


def ledger_total_kib(ledger: Path) -> int:
    """Return the KiB the ledger records as requested, in total; 0 when it does not exist."""
    if not ledger.exists():
        return 0
    with ledger.open() as ledger_file:
        return sum(int(row["kib_requested"]) for row in csv.DictReader(ledger_file))


def record_request(ledger: Path, *, purpose: str, kib_requested: int, status: str) -> None:
    """Append one request to the ledger, writing its header when the ledger is new."""
    is_new_ledger = not ledger.exists()
    with ledger.open("a", newline="") as ledger_file:
        writer = csv.DictWriter(ledger_file, fieldnames=LEDGER_FIELDS)
        if is_new_ledger:
            writer.writeheader()
        writer.writerow(
            {
                "occurred_at": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "purpose": purpose,
                "kib_requested": kib_requested,
                "status": status,
            }
        )


def run_snippet_once(snippet: str, *, api_url: str, token: str, run_number: int) -> SnippetRun:
    """Run one quickstart as a developer does, in an empty folder, and time it end to end."""
    with tempfile.TemporaryDirectory() as work_directory:
        copied_snippet = Path(work_directory) / SNIPPETS[snippet].name
        shutil.copy(SNIPPETS[snippet], copied_snippet)
        interpreter = sys.executable if snippet == "python" else shutil.which("node") or "node"
        environment = {key: value for key, value in os.environ.items() if key != "QRYPT_API_KEY"}
        environment.update({"QRYPT_API_KEY": token, "QRYPT_API_URL": api_url})
        started_at = time.monotonic()
        completed = subprocess.run(  # noqa: S603  this repository's snippet, with this Python or node
            [interpreter, str(copied_snippet)],
            check=False,
            cwd=work_directory,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )
        elapsed_seconds = time.monotonic() - started_at
    output_lines = (completed.stdout + completed.stderr).strip().splitlines()
    return SnippetRun(
        snippet=snippet,
        run_number=run_number,
        seconds=round(elapsed_seconds, 3),
        exit_code=completed.returncode,
        succeeded=completed.returncode == 0 and "Success" in completed.stdout,
        message=scrub(output_lines[-1] if output_lines else "", token),
    )


def probe(api_url: str, *, token: str, headers: dict[str, str]) -> dict[str, object]:
    """Make one request for 1 KiB and record what came back, never the entropy itself."""
    request = urllib.request.Request(f"{api_url}?size=1", headers=headers)  # noqa: S310  the endpoint or the mock
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310  the same
            status = response.status
            response_headers = response.headers
            body = response.read()
    except urllib.error.HTTPError as http_error:
        status = http_error.code
        response_headers = http_error.headers
        body = http_error.read()
    recorded: dict[str, object] = {
        "status": status,
        "headers": {
            name: response_headers.get(name)
            for name in HEADERS_RECORDED
            if name in response_headers
        },
    }
    try:
        answer = json.loads(body)
    except ValueError:
        recorded["body_excerpt"] = scrub(body[:300].decode("utf-8", "replace"), token)
        return recorded
    if isinstance(answer, dict) and isinstance(answer.get("random"), list):
        recorded["answer_keys"] = sorted(answer)
        recorded["size"] = answer.get("size")
        recorded["decoded_block_bytes"] = [
            len(base64.b64decode(block)) for block in answer["random"]
        ]
    else:
        recorded["body_excerpt"] = scrub(json.dumps(answer)[:300], token)
    return recorded


def run_live_check(*, api_url: str, token: str, evidence_directory: Path) -> list[SnippetRun]:
    """Run the snippets and the probes against the endpoint, recording everything.

    Args:
        api_url: The endpoint: Qrypt's for the live check, the mock's in tests.
        token: The access token; never written anywhere.
        evidence_directory: Where the runs, the probes and the ledger are written.

    Returns:
        The timed snippet runs.

    Raises:
        LiveCheckRefusedError: Before any request, if there is no token or the ledger would pass
            the stop.
    """
    if not token:
        message = "no QRYPT_API_KEY: put the token in the environment or the repository's .env"
        raise LiveCheckRefusedError(message)
    evidence_directory.mkdir(parents=True, exist_ok=True)
    ledger = evidence_directory / "live_usage.csv"
    already_used_kib = ledger_total_kib(ledger)
    if already_used_kib + PLANNED_KIB > LEDGER_STOP_KIB:
        message = (
            f"the ledger holds {already_used_kib:,} KiB; {PLANNED_KIB} more would pass the "
            f"{LEDGER_STOP_KIB:,} KiB stop"
        )
        raise LiveCheckRefusedError(message)
    runs: list[SnippetRun] = []
    for snippet in SNIPPETS:
        for run_number in range(1, RUNS_PER_SNIPPET + 1):
            run = run_snippet_once(snippet, api_url=api_url, token=token, run_number=run_number)
            record_request(
                ledger,
                purpose=f"{snippet} run {run_number}",
                kib_requested=1,
                status=f"exit {run.exit_code}",
            )
            runs.append(run)
    good_headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    probe_plan = {
        "answer_shape": (1, {**good_headers, "User-Agent": NAMED_USER_AGENT}),
        "without_accept": (1, {"Authorization": f"Bearer {token}", "User-Agent": NAMED_USER_AGENT}),
        "bad_token_named_client": (
            0,
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {WRONG_TOKEN}",
                "User-Agent": NAMED_USER_AGENT,
            },
        ),
        "bad_token_python_default_client": (
            0,
            {"Accept": "application/json", "Authorization": f"Bearer {WRONG_TOKEN}"},
        ),
    }
    probes: dict[str, dict[str, object]] = {}
    for probe_name, (kib_requested, headers) in probe_plan.items():
        probes[probe_name] = probe(api_url, token=token, headers=headers)
        record_request(
            ledger,
            purpose=f"probe {probe_name}",
            kib_requested=kib_requested,
            status=str(probes[probe_name]["status"]),
        )
    with (evidence_directory / "live_runs.csv").open("w", newline="") as runs_file:
        writer = csv.DictWriter(runs_file, fieldnames=list(SnippetRun.model_fields))
        writer.writeheader()
        writer.writerows(run.model_dump() for run in runs)
    probes_text = scrub(json.dumps(probes, indent=2) + "\n", token)
    (evidence_directory / "live_probes.json").write_text(probes_text)
    return runs


def main() -> None:
    """Run the live check against Qrypt's endpoint with the owner's token, and print a summary."""
    token = (
        os.environ.get("QRYPT_API_KEY") or dotenv_values(ENV_FILE).get("QRYPT_API_KEY") or ""
    ).strip()
    try:
        runs = run_live_check(
            api_url=LIVE_API_URL, token=token, evidence_directory=EVIDENCE_DIRECTORY
        )
    except LiveCheckRefusedError as refusal:
        sys.exit(f"live-check: refused: {refusal}")
    for snippet in SNIPPETS:
        seconds = [run.seconds for run in runs if run.snippet == snippet]
        successes = sum(run.succeeded for run in runs if run.snippet == snippet)
        print(  # noqa: T201  a command-line tool
            f"live-check: {snippet}: {successes} of {len(seconds)} succeeded, "
            f"median {statistics.median(seconds):.2f} s, slowest {max(seconds):.2f} s "
            f"(target under {RUNTIME_TARGET_SECONDS:.0f} s)"
        )
    total_kib = ledger_total_kib(EVIDENCE_DIRECTORY / "live_usage.csv")
    print(f"live-check: the ledger now holds {total_kib:,} KiB of {LEDGER_STOP_KIB:,}")  # noqa: T201  a command-line tool


if __name__ == "__main__":
    main()
