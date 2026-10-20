"""The recording relay: Qrypt's entropy endpoint, passed through unchanged, recorded and capped.

In a live round of the agent-readiness test, `api-eus.qrypt.com` resolves to this relay inside the
agent's container (the same mapping the mock uses), and the relay forwards each request to Qrypt.
That gives a live run what a mock run has: every request the agent's program made, with what Qrypt
served, so one judge decides both (`agent_harness.judge_run`). It changes nothing on the way:
the request goes up with the headers the program sent, and Qrypt's status and body come back as
they are.

It also guards the owner's entropy allotment, which a looping agent could otherwise spend:

- a cap per run (64 KiB by default): past it, the relay answers 403 itself, without forwarding;
- the ledger's stop (8,192 KiB, shared with the live check): past it, the same;
- only `GET /api/v1/quantum-entropy` is forwarded; any other path gets 404 here.

Each forwarded request gets a ledger row in `evidence/live_usage.csv`, charged its `size` in KiB
when Qrypt served entropy and 0 otherwise. The relay never sees the token as anything but a header
it passes on; it writes the token nowhere.
"""

import base64
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Final

from .live_check import LEDGER_STOP_KIB, ledger_total_kib, record_request
from .mock_server import ENTROPY_PATH, MockQryptServer, parse_size_kib

DEFAULT_RUN_CAP_KIB: Final = 64
UPSTREAM_TIMEOUT_SECONDS: Final = 15
FORWARDED_HEADERS: Final = ("Accept", "Authorization", "User-Agent")
REFUSAL_BODY: Final = json.dumps(
    {"error": "Limit reached: the agent-readiness harness's budget for this run is used up"}
).encode()


def served_bytes_of(body: bytes) -> bytes:
    """Return the entropy an answer carried, decoded from its base64 blocks; b"" if none."""
    try:
        answer = json.loads(body)
        return b"".join(base64.b64decode(block) for block in answer["random"])
    except (ValueError, KeyError, TypeError):
        return b""


class RecordingRelay(MockQryptServer):
    """A server that forwards each entropy request to an upstream endpoint and records it.

    It records requests exactly as the mock does (`recorded_requests`), so the harness treats both
    alike; only the answer differs: it comes from upstream, within the caps.
    """

    def __init__(
        self,
        *,
        upstream_url: str,
        ledger: Path,
        run_cap_kib: int = DEFAULT_RUN_CAP_KIB,
        ledger_stop_kib: int = LEDGER_STOP_KIB,
        port: int = 0,
        tls_certificate: tuple[Path, Path] | None = None,
        host: str = "127.0.0.1",
    ) -> None:
        """Create the relay.

        Args:
            upstream_url: The endpoint to forward to: Qrypt's, or the mock's in tests.
            ledger: The live-usage ledger each forwarded request is written to.
            run_cap_kib: The entropy one run may request before the relay refuses.
            ledger_stop_kib: The ledger total past which the relay refuses.
            port: The port to listen on; 0 lets the system choose.
            tls_certificate: A certificate and key to serve HTTPS with, as `api-eus.qrypt.com`.
            host: The address to listen on.
        """
        super().__init__(port=port, tls_certificate=tls_certificate, host=host)
        self._upstream_url = upstream_url
        self._ledger = ledger
        self._run_cap_kib = run_cap_kib
        self._ledger_stop_kib = ledger_stop_kib
        self._run_label = "no run started"
        self._run_used_kib = 0
        self._budget_lock = threading.Lock()

    def start_run(self, run_label: str) -> None:
        """Begin a new run: its ledger rows carry this label, and its cap starts afresh."""
        with self._budget_lock:
            self._run_label = run_label
            self._run_used_kib = 0

    def answer(self, *, path: str, query: str, headers: dict[str, str]) -> tuple[int, bytes, bytes]:
        """Forward one request upstream unchanged, within the caps, and return Qrypt's answer.

        Args:
            path: The request's path.
            query: The request's query string, without the `?`.
            headers: The request's `Accept`, `Authorization` and `User-Agent` ("" when missing).

        Returns:
            The HTTP status, the entropy served (decoded), and the body exactly as upstream sent it.
        """
        if path != ENTROPY_PATH:
            return 404, b"", json.dumps({"error": "Not found"}).encode()
        requested_kib = parse_size_kib(query) or 0
        with self._budget_lock:
            is_over_run_cap = self._run_used_kib + requested_kib > self._run_cap_kib
            is_over_stop = ledger_total_kib(self._ledger) + requested_kib > self._ledger_stop_kib
            if is_over_run_cap or is_over_stop:
                return 403, b"", REFUSAL_BODY
            self._run_used_kib += requested_kib
            run_label = self._run_label
        forwarded_headers = {name: headers[name] for name in FORWARDED_HEADERS if headers[name]}
        upstream_request = urllib.request.Request(  # noqa: S310  Qrypt's https endpoint, or the mock
            f"{self._upstream_url}?{query}", headers=forwarded_headers
        )
        try:
            with urllib.request.urlopen(  # noqa: S310  the same
                upstream_request, timeout=UPSTREAM_TIMEOUT_SECONDS
            ) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as http_error:
            status = http_error.code
            body = http_error.read()
        except (urllib.error.URLError, TimeoutError) as failure:
            status = 502
            body = json.dumps({"error": f"the relay could not reach Qrypt: {failure}"}).encode()
        served_bytes = served_bytes_of(body) if status == 200 else b""
        record_request(
            self._ledger,
            purpose=f"agent {run_label}",
            kib_requested=requested_kib if status == 200 else 0,
            status=str(status),
        )
        return status, served_bytes, body
