"""The system under test: the one file a project replaces with its own.

`run_target` is what every eval case exercises. The version shipped with the kit is the smallest
thing that goes end to end: it sends one versioned prompt and the case's input to a model and
returns the reply. Replace its body with a call into the real system, and keep two things:

- every model call goes through `model_client`, so the gate can replay it from a recording;
- `prompts_used` names every prompt the answer depended on, so results carry prompt versions.
"""

from typing import Final

from ..prompts import load_prompt
from .clients import ModelClient
from .models import CaseInput, PromptVersion, TargetOutput

ANSWER_PROMPT_NAME: Final = "answer"
REFUSAL_PREFIXES: Final = ("i don't know", "i do not know", "i can't", "i cannot")


async def run_target(case_input: CaseInput, model_client: ModelClient) -> TargetOutput:
    """Run the system under test on one case's input.

    Args:
        case_input: The case's input.
        model_client: The client every model call must go through.

    Returns:
        The answer, whether it was a refusal, and the prompt versions it was produced with.
    """
    answer_prompt = load_prompt(ANSWER_PROMPT_NAME)
    response_text = await model_client.complete(
        system_prompt=answer_prompt.text, user_message=case_input.prompt
    )
    answer_text = response_text.strip()
    return TargetOutput(
        text=answer_text,
        refused=answer_text.lower().startswith(REFUSAL_PREFIXES),
        prompts_used=[
            PromptVersion(
                name=answer_prompt.name, version=answer_prompt.version, sha256=answer_prompt.sha256
            )
        ],
    )


def build_live_client(model: str) -> ModelClient:
    """Return a client that calls the real model, for `--mode record` and `--mode live`.

    The kit ships no provider SDK. Wire the project's provider in here and return an object with an
    async `complete(system_prompt=..., user_message=...)` method. Take the provider's key from
    `Settings().model_api_key`, which reads the `<MODULE>_MODEL_API_KEY` line of the `.env` at the
    repository root (`.env.example` names it), and from nowhere else. A live run costs money: say
    the estimate and get the owner's yes first.

    Args:
        model: The model id from `evals/thresholds.yaml`.

    Raises:
        NotImplementedError: Until a provider is wired in.
    """
    message = (
        f"no live model client is wired in for {model!r}; "
        "implement build_live_client in evals/target.py (see docs/guides/evals.md)"
    )
    raise NotImplementedError(message)
