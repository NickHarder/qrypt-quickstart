"""A local stand-in for Qrypt's quantum entropy endpoint, for tests, CI and the agent harness.

It answers `GET /api/v1/quantum-entropy?size=<KiB>` the way Qrypt's documentation says the real
endpoint does (docs.qrypt.com/eaas, read 2026-10-19): a JSON body `{"random": [...], "size": n}`
holding `n` base64 blocks of 1,024 bytes each, for `n` from 1 to 512.

The token chooses the answer, so a test can ask for any status without touching the live API:
`mock-200` gets entropy, `mock-400`, `mock-401`, `mock-403`, `mock-429`, `mock-500` and `mock-503`
get that status, and any other token gets 401. Three tokens get a 200 whose body holds no usable
block (`mock-not-json`, `mock-no-block`, `mock-short-block`), for the snippets' failure tests. Given
a certificate, the mock serves HTTPS, so a client that does not trust it fails as it would behind
a TLS-intercepting proxy.

Two answers are this mock's guesses, not Qrypt's documented behavior, until the live check records
what Qrypt does (docs/PLAN.md, Phase 7): the JSON shape of an error body, and a 400 to a request
without `Accept: application/json`. Qrypt's page requires the header and names no status for its
absence; the mock refuses it so that a snippet that forgets the header fails here first.

Run it on its own with `python -m qrypt_quickstart.mock_server --port 8765`.
"""

import argparse
import base64
import json
import os
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import TracebackType
from typing import Final, Self
from urllib.parse import parse_qs, urlsplit

from pydantic import BaseModel, ConfigDict

ENTROPY_PATH: Final = "/api/v1/quantum-entropy"
BYTES_PER_KIB: Final = 1024
LARGEST_SIZE_KIB: Final = 512
SUCCESS_TOKEN: Final = "mock-200"  # noqa: S105  a mock token, not a secret
STATUS_TOKENS: Final = {f"mock-{status}": status for status in (400, 401, 403, 429, 500, 503)}
BAD_BODIES: Final = {
    "mock-not-json": b"<html><body>Service temporarily unavailable</body></html>",
    "mock-no-block": b'{"random": [], "size": 1}',
    "mock-short-block": b'{"random": ["AAAA"], "size": 1}',
}
SHUTDOWN_POLL_SECONDS: Final = 0.05
ERROR_REASONS: Final = {
    400: "Bad request",
    401: "Access token invalid or expired",
    403: "Limit reached",
    404: "Not found",
    429: "Rate limit reached",
    500: "Internal server error",
    503: "Not enough supply",
}


