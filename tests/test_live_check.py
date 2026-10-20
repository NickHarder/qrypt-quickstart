"""The live check, run against the mock: what it records, what it costs, and that it leaks nothing.

The live check (`make live-check`) is the only code here that calls Qrypt's API with the owner's
token. These tests run it against the mock with a planted token, so they cost nothing and can
prove the guards: it refuses before any request when the ledger would pass 8,192 KiB, it writes
the token's value nowhere, and it records every request it makes.
"""

import csv
import json
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.live_check import (
    LEDGER_STOP_KIB,
    PLANNED_KIB,
    REQUEST_SPACING_SECONDS,
    LiveCheckRefusedError,
    ledger_total_kib,
    run_live_check,
    scrub,
)
from qrypt_quickstart.mock_server import MockQryptServer

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
PLANTED_TOKEN: Final = "mock-200"  # noqa: S105  the mock's success token, not a secret
ASSESSMENT_BUDGET_KIB: Final = 10_240


def test_scrub_removes_every_copy_of_the_token() -> None:
    text = f"Authorization: Bearer {PLANTED_TOKEN} and again {PLANTED_TOKEN}"
    scrubbed = scrub(text, PLANTED_TOKEN)
    assert PLANTED_TOKEN not in scrubbed
    assert scrubbed.count("[token]") == 2


def test_scrub_refuses_an_empty_token() -> None:
    with pytest.raises(ValueError, match="token"):
        scrub("text", "")


def no_pause(seconds: float) -> None:
    """Stand in for `time.sleep`, so a test against the mock does not wait between requests."""
    del seconds


def test_a_run_against_the_mock_records_runs_probes_and_every_request(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run_live_check(
            api_url=server.url, token=PLANTED_TOKEN, evidence_directory=tmp_path, pause=no_pause
        )
        request_count = len(server.recorded_requests)
    with (tmp_path / "live_runs.csv").open() as runs_file:
        runs = list(csv.DictReader(runs_file))
    assert sorted({run["snippet"] for run in runs}) == ["node", "python", "rust"]
    assert len(runs) == 15
    assert all(run["succeeded"] == "True" for run in runs)
    with (tmp_path / "live_usage.csv").open() as ledger_file:
        ledger = list(csv.DictReader(ledger_file))
    assert len(ledger) == request_count
    assert ledger_total_kib(tmp_path / "live_usage.csv") == PLANNED_KIB
    probes = json.loads((tmp_path / "live_probes.json").read_text())
    assert set(probes) == {
        "answer_shape",
        "without_accept",
        "bad_token_named_client",
        "bad_token_python_default_client",
    }
    assert probes["answer_shape"]["status"] == 200
    assert probes["answer_shape"]["decoded_block_bytes"] == [1024]
    # The mock answers a wrong token as Qrypt did live: 403, not the documented 401.
    assert probes["bad_token_named_client"]["status"] == 403


def test_it_pauses_before_every_request_but_the_first(tmp_path: Path) -> None:
    # Live, a trial key got 429 for a second request 0.36 s after the first, and every 429 had
    # cleared within 1.5 s (evidence/live_rate_limit.json); the spacing keeps runs apart past that.
    pauses_seconds: list[float] = []
    with MockQryptServer() as server:
        run_live_check(
            api_url=server.url,
            token=PLANTED_TOKEN,
            evidence_directory=tmp_path,
            pause=pauses_seconds.append,
        )
        request_count = len(server.recorded_requests)
    assert REQUEST_SPACING_SECONDS >= 2.0
    assert pauses_seconds == [REQUEST_SPACING_SECONDS] * (request_count - 1)


def test_nothing_it_writes_holds_the_token(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run_live_check(
            api_url=server.url, token=PLANTED_TOKEN, evidence_directory=tmp_path, pause=no_pause
        )
    for written_file in tmp_path.iterdir():
        assert PLANTED_TOKEN not in written_file.read_text(), written_file.name


def test_it_refuses_before_any_request_when_the_ledger_would_pass_the_stop(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "live_usage.csv"
    ledger.write_text(
        "occurred_at,purpose,kib_requested,status\n"
        f"2026-10-20T00:00:00Z,earlier work,{LEDGER_STOP_KIB - PLANNED_KIB + 1},200\n"
    )
    with MockQryptServer() as server:
        with pytest.raises(LiveCheckRefusedError, match="8,192"):
            run_live_check(api_url=server.url, token=PLANTED_TOKEN, evidence_directory=tmp_path)
        request_count = len(server.recorded_requests)
    assert request_count == 0


def test_it_refuses_without_a_token(tmp_path: Path) -> None:
    with pytest.raises(LiveCheckRefusedError, match="QRYPT_API_KEY"):
        run_live_check(api_url="http://127.0.0.1:9/x", token="", evidence_directory=tmp_path)


def test_the_committed_ledger_stays_within_the_stop_and_the_budget() -> None:
    ledger = REPOSITORY_ROOT / "evidence" / "live_usage.csv"
    total_kib = ledger_total_kib(ledger) if ledger.exists() else 0
    assert total_kib <= LEDGER_STOP_KIB < ASSESSMENT_BUDGET_KIB
