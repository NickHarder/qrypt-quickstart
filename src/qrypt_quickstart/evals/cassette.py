"""Recorded model exchanges, so the gate replays for free and offline.

Each exchange is stored under a `ref`: the SHA-256 of the case id, the model id, the system prompt
and the user message. Change any of them and replay misses, which is the point: a recording made
for one prompt must not answer for another. (The field is called `ref` so secret scanners do not
mistake the hash for a credential.)
"""

import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from .errors import CassetteMissError, EvalSetupError
from .models import StrictModel


class RecordedExchange(StrictModel):
    """One model call: the hash of its request, and the response it got."""

    ref: str
    response: str


class Cassette(StrictModel):
    """Every exchange recorded for one case."""

    case_id: str
    model: str
    exchanges: list[RecordedExchange]


def exchange_ref(*, case_id: str, model: str, system_prompt: str, user_message: str) -> str:
    """Return the hash that identifies one request."""
    canonical_request = json.dumps(
        {"case_id": case_id, "model": model, "system": system_prompt, "user": user_message},
        sort_keys=True,
    )
    return hashlib.sha256(canonical_request.encode()).hexdigest()


def cassette_file(cassettes_directory: Path, case_id: str) -> Path:
    """Return where a case's recording lives."""
    return cassettes_directory / f"{case_id}.json"


def load_cassette(cassettes_directory: Path, case_id: str) -> Cassette:
    """Read a case's recording.

    Raises:
        CassetteMissError: If the case has no recording.
        EvalSetupError: If the recording cannot be read; the message names the file.
    """
    recording_file = cassette_file(cassettes_directory, case_id)
    if not recording_file.exists():
        message = f"cassette miss: {case_id} has no recording at {recording_file}"
        raise CassetteMissError(message)
    try:
        return Cassette.model_validate_json(recording_file.read_text(encoding="utf-8"))
    except ValidationError as error:
        message = f"{recording_file}: {error}"
        raise EvalSetupError(message) from error


def save_cassette(cassettes_directory: Path, cassette: Cassette) -> Path:
    """Write a case's recording and return its path."""
    recording_file = cassette_file(cassettes_directory, cassette.case_id)
    recording_file.parent.mkdir(parents=True, exist_ok=True)
    recording_file.write_text(cassette.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return recording_file


def recorded_response(cassette: Cassette, ref: str) -> str:
    """Return the response recorded for a request.

    Raises:
        CassetteMissError: If the recording holds no exchange with that ref.
    """
    for exchange in cassette.exchanges:
        if exchange.ref == ref:
            return exchange.response
    message = (
        f"cassette miss: {cassette.case_id} has no recorded exchange for this request "
        "(the prompt, the model id or the input changed since it was recorded)"
    )
    raise CassetteMissError(message)
