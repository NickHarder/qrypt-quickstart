#!/usr/bin/env python3
"""Which files of this project the kit gave it, unchanged, and which are the project's own.

    scripts/kit_files.py [--json | --diff]      (make kit-files [JSON=1] [DIFF=1])

It renders the kit again into a temporary folder, at the version and with the answers that
`.copier-answers.yml` records (`copier recopy --vcs-ref=:current:`), and compares that render with
the files git tracks here. Each tracked file lands in one group:

    unchanged   a kit file as the kit wrote it: an audit skips it, since the kit's own tests and CI
                prove it at that version
    changed     a kit file the project edited: an audit reads the diff (`--diff` prints it)
    removed     a kit file the project deleted
    own         a file the kit did not write: an audit reads it whole

Nothing here is changed. The `audit-codebase` and `audit-security` skills read it first, so that
their areas read the project and not the scaffold.

Exit 0 when it ran. Exit 2 outside a git repository, without `.copier-answers.yml`, or in the kit
itself. Exit 3 when copier is not installed. Exit 4 when the kit could not be rendered (its source
cannot be reached, say): an audit then reads every file, and says so.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

EXIT_RAN: Final = 0
EXIT_NOT_A_PROJECT: Final = 2
EXIT_NO_COPIER: Final = 3
EXIT_RENDER_FAILED: Final = 4

ANSWERS_FILE: Final = ".copier-answers.yml"
GATE_SCRIPT: Final = "scripts/gate.sh"
KIT_MARKERS: Final = ("copier.yml", "template")
ANSWER_LINE_PATTERN: Final = re.compile(
    r"^(?P<key>_commit|_src_path):\s*['\"]?(?P<value>.*?)['\"]?\s*$"
)
UNKNOWN_VERSION: Final = "the version it was rendered from"
COPIER_ERROR_LINES: Final = 3


class NotAProjectError(Exception):
    """There is nothing to sort here; the message says why."""


@dataclass(frozen=True)
class KitFiles:
    """The project's tracked files in their groups, and the kit version they were compared with."""

    kit_source: str
    kit_version: str
    unchanged: list[str]
    changed: list[str]
    removed: list[str]
    own: list[str]

    def as_json(self) -> str:
        """Return the groups as the JSON `--json` prints."""
        return json.dumps(
            {
                "kit": {"source": self.kit_source, "version": self.kit_version},
                "unchanged": self.unchanged,
                "changed": self.changed,
                "removed": self.removed,
                "own": self.own,
            },
            indent=2,
        )

    def summary(self) -> str:
        """Return the groups as the lines a person reads."""
        lines = [
            f"kit-files: compared with the kit at {self.kit_version} ({self.kit_source})",
            f"{len(self.unchanged)} unchanged kit files, which an audit skips",
        ]
        groups = (
            ("changed kit files, whose diff an audit reads (make kit-files DIFF=1):", self.changed),
            ("kit files the project removed:", self.removed),
            ("the project's own files, which an audit reads whole:", self.own),
        )
        for heading, paths in groups:
            lines.append(heading)
            lines.extend(f"  {path}" for path in paths or ["(none)"])
        return "\n".join(lines) + "\n"


def repository_root(directory: Path) -> Path:
    """Return the git repository the directory is in.

    Raises:
        NotAProjectError: Outside a git repository.
    """
    done = git(directory, "rev-parse", "--show-toplevel")
    if done.returncode != 0:
        message = f"{directory} is not a git repository"
        raise NotAProjectError(message)
    return Path(done.stdout.strip())