class RecordedRequest(BaseModel):
    """One request the mock received, and the entropy it served in answer, if any."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    size_kib: int | None
    accept: str
    authorization: str
    user_agent: str
    status: int
    served_bytes: bytes = b""


def parse_size_kib(query: str) -> int | None:
    """Return the `size` query parameter as an integer, or None when it is missing or not one.

    Args:
        query: The query string of the request, without the `?`.

    Returns:
        The size in KiB as the client wrote it, or None.
    """
    size_values = parse_qs(query).get("size", [])
    if len(size_values) != 1 or not size_values[0].isdigit():
        return None
    return int(size_values[0])


class MockQryptServer:
    """A threaded HTTP server on 127.0.0.1 that plays Qrypt's entropy endpoint.

    Use it as a context manager: it starts on a free port on entry and stops on exit. Every request
    it answers is appended to `recorded_requests`.
    """

    def __init__(self, port: int = 0, tls_certificate: tuple[Path, Path] | None = None) -> None:
        """Create the server; `port` 0 lets the system choose a free one.

        Args:
            port: The port to listen on.
            tls_certificate: A certificate and its private key (PEM) to serve HTTPS with, or None
                for plain HTTP.
        """
        self.recorded_requests: list[RecordedRequest] = []
        self._recording_lock = threading.Lock()
        handler_class = self._handler_class()
        self._http_server = ThreadingHTTPServer(("127.0.0.1", port), handler_class)
        self._scheme = "http" if tls_certificate is None else "https"
        if tls_certificate is not None:
            tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls_context.load_cert_chain(*tls_certificate)
            self._http_server.socket = tls_context.wrap_socket(
                self._http_server.socket, server_side=True
            )
        self._serving_thread = threading.Thread(
            target=self._http_server.serve_forever,
            kwargs={"poll_interval": SHUTDOWN_POLL_SECONDS},
            name="mock-qrypt",
            daemon=True,
        )

    @property
    def url(self) -> str:
        """The endpoint's full URL, without the query string."""
        host, port = self._http_server.server_address[:2]
        return f"{self._scheme}://{host!s}:{port}{ENTROPY_PATH}"

    def __enter__(self) -> Self:
        """Start serving in a background thread."""
        self._serving_thread.start()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop serving and release the port."""
        self._http_server.shutdown()
        self._http_server.server_close()

    def serve_until_interrupted(self) -> None:
        """Serve in the calling thread until the process is interrupted."""
        try:
            self._http_server.serve_forever()
        finally:
            self._http_server.server_close()

    def _record(self, recorded_request: RecordedRequest) -> None:
        """Append one request to the record, safely across the server's threads."""
        with self._recording_lock:
            self.recorded_requests.append(recorded_request)

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        """Return a request handler class bound to this server's record."""
        mock_server = self

        class EntropyRequestHandler(BaseHTTPRequestHandler):
            """Answers each GET as Qrypt's endpoint would, for the token it carries."""

            def do_GET(self) -> None:
                """Answer one GET request."""
                split_url = urlsplit(self.path)
                size_kib = parse_size_kib(split_url.query)
                authorization = self.headers.get("Authorization", "")
                token = authorization.removeprefix("Bearer ").strip()
                status, served_bytes = choose_answer(
                    path=split_url.path,
                    size_kib=size_kib,
                    accept=self.headers.get("Accept", ""),
                    token=token,
                )
                mock_server._record(
                    RecordedRequest(
                        path=split_url.path,
                        size_kib=size_kib,
                        accept=self.headers.get("Accept", ""),
                        authorization=authorization,
                        user_agent=self.headers.get("User-Agent", ""),
                        status=status,
                        served_bytes=served_bytes,
                    )
                )
                if status == 200 and token in BAD_BODIES:
                    self._send_body(status, BAD_BODIES[token])
                else:
                    self._send_answer(status, served_bytes, size_kib)

            def _send_answer(self, status: int, served_bytes: bytes, size_kib: int | None) -> None:
                """Write the status line, the headers and the JSON body."""
                if status == 200:
                    blocks = [
                        served_bytes[offset : offset + BYTES_PER_KIB]
                        for offset in range(0, len(served_bytes), BYTES_PER_KIB)
                    ]
                    body: dict[str, object] = {
                        "random": [base64_text(block) for block in blocks],
                        "size": size_kib,
                    }
                else:
                    body = {"error": ERROR_REASONS.get(status, "Error")}
                self._send_body(status, json.dumps(body).encode())

            def _send_body(self, status: int, encoded_body: bytes) -> None:
                """Write the status line, the headers and a body given as bytes."""
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded_body)))
                self.end_headers()
                self.wfile.write(encoded_body)

            def log_message(self, format: str, *args: object) -> None:  # noqa: A002  http.server's name
                """Keep the test output quiet: the record holds every request."""

        return EntropyRequestHandler


def base64_text(block: bytes) -> str:
    """Return a block of bytes as standard base64 text, as Qrypt sends it."""
    return base64.b64encode(block).decode("ascii")


def choose_answer(*, path: str, size_kib: int | None, accept: str, token: str) -> tuple[int, bytes]:
    """Decide the status and the entropy for one request.

    Args:
        path: The request's path.
        size_kib: The `size` parameter, or None when it is missing or not an integer.
        accept: The request's `Accept` header.
        token: The bearer token, without the `Bearer ` prefix.

    Returns:
        The HTTP status, and the bytes served (empty unless the status is 200).
    """
    if path != ENTROPY_PATH:
        return 404, b""
    is_size_in_range = size_kib is not None and 1 <= size_kib <= LARGEST_SIZE_KIB
    if "application/json" not in accept or size_kib is None or not is_size_in_range:
        return 400, b""
    is_known_success_token = token == SUCCESS_TOKEN or token in BAD_BODIES
    status = STATUS_TOKENS.get(token, 200 if is_known_success_token else 401)
    served_bytes = os.urandom(size_kib * BYTES_PER_KIB) if token == SUCCESS_TOKEN else b""
    return status, served_bytes


def main() -> None:
    """Serve the mock on the port given on the command line until interrupted."""
    parser = argparse.ArgumentParser(description="A local stand-in for Qrypt's entropy endpoint.")
    parser.add_argument("--port", type=int, default=8765)
    arguments = parser.parse_args()
    MockQryptServer(port=arguments.port).serve_until_interrupted()


if __name__ == "__main__":
    main()
