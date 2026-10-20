"""The recording relay: Qrypt's endpoint, passed through unchanged, recorded, and capped.

In a live agent round the relay stands in for `api-eus.qrypt.com` and forwards each request to
Qrypt. These tests put the mock upstream, so they spend nothing and can prove the guards: requests
and answers pass unchanged, each forwarded request is recorded with the bytes served and a ledger
row, and past a run's cap or the ledger's stop the relay refuses without forwarding.
"""

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Final

from qrypt_quickstart.live_check import ledger_total_kib
from qrypt_quickstart.mock_server import MockQryptServer
from qrypt_quickstart.recording_relay import RecordingRelay

TOKEN: Final = "mock-200"  # noqa: S105  the mock's success token, not a secret


def fetch(
    url: str, *, size: int = 1, accept: bool = True, path_suffix: str = ""
) -> tuple[int, bytes]:
    headers = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "test-client"}
    if accept:
        headers["Accept"] = "application/json"
    request = urllib.request.Request(f"{url}{path_suffix}?size={size}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as http_error:
        return http_error.code, http_error.read()


def test_a_request_passes_through_unchanged_and_is_recorded(tmp_path: Path) -> None:
    ledger = tmp_path / "live_usage.csv"
    with (
        MockQryptServer() as upstream,
        RecordingRelay(upstream_url=upstream.url, ledger=ledger) as relay,
    ):
        relay.start_run("round 1 run 1")
        status, body = fetch(relay.url)
        upstream_request = upstream.recorded_requests[0]
        relayed_request = relay.recorded_requests[0]
    assert status == 200
    assert json.loads(body)["size"] == 1
    assert upstream_request.user_agent == "test-client"
    assert upstream_request.authorization == f"Bearer {TOKEN}"
    assert relayed_request.served_bytes == upstream_request.served_bytes
    assert ledger_total_kib(ledger) == 1
    assert "round 1 run 1" in ledger.read_text()


def test_a_missing_accept_header_is_passed_on_missing(tmp_path: Path) -> None:
    with (
        MockQryptServer() as upstream,
        RecordingRelay(upstream_url=upstream.url, ledger=tmp_path / "ledger.csv") as relay,
    ):
        relay.start_run("run")
        status, _ = fetch(relay.url, accept=False)
        upstream_accept = upstream.recorded_requests[0].accept
    assert status == 400
    assert upstream_accept == ""


def test_past_the_runs_cap_it_refuses_without_forwarding(tmp_path: Path) -> None:
    with (
        MockQryptServer() as upstream,
        RecordingRelay(
            upstream_url=upstream.url, ledger=tmp_path / "ledger.csv", run_cap_kib=2
        ) as relay,
    ):
        relay.start_run("run")
        first_status, _ = fetch(relay.url, size=2)
        second_status, second_body = fetch(relay.url, size=1)
        upstream_count = len(upstream.recorded_requests)
        relay.start_run("next run")
        third_status, _ = fetch(relay.url, size=1)
    assert first_status == 200
    assert second_status == 403
    assert b"harness" in second_body
    assert upstream_count == 1
    assert third_status == 200


def test_past_the_ledgers_stop_it_refuses_without_forwarding(tmp_path: Path) -> None:
    ledger = tmp_path / "live_usage.csv"
    ledger.write_text(
        "occurred_at,purpose,kib_requested,status\n2026-10-20T00:00:00Z,earlier,8192,200\n"
    )
    with (
        MockQryptServer() as upstream,
        RecordingRelay(upstream_url=upstream.url, ledger=ledger) as relay,
    ):
        relay.start_run("run")
        status, _ = fetch(relay.url)
        upstream_count = len(upstream.recorded_requests)
    assert status == 403
    assert upstream_count == 0
    assert ledger_total_kib(ledger) == 8192


def test_another_path_is_not_forwarded(tmp_path: Path) -> None:
    with (
        MockQryptServer() as upstream,
        RecordingRelay(upstream_url=upstream.url, ledger=tmp_path / "ledger.csv") as relay,
    ):
        relay.start_run("run")
        status, _ = fetch(relay.url, path_suffix="/../../admin")
        upstream_count = len(upstream.recorded_requests)
    assert status == 404
    assert upstream_count == 0


def test_a_failed_answer_costs_nothing_in_the_ledger(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.csv"
    with (
        MockQryptServer() as upstream,
        RecordingRelay(upstream_url=upstream.url, ledger=ledger) as relay,
    ):
        relay.start_run("run")
        fetch(relay.url, accept=False)
    assert ledger_total_kib(ledger) == 0
    assert len(ledger.read_text().splitlines()) == 2
