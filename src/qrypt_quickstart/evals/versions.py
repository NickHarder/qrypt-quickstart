"""What was under test: the kit version, the commit, each skill's version and each prompt's.

These go at the top of every result file, so a pass or a failure can always be traced to the exact
instructions and prompts that produced it.
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Final

import yaml

from ..prompts import Prompt
from .models import PromptVersion, Versions

UNKNOWN: Final = "unknown"
FRONTMATTER_PATTERN: Final = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def skill_versions(repository_root: Path) -> dict[str, str]:
    """Return each skill's metadata.version by skill name; empty if the project has no skills."""
    skills_directory = repository_root / ".claude" / "skills"
    if not skills_directory.is_dir():
        return {}
    versions_by_skill: dict[str, str] = {}
    for skill_file in sorted(skills_directory.glob("*/SKILL.md")):
        frontmatter_match = FRONTMATTER_PATTERN.match(skill_file.read_text(encoding="utf-8"))
        frontmatter: object = (
            yaml.safe_load(frontmatter_match.group(1)) if frontmatter_match else None
        )
        metadata: object = frontmatter.get("metadata") if isinstance(frontmatter, dict) else None
        declared_version: object = metadata.get("version") if isinstance(metadata, dict) else None
        versions_by_skill[skill_file.parent.name] = (
            str(declared_version) if declared_version is not None else UNKNOWN
        )
    return versions_by_skill


def kit_version(repository_root: Path) -> str:
    """Return the kit version this project was rendered from, as recorded by Copier."""
    answers_file = repository_root / ".copier-answers.yml"
    if not answers_file.exists():
        return UNKNOWN
    answers: object = yaml.safe_load(answers_file.read_text(encoding="utf-8"))
    recorded_commit: object = answers.get("_commit") if isinstance(answers, dict) else None
    return str(recorded_commit) if recorded_commit is not None else UNKNOWN


def git_commit(repository_root: Path) -> str:
    """Return the short hash of the checked-out commit, or "unknown" outside a repository."""
    git_executable = shutil.which("git")
    if git_executable is None:
        return UNKNOWN
    completed = subprocess.run(  # noqa: S603  fixed arguments, no shell, the executable is resolved
        [git_executable, "-C", str(repository_root), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else UNKNOWN


def collect_versions(repository_root: Path, prompts: list[Prompt]) -> Versions:
    """Gather everything that names what was under test."""
    return Versions(
        kit=kit_version(repository_root),
        git_commit=git_commit(repository_root),
        skills=skill_versions(repository_root),
        prompts=[
            PromptVersion(name=prompt.name, version=prompt.version, sha256=prompt.sha256)
            for prompt in prompts
        ],
    )
