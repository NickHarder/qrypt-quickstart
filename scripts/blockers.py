#!/usr/bin/env python3
"""What blocks this project now, and where its plan will need the owner.

    scripts/blockers.py [--no-gate] [--plan <file>]      (make blockers)

It reads what is already there and says, for each thing that holds the work up, who unblocks it
and how. Nothing is changed, run, approved or pushed.

    now     the gate (red, or the machine not set up); work not committed, and commits not pushed;
            the gate ladder (docs/METHOD.md, with scripts/kit.conf): the next gate, a document
            before it not committed, and what the hook before a skill call would answer for it;
            documents changed since their approval; deliverables marked `Owner to do`; the
            handoff's "Open, for the owner"
    ahead   each `**You act:** <what> (<kind>)` line of docs/PLAN.md, or of the plan --plan names

Each line starts with its kind: `blocked:` (the work cannot go on), `waits:` (it waits on the
owner), `next:` (what comes next and may start), `ahead:` (where the plan will need the owner).
The `blockers` skill reads this, then walks the plan for the points no line marks.

In the kit that makes projects, it skips the gate and the ladder, which a kit does not have.

Exit 0 when it ran, whatever it found: a blocker is something to read, never a red run. Exit 2
outside a git repository.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import skill_costs

EXIT_RAN: Final = 0
EXIT_COULD_NOT_RUN: Final = 2
GATE_NOT_SET_UP: Final = 3

GATE_SCRIPT: Final = "scripts/gate.sh"
BUNDLE_SCRIPTS: Final = ("scripts/okf_bundle.py", "template/scripts/okf_bundle.py")
KIT_MARKERS: Final = ("copier.yml", "template")
PLAN: Final = "docs/PLAN.md"
DELIVERABLES: Final = "docs/DELIVERABLES.md"
HANDOFF: Final = "HANDOFF.md"
DOCS: Final = "docs"
KICKOFF: Final = "kickoff"
OWNER_TO_DO: Final = "Owner to do"
OPEN_HEADING: Final = "## Open, for the owner"
YOU_ACT_PATTERN: Final = re.compile(r"\*\*You act:\*\*\s*(.+?)\s*$")
GATE_RED_PATTERN: Final = re.compile(r"(?:GATE RED|PUSH BLOCKED): ([^=]+?)\s*=")
OPEN_ITEM_PATTERN: Final = re.compile(r"^- (?:\*\*(.+?)\*\*.*|(.+))$")
CHANGED_SINCE_APPROVAL: Final = "changed since the approval"
OWNER: Final = "the owner"
AGENT: Final = "the agent"


class CannotRunError(Exception):
    """The script cannot look here; the message says why."""


@dataclass(frozen=True)
class Item:
    """One thing that holds the work up or lies ahead: its kind, what, who, and how to clear it."""

    kind: str
    what: str
    who: str = ""
    how: str = ""

    def line(self) -> str:
        """Return the item as the line the script prints."""
        unblocks = f". Unblocks it: {self.who}, {self.how}" if self.who else ""
        return f"{self.kind}: {self.what}{unblocks}"


def git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run git in the repository and return what it did; never raises on a refusal."""
    git_executable = shutil.which("git")
    if git_executable is None:
        message = "git is not installed"
        raise CannotRunError(message)
    return subprocess.run(  # noqa: S603  fixed arguments, no shell, the executable is resolved
        [git_executable, "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def repository_root(directory: Path) -> Path:
    """Return the repository the directory is in.

    Raises:
        CannotRunError: Outside a git repository.
    """
    done = git(directory, "rev-parse", "--show-toplevel")
    if done.returncode != 0:
        message = f"{directory} is not a git repository"
        raise CannotRunError(message)
    return Path(done.stdout.strip())


def is_kit(repository: Path) -> bool:
    """Say whether this is the kit that makes projects: it has no gate and no ladder of its own."""
    has_markers = all((repository / marker).exists() for marker in KIT_MARKERS)
    return has_markers and not (repository / GATE_SCRIPT).is_file()


def read_if_there(path: Path) -> str:
    """Return a file's text, or nothing when there is no such file."""
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def gate_items(repository: Path) -> list[Item]:
    """Run the gate: red groups are the agent's to fix; a machine not set up, as the gate says."""
    done = subprocess.run(  # noqa: S603  the project's own gate script, no shell
        [str(repository / GATE_SCRIPT)],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    printed = done.stdout + done.stderr
    if done.returncode == 0:
        return []
    if done.returncode == GATE_NOT_SET_UP:
        reason_lines = [line for line in done.stderr.splitlines() if line.strip()]
        reason = reason_lines[-1] if reason_lines else "exit 3"
        return [
            Item(
                "blocked",
                f"the gate cannot run on this machine ({reason})",
                AGENT,
                "with `make bootstrap`; `make tools` installs, which on the owner's machine is "
                "the owner's to allow",
            )
        ]
    red = GATE_RED_PATTERN.search(printed)
    groups = red.group(1).strip() if red else f"exit {done.returncode}"
    return [
        Item("blocked", f"the gate is red: {groups}", AGENT, "by fixing what `make gate` prints")
    ]


def git_items(repository: Path) -> list[Item]:
    """Work not committed is the agent's; a commit on no remote branch waits on a push."""
    items: list[Item] = []
    changed = [
        line for line in git(repository, "status", "--porcelain").stdout.splitlines() if line
    ]
    if changed:
        items.append(
            Item("blocked", f"{len(changed)} file(s) not committed", AGENT, "by committing them")
        )
    upstream = git(repository, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if upstream.returncode == 0:
        upstream_name = upstream.stdout.strip()
        ahead = git(repository, "rev-list", "--count", f"{upstream_name}..HEAD").stdout.strip()
        if ahead.isdigit() and int(ahead) > 0:
            items.append(
                Item(
                    "blocked",
                    f"{ahead} commit(s) not pushed to {upstream_name}",
                    OWNER,
                    "with a push, or a yes to the agent's",
                )
            )
    elif git(repository, "remote").stdout.strip() and not is_on_a_remote_branch(repository):
        branch = git(repository, "branch", "--show-current").stdout.strip()
        unpushed = f"the branch {branch}" if branch else "a commit on no branch"
        items.append(
            Item(
                "blocked",
                f"{unpushed} has never been pushed",
                OWNER,
                "with a push, or a yes to the agent's",
            )
        )
    return items


def is_on_a_remote_branch(repository: Path) -> bool:
    """Say whether a remote branch holds HEAD's commit: pushed, though no upstream is set."""
    return bool(git(repository, "branch", "--remotes", "--contains", "HEAD").stdout.strip())


def is_committed(repository: Path, relative: str) -> bool:
    """Say whether git tracks the file as it is: committed, with no change since."""
    tracked = git(repository, "ls-files", "--error-unmatch", relative).returncode == 0
    clean = not git(repository, "status", "--porcelain", "--", relative).stdout.strip()
    return tracked and clean


def ladder_items(repository: Path, projects_folder: Path) -> list[Item]:
    """The ladder: the next gate, a document before it not committed, what the hook would say."""
    conf = skill_costs.read_conf(repository / skill_costs.KIT_CONF)
    ladder = [(KICKOFF, PLAN), *skill_costs.artifacts_of(conf).items()]
    missing = [
        (skill, document) for skill, document in ladder if not (repository / document).is_file()
    ]
    if not missing:
        return []
    skill, document = missing[0]
    if skill == KICKOFF:
        return [Item("blocked", f"no {PLAN}", OWNER, "by calling `kickoff` with the brief")]
    previous = ladder[ladder.index((skill, document)) - 1][1]
    if not is_committed(repository, previous):
        return [
            Item(
                "blocked",
                f"{previous} is not committed, and {skill} reads what is",
                AGENT,
                f"by committing {previous}",
            )
        ]
    decided = skill_costs.decision_for(repository, projects_folder, skill)
    if decided is None:
        return [Item("next", f"{skill}, which writes {document}")]
    answer, reason, _ = decided
    if answer == skill_costs.ASK:
        return [
            Item(
                "waits",
                f"{skill} would ask first: {reason}",
                OWNER,
                "by saying yes, or by setting the cap in scripts/kit.conf",
            )
        ]
    return [Item("next", f"{skill}, which writes {document}, may start on its own: {reason}")]


def approval_items(repository: Path) -> list[Item]:
    """Documents changed since the owner approved them: each waits for the owner again."""
    bundle_scripts = [repository / name for name in BUNDLE_SCRIPTS if (repository / name).is_file()]
    if not bundle_scripts or not (repository / DOCS).is_dir():
        return []
    done = subprocess.run(  # noqa: S603  the project's own bundle script, no shell
        [str(bundle_scripts[0]), "status", DOCS],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    changed = [
        line.split()[0] for line in done.stdout.splitlines() if CHANGED_SINCE_APPROVAL in line
    ]
    return [
        Item(
            "waits",
            f"{path} changed since its approval",
            OWNER,
            f"by reading it and `make docs-approve DOC={path}`, or `make docs-reopen`",
        )
        for path in changed
    ]


def deliverable_items(repository: Path) -> list[Item]:
    """Rows of docs/DELIVERABLES.md whose status is `Owner to do`."""
    rows = [
        line
        for line in read_if_there(repository / DELIVERABLES).splitlines()
        if OWNER_TO_DO in line
    ]
    names = [cells[1].strip() for cells in (row.split("|") for row in rows) if len(cells) > 1]
    return [
        Item("waits", f"a deliverable marked {OWNER_TO_DO}: {name}", OWNER, "as its row says")
        for name in names
    ]


def handoff_items(repository: Path) -> list[Item]:
    """The handoff's "Open, for the owner": each item by its bold lead, or its whole line."""
    lines = read_if_there(repository / HANDOFF).splitlines()
    if OPEN_HEADING not in lines:
        return []
    section = lines[lines.index(OPEN_HEADING) + 1 :]
    end = next(
        (index for index, line in enumerate(section) if line.startswith("## ")), len(section)
    )
    found = [OPEN_ITEM_PATTERN.match(line) for line in section[:end]]
    leads = [(match.group(1) or match.group(2)).strip() for match in found if match is not None]
    return [Item("waits", f"open for the owner in {HANDOFF}: {lead}") for lead in leads]


def ahead_items(repository: Path, plan: Path | None) -> list[Item]:
    """Each `**You act:**` line of the plan: where it will need the owner."""
    plan_path = plan if plan is not None else repository / PLAN
    shown = str(plan) if plan is not None else PLAN
    return [
        Item("ahead", f"{shown}:{number}: {found.group(1)}")
        for number, line in enumerate(read_if_there(plan_path).splitlines(), start=1)
        for found in [YOU_ACT_PATTERN.search(line)]
        if found is not None
    ]


def main() -> int:
    """Print what blocks the work now and what lies ahead, and say whether it ran."""
    parser = argparse.ArgumentParser(description="What blocks this project now, and ahead.")
    parser.add_argument("--no-gate", action="store_true", help="skip the gate, which takes seconds")
    parser.add_argument(
        "--plan", type=Path, help="the plan to read ahead in (default: docs/PLAN.md)"
    )
    arguments = parser.parse_args()
    config_home = Path(
        os.environ.get(skill_costs.CONFIG_DIR_VARIABLE) or skill_costs.DEFAULT_CONFIG_DIR
    ).expanduser()
    try:
        repository = repository_root(Path.cwd())
        kit = is_kit(repository)
        gate = [] if kit or arguments.no_gate else gate_items(repository)
        ladder = [] if kit else ladder_items(repository, config_home / skill_costs.PROJECTS_FOLDER)
        now = [
            *gate,
            *git_items(repository),
            *ladder,
            *approval_items(repository),
            *deliverable_items(repository),
            *handoff_items(repository),
        ]
        ahead = ahead_items(repository, arguments.plan)
    except CannotRunError as error:
        sys.stderr.write(f"blockers: {error}\n")
        return EXIT_COULD_NOT_RUN
    if kit:
        sys.stdout.write("blockers: the kit: no gate and no gate ladder here\n")
    sys.stdout.write("blockers: now\n")
    sys.stdout.write("".join(f"{item.line()}\n" for item in now))
    sys.stdout.write("blockers: ahead\n")
    sys.stdout.write("".join(f"{item.line()}\n" for item in ahead))
    counts = {
        kind: sum(1 for item in [*now, *ahead] if item.kind == kind)
        for kind in ("blocked", "waits", "ahead")
    }
    sys.stdout.write(
        f"blockers: {counts['blocked']} blocked, {counts['waits']} waiting on the owner,"
        f" {counts['ahead']} marked ahead\n"
    )
    return EXIT_RAN


if __name__ == "__main__":
    sys.exit(main())
