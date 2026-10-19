"""The model clients a run can use: one that replays recordings and one that makes them."""

from typing import Protocol

from .cassette import Cassette, RecordedExchange, exchange_ref, recorded_response


class ModelClient(Protocol):
    """Anything that can answer a system prompt and a user message."""

    async def complete(self, *, system_prompt: str, user_message: str) -> str:
        """Return the model's reply."""
        ...


class ReplayClient:
    """Answers from a case's recording. It never touches the network, so it never costs anything."""

    def __init__(self, cassette: Cassette) -> None:
        """Create a client that replays the given recording."""
        self._cassette = cassette

    async def complete(self, *, system_prompt: str, user_message: str) -> str:
        """Return the recorded reply to this exact request.

        Raises:
            CassetteMissError: If the request was never recorded.
        """
        request_ref = exchange_ref(
            case_id=self._cassette.case_id,
            model=self._cassette.model,
            system_prompt=system_prompt,
            user_message=user_message,
        )
        return recorded_response(self._cassette, request_ref)


class RecordingClient:
    """Passes each request to a live client and keeps the exchange for the case's recording."""

    def __init__(self, *, case_id: str, model: str, live_client: ModelClient) -> None:
        """Create a client that records what the live client answers for one case."""
        self._case_id = case_id
        self._model = model
        self._live_client = live_client
        self._exchanges: list[RecordedExchange] = []

    async def complete(self, *, system_prompt: str, user_message: str) -> str:
        """Ask the live client, remember the exchange, and return the reply."""
        response_text = await self._live_client.complete(
            system_prompt=system_prompt, user_message=user_message
        )
        request_ref = exchange_ref(
            case_id=self._case_id,
            model=self._model,
            system_prompt=system_prompt,
            user_message=user_message,
        )
        self._exchanges.append(RecordedExchange(ref=request_ref, response=response_text))
        return response_text

    def cassette(self) -> Cassette:
        """Return everything recorded so far, as the case's cassette."""
        return Cassette(case_id=self._case_id, model=self._model, exchanges=list(self._exchanges))
