"""The system under test: the quickstart's docs, as a model acting for a developer reads them.

A case that names a `document` plays the agent-readiness test in one turn (docs/PLAN.md): the
model gets the `agent` prompt, the page rendered as a developer sees it (`site_builder`), and the
case's prompt, and the program it writes is scored. Changing the page changes the request, so a
change to the docs needs the case recorded again, which is the point: the eval measures the docs.

A case with no `document` keeps the kit's `answer` prompt.

- every model call goes through `model_client`, so the gate can replay it from a recording;
- `prompts_used` names every prompt the answer depended on, so results carry prompt versions.
"""

from typing import Final

from ..config import REPOSITORY_ROOT
from ..prompts import load_prompt
from ..site_builder import render_page
from .clients import ModelClient
from .models import CaseInput, PromptVersion, TargetOutput

ANSWER_PROMPT_NAME: Final = "answer"
AGENT_PROMPT_NAME: Final = "agent"
REFUSAL_PREFIXES: Final = ("i don't know", "i do not know", "i can't", "i cannot")


def agent_user_message(document: str, task_prompt: str) -> str:
    """Return the page, rendered as a developer sees it, followed by the task.

    Args:
        document: The page's path under `site/`, from the repository's root.
        task_prompt: The case's prompt.

    Returns:
        The user message the model is sent.
    """
    rendered_page = render_page((REPOSITORY_ROOT / document).read_text())
    return f"Documentation page ({document}):\n\n{rendered_page}\n\nTask: {task_prompt}"


async def run_target(case_input: CaseInput, model_client: ModelClient) -> TargetOutput:
    """Run the system under test on one case's input.

    Args:
        case_input: The case's input.
        model_client: The client every model call must go through.

    Returns:
        The answer, whether it was a refusal, and the prompt versions it was produced with.
    """
    if case_input.document is None:
        system_prompt = load_prompt(ANSWER_PROMPT_NAME)
        user_message = case_input.prompt
    else:
        system_prompt = load_prompt(AGENT_PROMPT_NAME)
        user_message = agent_user_message(case_input.document, case_input.prompt)
    response_text = await model_client.complete(
        system_prompt=system_prompt.text, user_message=user_message
    )
    answer_text = response_text.strip()
    return TargetOutput(
        text=answer_text,
        refused=answer_text.lower().startswith(REFUSAL_PREFIXES),
        prompts_used=[
            PromptVersion(
                name=system_prompt.name, version=system_prompt.version, sha256=system_prompt.sha256
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
