import base64
import json
import urllib.error
import urllib.request

import pytest

from qrypt_quickstart.mock_server import MockQryptServer


def fetch(
    server: MockQryptServer, token: str, *, size: int = 1, accept: bool = True
) -> tuple[int, bytes]:
    headers = {"Authorization": f"Bearer {token}"}
    if accept:
        headers["Accept"] = "application/json"
    request = urllib.request.Request(f"{server.url}?size={size}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as http_error:
        return http_error.code, http_error.read()


def test_a_good_token_gets_size_kib_of_base64_blocks() -> None:
    with MockQryptServer() as server:
        status, body = fetch(server, "mock-200", size=2)
    payload = json.loads(body)
    assert status == 200
    assert payload["size"] == 2
    assert [len(base64.b64decode(block)) for block in payload["random"]] == [1024, 1024]


def test_the_server_records_what_it_served_and_what_it_was_sent() -> None:
    with MockQryptServer() as server:
        fetch(server, "mock-200")
        recorded = server.recorded_requests[0]
    assert recorded.size_kib == 1
    assert recorded.accept == "application/json"
    assert recorded.authorization == "Bearer mock-200"
    assert len(recorded.served_bytes) == 1024


@pytest.mark.parametrize("status_code", [401, 403, 429, 500, 503])
def test_a_status_token_gets_that_status(status_code: int) -> None:
    with MockQryptServer() as server:
        status, _ = fetch(server, f"mock-{status_code}")
    assert status == status_code


def test_an_unknown_token_is_unauthorized() -> None:
    with MockQryptServer() as server:
        status, _ = fetch(server, "not-a-mock-token")
    assert status == 401


@pytest.mark.parametrize("size", [0, 513])
def test_a_size_out_of_range_is_a_bad_request(size: int) -> None:
    with MockQryptServer() as server:
        status, _ = fetch(server, "mock-200", size=size)
    assert status == 400


def test_a_request_without_accept_is_refused_by_the_mock() -> None:
    with MockQryptServer() as server:
        status, _ = fetch(server, "mock-200", accept=False)
    assert status == 400
