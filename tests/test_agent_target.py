from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.evals.loader import load_case
from qrypt_quickstart.evals.models import CaseInput
from qrypt_quickstart.evals.target import run_target
from qrypt_quickstart.prompts import load_prompt

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
BRIEF_PROMPT: Final = "Generate an AES-256 key using Qrypt quantum entropy in a new project"


class CapturingClient:
    def __init__(self) -> None:
        self.system_prompts: list[str] = []
        self.user_messages: list[str] = []

    async def complete(self, *, system_prompt: str, user_message: str) -> str:
        self.system_prompts.append(system_prompt)
        self.user_messages.append(user_message)
        return "print('a program')"


async def test_a_case_with_a_document_gives_the_agent_the_rendered_page_and_the_prompt() -> None:
    client = CapturingClient()
    output = await run_target(CaseInput(prompt=BRIEF_PROMPT, document="site/index.html"), client)
    user_message = client.user_messages[0]
    snippet_line = 'api_key = os.environ.get("QRYPT_API_KEY", "").strip()'
    assert client.system_prompts == [load_prompt("agent").text]
    assert user_message.endswith(BRIEF_PROMPT)
    assert "<!-- include:" not in user_message
    assert snippet_line.replace('"', "&quot;") in user_message
    assert [prompt.name for prompt in output.prompts_used] == ["agent"]


async def test_a_case_without_a_document_still_uses_the_answer_prompt() -> None:
    client = CapturingClient()
    output = await run_target(CaseInput(prompt="What is 2 + 2?"), client)
    assert client.system_prompts == [load_prompt("answer").text]
    assert [prompt.name for prompt in output.prompts_used] == ["answer"]


def test_a_document_outside_site_is_refused() -> None:
    with pytest.raises(ValueError, match="site/"):
        CaseInput(prompt=BRIEF_PROMPT, document="../.ssh/id_rsa")


def test_the_agent_contract_case_names_the_brief_prompt_word_for_word() -> None:
    case = load_case(REPOSITORY_ROOT / "evals" / "pending" / "AC-01.yaml")
    assert case.input.prompt == BRIEF_PROMPT
    assert case.input.document == "site/index.html"


async def test_a_markdown_document_is_given_as_plain_text_with_the_snippets_filled_in() -> None:
    client = CapturingClient()
    await run_target(CaseInput(prompt=BRIEF_PROMPT, document="site/llms-full.md"), client)
    user_message = client.user_messages[0]
    assert 'api_key = os.environ.get("QRYPT_API_KEY", "").strip()' in user_message
    assert "<!-- include:" not in user_message
