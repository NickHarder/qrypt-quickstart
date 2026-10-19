#!/usr/bin/env python3
"""Before a pull request: what this branch changed, and what else may have to change with it.

    scripts/look_ahead.py [--base <ref>]

A change closes in one pull request when what describes the changed code goes with it: the
documents that name it, a test beside it, the handoff, the log. The gate holds part of that already
(a source that changed after its concept, the links, the index files). This reads the rest and
prints notes. A note is something to read and decide; it is never a failure.

From the merge-base of HEAD with the base (origin/main, then main, or --base), it takes every path
changed since, committed or not, and notes:

    a document of the current state (README.md, HANDOFF.md, AGENTS.md, every concept under docs/
    but a plan and the log) that names a changed file and is itself unchanged on the branch; one
    that lists the file as a source is left to the bundle check's drift note
    code changed with no test changed
    a make target added without a line in the Makefile's help header or in the AGENTS.md table
    HANDOFF.md unchanged, or describing this change as still to come
    docs/log.md unchanged

Exit 0 when it ran, notes or none. Exit 2 outside a git repository, or without a base to compare.
"""

from __future__ import annotations

import argparse
import posixpath
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

EXIT_RAN: Final = 0
EXIT_COULD_NOT_RUN: Final = 2
DEFAULT_BASES: Final = ("origin/main", "main")

# The documents that describe the current state, in a project and in the kit that makes one.
DOCUMENT_PATTERNS: Final = (
    "README.md",
    "HANDOFF.md",
    "AGENTS.md",
    "docs/**/*.md",
    "template/README.md.jinja",
    "template/HANDOFF.md.jinja",
    "template/AGENTS.md.jinja",
    "template/docs/**/*.md",
    "template/docs/**/*.md.jinja",
)
# Records of what was: they never change, so nothing is noted against them.
HISTORY_DOCUMENTS: Final = frozenset(
    {"docs/log.md", "docs/references/the-owners-reasons.md", "template/docs/log.md"}
)
HISTORY_TYPES: Final = frozenset({"Plan"})
INDEX_NAME: Final = "index.md"
TOP_DOCUMENTS: Final = frozenset({"README.md", "HANDOFF.md", "AGENTS.md"})
HANDOFF_NAME: Final = "HANDOFF.md"
LOG_NAME: Final = "docs/log.md"

# A changed file is looked for by its path, its path as a project has it, and its name, unless the
# name says nothing on its own.
GENERIC_BASENAMES: Final = frozenset(
    {
        "AGENTS.md",
        "HANDOFF.md",
        "Makefile",
        "README.md",
        "SKILL.md",
        "__init__.py",
        "conftest.py",
        "index.md",
        "package.json",
        "pyproject.toml",
        "settings.json",
    }
)
MINIMUM_BASENAME_LENGTH: Final = 6
LOCK_SUFFIXES: Final = (".lock", "lock.json")
CODE_SUFFIXES: Final = frozenset(
    {
        ".py",
        ".sh",
        ".zsh",
        ".yml",
        ".yaml",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".rb",
        ".cs",
        ".swift",
    }
)
TEST_DIRECTORY: Final = "tests"
# A test named as one, by each language's convention: `*.test.ts`, `*.spec.jsx`, `*_test.go`.
TEST_SUFFIXES: Final = (
    *(
        f"{marker}{suffix}"
        for marker in (".test", ".spec")
        for suffix in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
    ),
    "_test.go",
)

MAKEFILE_PAIRS: Final = (
    ("Makefile", "AGENTS.md"),
    ("template/Makefile.jinja", "template/AGENTS.md.jinja"),
)
MAKEFILE_NAMES: Final = ("Makefile", "template/Makefile.jinja")
ADDED_TARGET_PATTERN: Final = re.compile(r"^\+([a-z][a-z0-9-]*):(?!=)", re.MULTILINE)
REMOVED_TARGET_PATTERN: Final = re.compile(r"^-([a-z][a-z0-9-]*):(?!=)", re.MULTILINE)

FRONTMATTER_TYPE_PATTERN: Final = re.compile(r"^type:\s*(\S+)", re.MULTILINE)
SOURCE_RESOURCE_PATTERN: Final = re.compile(r"resource:\s*['\"]?([^'\"\s}]+)")
PENDING_PATTERN: Final = re.compile(
    r"once (?:its|this|the|that) pull request is merged"
    r"|after (?:its|this|the|that) merge\b"
    r"|when (?:it|this|that) (?:is|has been) merged"
    r"|will be (?:made|tagged|pushed|merged)"
    r"|is (?:yours|the owner's) to (?:push|tag)",
    re.IGNORECASE,
)


class CannotRunError(Exception):
    """The script cannot look ahead here; the message says why."""


@dataclass(frozen=True)
class Document:
    """A document of the current state: its path, its text, and the files it lists as sources."""

    path: str
    text: str
    sources: frozenset[str]


@dataclass(frozen=True)
class Branch:
    """What the branch changed, and against which base."""

    base_name: str
    base_commit: str
    changed: frozenset[str]