def git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run git in the repository and return what it did; never raises on a refusal.

    Raises:
        NotAProjectError: git is not installed.
    """
    git_executable = shutil.which("git")
    if git_executable is None:
        message = "git is not installed"
        raise NotAProjectError(message)
    return subprocess.run(  # noqa: S603  fixed arguments, no shell, the executable is resolved
        [git_executable, "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def recorded_answers(repository: Path) -> dict[str, str]:
    """Return the kit's source and commit as `.copier-answers.yml` records them.

    Raises:
        NotAProjectError: In the kit itself, or where no answers file records a source.
    """
    has_markers = all((repository / marker).exists() for marker in KIT_MARKERS)
    if has_markers and not (repository / GATE_SCRIPT).is_file():
        message = "this is the kit itself: it has no project files to sort from the kit's"
        raise NotAProjectError(message)
    answers_path = repository / ANSWERS_FILE
    if not answers_path.is_file():
        message = f"no {ANSWERS_FILE}: this repository was not made from the kit"
        raise NotAProjectError(message)
    matches = (
        ANSWER_LINE_PATTERN.match(line)
        for line in answers_path.read_text(encoding="utf-8").splitlines()
    )
    answers = {match["key"]: match["value"] for match in matches if match}
    if "_src_path" not in answers:
        message = f"{ANSWERS_FILE} names no _src_path, so the kit cannot be rendered again"
        raise NotAProjectError(message)
    return answers


def render_kit(
    copier_executable: str, repository: Path, render_folder: Path
) -> subprocess.CompletedProcess[str]:
    """Render the kit into the folder at the recorded version, with the recorded answers."""
    shutil.copyfile(repository / ANSWERS_FILE, render_folder / ANSWERS_FILE)
    return subprocess.run(  # noqa: S603  fixed arguments, no shell, the executable is resolved
        [
            copier_executable,
            "recopy",
            "--force",
            "--quiet",
            "--skip-tasks",
            "--vcs-ref=:current:",
            str(render_folder),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def tracked_files(repository: Path) -> list[str]:
    """Return every file git tracks here, as paths from the root, that is on disk."""
    listed = git(repository, "ls-files", "-z").stdout.split("\0")
    return sorted(path for path in listed if path and (repository / path).is_file())


def rendered_files(render_folder: Path) -> list[str]:
    """Return every file of the render, as paths from its root."""
    return sorted(
        path.relative_to(render_folder).as_posix()
        for path in render_folder.rglob("*")
        if path.is_file()
    )


def sort_files(repository: Path, render_folder: Path, answers: dict[str, str]) -> KitFiles:
    """Put each tracked file in its group by comparing it with the render."""
    tracked = tracked_files(repository)
    kit_paths = set(rendered_files(render_folder))
    in_both = [path for path in tracked if path in kit_paths]
    unchanged = [
        path
        for path in in_both
        if (repository / path).read_bytes() == (render_folder / path).read_bytes()
    ]
    return KitFiles(
        kit_source=answers["_src_path"],
        kit_version=answers.get("_commit", UNKNOWN_VERSION),
        unchanged=unchanged,
        changed=[path for path in in_both if path not in set(unchanged)],
        removed=sorted(kit_paths - set(tracked)),
        own=[path for path in tracked if path not in kit_paths],
    )


def diff_of(repository: Path, render_folder: Path, path: str) -> str:
    """Return the unified diff from the kit's text of a file to the project's."""
    kit_lines = (
        (render_folder / path)
        .read_text(encoding="utf-8", errors="replace")
        .splitlines(keepends=True)
    )
    project_lines = (
        (repository / path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    )
    return "".join(
        difflib.unified_diff(
            kit_lines, project_lines, fromfile=f"kit/{path}", tofile=f"project/{path}"
        )
    )


def main() -> int:
    """Print the project's files in their groups, or the diffs of the kit files it changed."""
    parser = argparse.ArgumentParser(
        description="Which files the kit gave this project, and which are its own."
    )
    output_choice = parser.add_mutually_exclusive_group()
    output_choice.add_argument("--json", action="store_true", help="print the groups as JSON")
    output_choice.add_argument(
        "--diff", action="store_true", help="print the diff of each changed kit file"
    )
    arguments = parser.parse_args()
    try:
        repository = repository_root(Path.cwd())
        answers = recorded_answers(repository)
    except NotAProjectError as error:
        sys.stderr.write(f"kit-files: {error}\n")
        return EXIT_NOT_A_PROJECT
    copier_executable = shutil.which("copier")
    if copier_executable is None:
        sys.stderr.write(
            "kit-files: copier is not installed. Install it with:  uv tool install copier\n"
        )
        return EXIT_NO_COPIER
    with tempfile.TemporaryDirectory(prefix="kit-files-") as temporary_folder:
        render_folder = Path(temporary_folder)
        rendered = render_kit(copier_executable, repository, render_folder)
        if rendered.returncode != 0:
            copier_lines = (rendered.stdout + rendered.stderr).strip().splitlines()
            sys.stderr.write("".join(f"{line}\n" for line in copier_lines[-COPIER_ERROR_LINES:]))
            sys.stderr.write(
                f"kit-files: could not render the kit from {answers['_src_path']}:"
                " an audit must audit every file, and say why\n"
            )
            return EXIT_RENDER_FAILED
        kit_files = sort_files(repository, render_folder, answers)
        if arguments.diff:
            sys.stdout.write(
                "".join(diff_of(repository, render_folder, path) for path in kit_files.changed)
            )
        elif arguments.json:
            sys.stdout.write(kit_files.as_json() + "\n")
        else:
            sys.stdout.write(kit_files.summary())
    return EXIT_RAN


if __name__ == "__main__":
    sys.exit(main())
