from typing import Final

from qrypt_quickstart.config import REPOSITORY_ROOT
from qrypt_quickstart.evals.baseline import (
    load_prompt_manifest,
    manifest_from,
    unbumped_prompts,
)
from qrypt_quickstart.evals.paths import eval_paths
from qrypt_quickstart.prompts import all_prompts

PROMPT_MANIFEST_FILE: Final = eval_paths(REPOSITORY_ROOT).prompt_manifest_file


def test_there_is_at_least_one_prompt() -> None:
    assert all_prompts()


def test_a_prompt_whose_text_changed_has_a_new_version() -> None:
    unbumped_prompt_names = unbumped_prompts(
        load_prompt_manifest(PROMPT_MANIFEST_FILE), all_prompts()
    )
    assert not unbumped_prompt_names, (
        f"prompt text changed without a version bump: {unbumped_prompt_names}. "
        "Raise metadata.version in the prompt file, then run `make prompt-manifest`."
    )


def test_the_prompt_manifest_is_current() -> None:
    assert load_prompt_manifest(PROMPT_MANIFEST_FILE) == manifest_from(all_prompts()), (
        "evals/prompt_manifest.json is out of date; run `make prompt-manifest` and commit it"
    )
