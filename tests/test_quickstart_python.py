"""The Python quickstart, run as a developer runs it, against the mock instead of Qrypt.

Each run copies the snippet into an empty directory, so no `.env` of this repository is found,
and points `QRYPT_API_URL` at the mock, so no request can reach the live API.
"""

import base64
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.mock_server import MockQryptServer

SNIPPET: Final = Path(__file__).resolve().parents[1] / "quickstart" / "python" / "quickstart.py"


def run_snippet(
    work_directory: Path, *, api_url: str, token: str | None, optimize: bool = False
) -> subprocess.CompletedProcess[str]:
    copied_snippet = work_directory / "quickstart.py"
    shutil.copy(SNIPPET, copied_snippet)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("QRYPT_")}
    environment["QRYPT_API_URL"] = api_url
    if token is not None:
        environment["QRYPT_API_KEY"] = token
    command = [sys.executable, *(["-O"] if optimize else []), str(copied_snippet)]
    return subprocess.run(
        command,
        check=False,
        cwd=work_directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_a_good_token_prints_the_success_line(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        result = run_snippet(tmp_path, api_url=server.url, token="mock-200")
    assert result.returncode == 0, result.stderr
    assert "Success" in result.stdout


def test_the_success_line_holds_under_python_optimize(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        result = run_snippet(tmp_path, api_url=server.url, token="mock-200", optimize=True)
    assert result.returncode == 0, result.stderr


def test_the_key_never_reaches_the_output(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        result = run_snippet(tmp_path, api_url=server.url, token="mock-200")
        served_bytes = server.recorded_requests[0].served_bytes
    output = result.stdout + result.stderr
    key_bytes = served_bytes[:32]
    for key_form in (
        key_bytes.hex(),
        key_bytes.hex().upper(),
        base64.b64encode(key_bytes).decode()[:40],
        base64.b64encode(served_bytes).decode()[:40],
        repr(key_bytes)[2:40],
    ):
        assert key_form not in output


def test_it_asks_for_one_kib_with_both_headers_and_names_itself(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run_snippet(tmp_path, api_url=server.url, token="mock-200")
        recorded = server.recorded_requests
    assert len(recorded) == 1
    assert recorded[0].size_kib == 1
    assert recorded[0].accept == "application/json"
    assert recorded[0].authorization == "Bearer mock-200"
    assert recorded[0].user_agent.startswith("qrypt-quickstart-python/")


def test_it_writes_no_file(tmp_path: Path) -> None:
    with MockQryptServer() as server:
        run_snippet(tmp_path, api_url=server.url, token="mock-200")
    assert sorted(path.name for path in tmp_path.iterdir()) == ["quickstart.py"]


@pytest.mark.parametrize("token", [None, "", "   "])
def test_a_missing_token_says_where_to_get_one_and_how_to_set_it(
    tmp_path: Path, token: str | None
) -> None:
    with MockQryptServer() as server:
        result = run_snippet(tmp_path, api_url=server.url, token=token)
        request_count = len(server.recorded_requests)
    assert result.returncode != 0
    assert "QRYPT_API_KEY" in result.stderr
    assert "portal.qrypt.com" in result.stderr
    assert ".env" in result.stderr
    assert "Traceback" not in result.stderr
    assert request_count == 0
