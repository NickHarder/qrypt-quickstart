"""The prompts this project sends to a model, each with a name and a version.

A prompt is a Markdown file in this package, with frontmatter:

    ---
    name: answer
    metadata:
      version: "1.0.0"
    ---
    The prompt text.

A version names one exact text: `tests/test_prompts_versioned.py` fails when a prompt's text
changes and its version does not. Eval results record the version and the content hash of every
prompt a case used, so a pass or a failure is always tied to a prompt version.
"""

import hashlib
import re
from importlib import resources
from typing import Final

import yaml
from pydantic import BaseModel, ConfigDict

FRONTMATTER_PATTERN: Final = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
VERSION_PATTERN: Final = re.compile(r"\d+\.\d+\.\d+")
PROMPT_FILE_SUFFIX: Final = ".md"


class PromptFormatError(ValueError):
    """A prompt file is missing its frontmatter, its name or its version."""


class PromptMetadata(BaseModel):
    """The `metadata` block of a prompt's frontmatter."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str


class PromptFrontmatter(BaseModel):
    """The frontmatter of a prompt file."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: str | None = None
    metadata: PromptMetadata


class Prompt(BaseModel):
    """One prompt: its text, the version that names that text, and the text's SHA-256."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    version: str
    text: str
    sha256: str


def parse_prompt(file_name: str, file_text: str) -> Prompt:
    """Parse one prompt file.

    Args:
        file_name: The file's name, used to check the declared name and in error messages.
        file_text: The file's whole content.

    Returns:
        The prompt, with its text stripped of surrounding blank lines.

    Raises:
        PromptFormatError: If the frontmatter is missing or does not match the file.
    """
    frontmatter_match = FRONTMATTER_PATTERN.match(file_text)
    if frontmatter_match is None:
        message = f"{file_name}: a prompt file starts with frontmatter between two --- lines"
        raise PromptFormatError(message)
    frontmatter = PromptFrontmatter.model_validate(yaml.safe_load(frontmatter_match.group(1)))
    expected_name = file_name.removesuffix(PROMPT_FILE_SUFFIX)
    if frontmatter.name != expected_name:
        message = f"{file_name}: name is {frontmatter.name!r} but the file is {expected_name!r}"
        raise PromptFormatError(message)
    if VERSION_PATTERN.fullmatch(frontmatter.metadata.version) is None:
        message = f"{file_name}: metadata.version must be MAJOR.MINOR.PATCH"
        raise PromptFormatError(message)
    prompt_text = frontmatter_match.group(2).strip()
    return Prompt(
        name=frontmatter.name,
        version=frontmatter.metadata.version,
        text=prompt_text,
        sha256=hashlib.sha256(prompt_text.encode()).hexdigest(),
    )


def all_prompts() -> list[Prompt]:
    """Return every prompt in this package, ordered by name."""
    prompt_files = sorted(
        (
            package_entry
            for package_entry in resources.files(__name__).iterdir()
            if package_entry.name.endswith(PROMPT_FILE_SUFFIX)
        ),
        key=lambda package_entry: package_entry.name,
    )
    return [
        parse_prompt(prompt_file.name, prompt_file.read_text(encoding="utf-8"))
        for prompt_file in prompt_files
    ]


def load_prompt(name: str) -> Prompt:
    """Return the prompt with the given name.

    Raises:
        KeyError: If no prompt has that name.
    """
    for prompt in all_prompts():
        if prompt.name == name:
            return prompt
    raise KeyError(name)
