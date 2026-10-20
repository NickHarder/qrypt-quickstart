"""The Rust quickstart, built and run as a developer runs it, against the mock instead of Qrypt.

Each run copies the built binary into an empty directory, so no `.env` of this repository is found,
and points `QRYPT_API_URL` at the mock, so no request can reach the live API. The errors it shares
with the other snippets are tested in `test_quickstart_errors.py`.
"""

import base64
from pathlib import Path

import pytest

from qrypt_quickstart.harness_certificates import write_authority_and_server_certificate
from qrypt_quickstart.mock_server import MockQryptServer
from snippet_runner import SnippetRun, run_snippet


def test_a_good_token_prints_the_success_line(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run = run_snippet("rust", tmp_path, api_url=server.url, token="mock-200")
    assert run.exit_code == 0, run.stderr
    assert run.stdout.strip() == (
        "Success: an AES-256 key from Qrypt quantum entropy passed AES-GCM (key not shown)."
    )


@pytest.mark.parametrize(
    "env_file_text",
    [
        "QRYPT_API_KEY=mock-200\n",
        '# the Entropy token\nexport QRYPT_API_KEY="mock-200"\n',
        "QRYPT_API_KEY='mock-200'  # from portal.qrypt.com\n",
    ],
)
def test_the_token_is_read_from_a_dot_env_file_in_the_folder(
    tmp_path: Path, env_file_text: str
) -> None:
    (tmp_path / ".env").write_text(env_file_text)
    with MockQryptServer() as server:
        run = run_snippet("rust", tmp_path, api_url=server.url, token=None)
        recorded = server.recorded_requests
    assert run.exit_code == 0, run.stderr
    assert recorded[0].authorization == "Bearer mock-200"


def test_the_key_never_reaches_the_output(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run = run_snippet("rust", tmp_path, api_url=server.url, token="mock-200")
        served_bytes = server.recorded_requests[0].served_bytes
    output = run.stdout + run.stderr
    key_bytes = served_bytes[:32]
    for key_form in (
        key_bytes.hex(),
        key_bytes.hex().upper(),
        base64.b64encode(key_bytes).decode()[:40],
        base64.b64encode(served_bytes).decode()[:40],
        " ".join(f"{byte:02x}" for byte in key_bytes[:8]),
        ", ".join(str(byte) for byte in key_bytes[:8]),
    ):
        assert key_form not in output


def test_it_asks_for_one_kib_with_both_headers_and_names_itself(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run_snippet("rust", tmp_path, api_url=server.url, token="mock-200")
        recorded = server.recorded_requests
    assert len(recorded) == 1
    assert recorded[0].size_kib == 1
    assert recorded[0].accept == "application/json"
    assert recorded[0].authorization == "Bearer mock-200"
    assert recorded[0].user_agent.startswith("qrypt-quickstart-rust/")


def test_it_writes_no_file(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run_snippet("rust", tmp_path, api_url=server.url, token="mock-200")
    assert sorted(path.name for path in tmp_path.iterdir()) == ["quickstart"]


@pytest.mark.parametrize("token", [None, "", "   "])
def test_a_missing_token_says_where_to_get_one_and_how_to_set_it(
    tmp_path: Path, token: str | None
) -> None:
    with MockQryptServer() as server:
        run = run_snippet("rust", tmp_path, api_url=server.url, token=token)
        request_count = len(server.recorded_requests)
    assert run.exit_code != 0
    assert run.stderr.strip() == (
        "Set QRYPT_API_KEY=<token> in .env (Entropy tokens: portal.qrypt.com)"
    )
    assert not run.shows_a_traceback
    assert request_count == 0


def test_a_company_root_certificate_named_in_ssl_cert_file_is_trusted(tmp_path: Path) -> None:
    # Behind a TLS-inspecting proxy, the troubleshooting page's fix is SSL_CERT_FILE: the program
    # trusts the platform's certificates, not only the roots built into the program.
    authority, certificate, private_key = write_authority_and_server_certificate(
        tmp_path / "tls", host_name="localhost"
    )
    work_directory = tmp_path / "work"
    work_directory.mkdir()
    with MockQryptServer(tls_certificate=(certificate, private_key)) as server:
        run = run_snippet(
            "rust",
            work_directory,
            api_url=server.url.replace("127.0.0.1", "localhost"),
            token="mock-200",
            extra_environment={"SSL_CERT_FILE": str(authority)},
        )
    assert run.exit_code == 0, run.stderr
    assert "Success" in run.stdout


def test_a_panic_would_be_caught_as_a_traceback() -> None:
    panicked_run = SnippetRun(
        exit_code=101,
        stdout="",
        stderr="thread 'main' panicked at src/main.rs:20:5:\nindex out of bounds",
        elapsed_seconds=0.1,
    )
    assert panicked_run.shows_a_traceback