def run_git(directory: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run git in the directory and return what it did, whatever its exit code."""
    git_executable = shutil.which("git")
    if git_executable is None:
        raise CannotRunError("git is not installed")
    return subprocess.run(  # noqa: S603  fixed arguments, no shell, the executable is resolved
        [git_executable, "-C", str(directory), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def git_output(repository: Path, *arguments: str) -> str:
    """Return git's output for the arguments, or raise CannotRunError with git's own words."""
    done = run_git(repository, *arguments)
    if done.returncode != 0:
        raise CannotRunError(done.stderr.strip() or f"git {' '.join(arguments)} failed")
    return done.stdout


def repository_root() -> Path:
    """Return the root of the repository the working directory is in."""
    done = run_git(Path.cwd(), "rev-parse", "--show-toplevel")
    if done.returncode != 0:
        raise CannotRunError("not in a git repository")
    return Path(done.stdout.strip())


def base_of(repository: Path, requested: str | None) -> tuple[str, str]:
    """Return the base's name and the merge-base commit of HEAD with it."""
    candidates = (requested,) if requested else DEFAULT_BASES
    for candidate in candidates:
        done = run_git(repository, "merge-base", "HEAD", candidate)
        if done.returncode == 0:
            return candidate, done.stdout.strip()
    if requested:
        raise CannotRunError(f"the base `{requested}` is not a ref of this repository")
    raise CannotRunError(
        "no base to compare with: neither origin/main nor main is a ref here; give --base"
    )


def changed_since(repository: Path, base_commit: str) -> frozenset[str]:
    """Return every path changed since the base commit, committed, staged, unstaged or untracked."""
    tracked = git_output(repository, "diff", "--name-only", base_commit).splitlines()
    untracked = git_output(repository, "ls-files", "--others", "--exclude-standard").splitlines()
    return frozenset(path for path in [*tracked, *untracked] if path)


def read_if_there(path: Path) -> str:
    """Return the file's text, or "" when there is no such file."""
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def frontmatter_of(text: str) -> str:
    """Return the text between a document's opening and closing `---`, or "" without one."""
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    return text[4:end] if end != -1 else ""


def is_history(path: str, frontmatter: str) -> bool:
    """A record of what was: a plan, the log, the owner's reasons."""
    found = FRONTMATTER_TYPE_PATTERN.search(frontmatter)
    return path in HISTORY_DOCUMENTS or (found is not None and found.group(1) in HISTORY_TYPES)


def sources_of(path: str, frontmatter: str) -> frozenset[str]:
    """Return the files of this repository the frontmatter lists as sources, as repository paths."""
    bundle_root = path[: path.index("docs/") + len("docs")] if "docs/" in path else ""
    document_directory = str(PurePosixPath(path).parent)
    resolved = [
        posixpath.normpath(
            posixpath.join(bundle_root, resource.lstrip("/"))
            if resource.startswith("/")
            else posixpath.join(document_directory, resource)
        )
        for resource in SOURCE_RESOURCE_PATTERN.findall(frontmatter)
        if "://" not in resource
    ]
    return frozenset(found for found in resolved if not found.startswith(".."))


def current_state_documents(repository: Path) -> list[Document]:
    """Return every document that describes the current state, with what it lists as sources."""
    paths = sorted(
        {
            found.relative_to(repository).as_posix()
            for pattern in DOCUMENT_PATTERNS
            for found in repository.glob(pattern)
            if found.is_file()
        }
    )
    documents: list[Document] = []
    for path in paths:
        if PurePosixPath(path).name == INDEX_NAME:
            continue
        text = read_if_there(repository / path)
        frontmatter = frontmatter_of(text)
        if not is_history(path, frontmatter):
            documents.append(Document(path, text, sources_of(path, frontmatter)))
    return documents


def project_path_of(path: str) -> str:
    """Return the path as a project made from the kit has it: no `template/`, no `.jinja`."""
    return path.removeprefix("template/").removesuffix(".jinja")


def is_swept(path: str) -> bool:
    """A changed file worth looking for in the documents.

    Not a document, an index or a lock file; and not a Makefile, whose targets have a check of their
    own below, since every document that names the Makefile would be noted on every target added.
    """
    name = PurePosixPath(path).name
    if name == INDEX_NAME or name.endswith(LOCK_SUFFIXES) or path in MAKEFILE_NAMES:
        return False
    return (
        not path.startswith(("docs/", "template/docs/"))
        and project_path_of(path) not in TOP_DOCUMENTS
    )


def names_of(path: str) -> tuple[str, ...]:
    """Return what a document would call the file: its path, its project path, and its name."""
    project_path = project_path_of(path)
    name = PurePosixPath(path).name
    project_name = PurePosixPath(project_path).name
    distinctive = (
        "." in project_name
        and project_name not in GENERIC_BASENAMES
        and len(project_name) >= MINIMUM_BASENAME_LENGTH
    )
    return tuple(
        dict.fromkeys((path, project_path, *((name, project_name) if distinctive else ())))
    )


def mentions(text: str, name: str) -> bool:
    """Whether the text names the file: the name whole, not as part of a longer path or word."""
    return re.search(r"(?<![\w.-])" + re.escape(name) + r"(?![\w.-])", text) is not None


def document_notes(documents: list[Document], branch: Branch) -> list[str]:
    """A current-state document that names a changed file and did not change with it."""
    swept = [path for path in sorted(branch.changed) if is_swept(path)]
    return [
        f"note: {document.path} names `{changed_path}`, changed here,"
        " and is unchanged on this branch"
        for document in documents
        if document.path not in branch.changed
        for changed_path in swept
        if changed_path not in document.sources
        and any(mentions(document.text, name) for name in names_of(changed_path))
    ]


def is_test(path: str) -> bool:
    """A test file: under a tests folder, or named as one."""
    parts = PurePosixPath(path).parts
    return (
        TEST_DIRECTORY in parts[:-1]
        or parts[-1].startswith("test_")
        or parts[-1].endswith(TEST_SUFFIXES)
    )


def is_code(path: str) -> bool:
    """A code file, by its suffix as a project has it, and not a test."""
    return not is_test(path) and PurePosixPath(project_path_of(path)).suffix in CODE_SUFFIXES


def test_notes(branch: Branch) -> list[str]:
    """Code changed, and no test with it."""
    code = [path for path in branch.changed if is_code(path)]
    if code and not any(is_test(path) for path in branch.changed):
        return [
            f"note: {len(code)} code file(s) changed and no test changed:"
            " test first, and watch it fail"
        ]
    return []


def added_targets(repository: Path, branch: Branch, makefile: str) -> list[str]:
    """The make targets this branch added to the Makefile, in the order they appear."""
    if makefile not in branch.changed:
        return []
    diff = git_output(repository, "diff", branch.base_commit, "--", makefile)
    removed = set(REMOVED_TARGET_PATTERN.findall(diff))
    return [
        name for name in dict.fromkeys(ADDED_TARGET_PATTERN.findall(diff)) if name not in removed
    ]


def make_notes(repository: Path, branch: Branch) -> list[str]:
    """A make target added without its help-header line, or its row in the AGENTS.md table."""
    notes: list[str] = []
    for makefile, agents in MAKEFILE_PAIRS:
        makefile_text = read_if_there(repository / makefile)
        agents_text = read_if_there(repository / agents)
        for target in added_targets(repository, branch, makefile):
            if (
                re.search(rf"^#\s+make\s+{re.escape(target)}(?:\s|$)", makefile_text, re.MULTILINE)
                is None
            ):
                notes.append(f"note: {makefile}: the target `{target}` is not in the help header")
            if agents_text and f"`make {target}" not in agents_text:
                notes.append(f"note: {agents}: the commands table has no `make {target}`")
    return notes


def handoff_notes(repository: Path, branch: Branch) -> list[str]:
    """The handoff unchanged while the branch changed, or describing the change as still to come."""
    handoff_text = read_if_there(repository / HANDOFF_NAME)
    if not handoff_text:
        return []
    unchanged = (
        [f"note: {HANDOFF_NAME} is unchanged on this branch"]
        if branch.changed and HANDOFF_NAME not in branch.changed
        else []
    )
    pending = [
        f"note: {HANDOFF_NAME}:{number}: describes this change as still to come"
        f' ("{found.group(0)}");'
        " write it as it is true once merged"
        for number, line in enumerate(handoff_text.splitlines(), start=1)
        for found in [PENDING_PATTERN.search(line)]
        if found is not None
    ]
    return [*unchanged, *pending]


def log_notes(repository: Path, branch: Branch) -> list[str]:
    """The log unchanged while the branch changed something."""
    if (repository / LOG_NAME).is_file() and branch.changed and LOG_NAME not in branch.changed:
        return [f"note: {LOG_NAME} is unchanged on this branch"]
    return []


def main() -> int:
    """Print what changed and the notes, and say whether it ran."""
    parser = argparse.ArgumentParser(
        description="Before a pull request: what else may have to change."
    )
    parser.add_argument("--base", help="the ref to compare with (default: origin/main, then main)")
    arguments = parser.parse_args()
    try:
        repository = repository_root()
        base_name, base_commit = base_of(repository, arguments.base)
        branch = Branch(base_name, base_commit, changed_since(repository, base_commit))
        notes = [
            *document_notes(current_state_documents(repository), branch),
            *test_notes(branch),
            *make_notes(repository, branch),
            *handoff_notes(repository, branch),
            *log_notes(repository, branch),
        ]
    except CannotRunError as error:
        sys.stderr.write(f"look-ahead: {error}\n")
        return EXIT_COULD_NOT_RUN
    sys.stdout.write(
        f"look-ahead: {len(branch.changed)} path(s) changed since {base_commit[:7]} ({base_name})\n"
    )
    sys.stdout.write("".join(f"{note}\n" for note in notes))
    if notes:
        sys.stdout.write(
            f"look-ahead: {len(notes)} note(s);"
            " read each, change what should change, and say what holds\n"
        )
    else:
        sys.stdout.write("look-ahead: no notes\n")
    return EXIT_RAN


if __name__ == "__main__":
    sys.exit(main())
