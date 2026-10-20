"""The harness's certificate authority lets a container reach the mock under Qrypt's own host name.

In the container mode, `api-eus.qrypt.com` resolves to the mock on the host, so the agent's program
calls Qrypt's real URL. These tests prove the TLS half: a client that trusts only the harness's
authority completes a handshake with the mock under that host name, and one that does not, fails.
"""

import socket
import ssl
from pathlib import Path

import pytest

from qrypt_quickstart.harness_certificates import write_authority_and_server_certificate
from qrypt_quickstart.mock_server import MockQryptServer


def handshake(port: int, *, trusted_authority: Path | None, host_name: str) -> None:
    context = ssl.create_default_context(
        cafile=str(trusted_authority) if trusted_authority else None
    )
    with (
        socket.create_connection(("127.0.0.1", port), timeout=5) as connection,
        context.wrap_socket(connection, server_hostname=host_name),
    ):
        pass


def test_a_client_trusting_the_authority_reaches_the_mock_as_api_eus(tmp_path: Path) -> None:
    authority, certificate, private_key = write_authority_and_server_certificate(
        tmp_path, host_name="api-eus.qrypt.com"
    )
    with MockQryptServer(tls_certificate=(certificate, private_key)) as server:
        port = int(server.url.split(":")[2].split("/")[0])
        handshake(port, trusted_authority=authority, host_name="api-eus.qrypt.com")


def test_a_client_without_the_authority_is_refused(tmp_path: Path) -> None:
    _, certificate, private_key = write_authority_and_server_certificate(
        tmp_path, host_name="api-eus.qrypt.com"
    )
    with MockQryptServer(tls_certificate=(certificate, private_key)) as server:
        port = int(server.url.split(":")[2].split("/")[0])
        with pytest.raises(ssl.SSLCertVerificationError):
            handshake(port, trusted_authority=None, host_name="api-eus.qrypt.com")
