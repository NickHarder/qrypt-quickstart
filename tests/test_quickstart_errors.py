"""Every way the first run can fail, for every snippet: a clear message, a non-zero exit, no trace.

The brief's edge cases (RQ-11, RQ-12, RQ-13, RQ-17): each HTTP error Qrypt documents, a refused
connection, a certificate the machine does not trust, and a 200 whose body holds no usable block.
No snippet retries, so each failure costs one request at most.
"""

import html
import re
import socket
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.mock_server import MockQryptServer
from snippet_runner import run_snippet
from tls_certificate import write_self_signed_certificate

LANGUAGES: Final = ["python", "node", "rust"]
TROUBLESHOOTING_PAGE: Final = Path(__file__).resolve().parents[1] / "site" / "troubleshooting.html"
EXPECTED_PHRASES: Final = {
    400: ["HTTP 400", "size"],
    401: ["HTTP 401", "invalid or expired", "portal.qrypt.com"],
    # Live, Qrypt answers a wrong token with 403 too, so the message names that first.
    403: ["HTTP 403", "wrong token", "allotment"],
    # Not "30 requests": live, a trial key was refused at two within half a second.
    429: ["HTTP 429", "too many requests in a short time", "wait 10 seconds"],
    500: ["HTTP 500", "try again shortly"],
    503: ["HTTP 503", "try again shortly"],
}


def page_text() -> str:
    page = TROUBLESHOOTING_PAGE.read_text()
    return html.unescape(re.sub(r"<[^>]+>", "", page))


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("status_code", sorted(EXPECTED_PHRASES))
def test_each_documented_error_gets_its_own_message_after_one_request(
    tmp_path: Path, language: str, status_code: int
) -> None:
    with MockQryptServer() as server:
        run = run_snippet(language, tmp_path, api_url=server.url, token=f"mock-{status_code}")
        request_count = len(server.recorded_requests)
    assert run.exit_code != 0
    assert not run.shows_a_traceback, run.stderr
    assert request_count == 1
    for phrase in EXPECTED_PHRASES[status_code]:
        assert phrase in run.stderr, run.stderr


@pytest.mark.parametrize("language", LANGUAGES)
def test_a_mistyped_token_gets_a_message_that_names_the_token_first(
    tmp_path: Path, language: str
) -> None:
    # Qrypt's docs say 401 for a bad token; live it answered 403 "Forbidden or entropy quota
    # reached" (evidence/live_probes.json), and the mock now answers an unknown token the same way.
    with MockQryptServer() as server:
        run = run_snippet(language, tmp_path, api_url=server.url, token="a-mistyped-token")
    assert run.exit_code != 0
    assert "HTTP 403: wrong token" in run.stderr, run.stderr


@pytest.mark.parametrize("language", LANGUAGES)
def test_a_rate_limit_stops_at_once_instead_of_looping(tmp_path: Path, language: str) -> None:
    with MockQryptServer() as server:
        run = run_snippet(language, tmp_path, api_url=server.url, token="mock-429")
        request_count = len(server.recorded_requests)
    assert request_count == 1
    assert run.elapsed_seconds < 1.5


@pytest.mark.parametrize("status_code", sorted(EXPECTED_PHRASES))
def test_every_snippet_prints_the_same_message_and_the_page_quotes_it(
    tmp_path: Path, status_code: int
) -> None:
    messages = []
    for language in LANGUAGES:
        work_directory = tmp_path / language
        work_directory.mkdir()
        with MockQryptServer() as server:
            run = run_snippet(
                language, work_directory, api_url=server.url, token=f"mock-{status_code}"
            )
        messages.append(run.stderr.strip())
    assert len(set(messages)) == 1, messages
    assert messages[0] in page_text()


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("token", ["mock-not-json", "mock-no-block", "mock-short-block"])
def test_an_answer_without_a_usable_block_is_a_message_not_a_crash(
    tmp_path: Path, language: str, token: str
) -> None:
    with MockQryptServer() as server:
        run = run_snippet(language, tmp_path, api_url=server.url, token=token)
    assert run.exit_code != 0
    assert not run.shows_a_traceback, run.stderr
    assert "try again shortly" in run.stderr
    assert "Success" not in run.stdout


@pytest.mark.parametrize("language", LANGUAGES)
def test_a_refused_connection_is_a_message_not_a_crash(tmp_path: Path, language: str) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        closed_port = probe.getsockname()[1]
    run = run_snippet(
        language,
        tmp_path,
        api_url=f"http://127.0.0.1:{closed_port}/api/v1/quantum-entropy",
        token="mock-200",
    )
    assert run.exit_code != 0
    assert not run.shows_a_traceback, run.stderr
    assert "Could not get entropy" in run.stderr
    assert "troubleshooting" in run.stderr


@pytest.mark.parametrize("language", LANGUAGES)
def test_an_untrusted_certificate_is_named_not_a_crash(tmp_path: Path, language: str) -> None:
    certificate_path, private_key_path = write_self_signed_certificate(tmp_path / "tls")
    work_directory = tmp_path / "work"
    work_directory.mkdir()
    with MockQryptServer(tls_certificate=(certificate_path, private_key_path)) as server:
        run = run_snippet(language, work_directory, api_url=server.url, token="mock-200")
    assert run.exit_code != 0
    assert not run.shows_a_traceback, run.stderr
    assert "CERT" in run.stderr.upper()
    assert "troubleshooting" in run.stderr
