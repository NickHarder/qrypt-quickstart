#!/usr/bin/env python3
"""What a skill cost before, from the transcripts on this machine and the project's ledger.

    scripts/skill_costs.py report [--json] [<skill>]
    scripts/skill_costs.py append
    scripts/skill_costs.py hook

Claude Code writes each session's transcript under its config directory (`~/.claude`, or
`CLAUDE_CONFIG_DIR`), one folder per project, with every API response's tokens, and a sub-agent's
transcript beside it. A skill run is the stretch from the record Claude Code adds when the skill
is invoked (its base directory, then its text) to the owner's next prompt or the next skill's
marker, with the sub-agents spawned in it. A skill forked into a sub-agent of its own leaves no
marker in the session's transcript: the sub-agent's transcript starts with it, and holds the run.
A response is recorded once per content block, and counted once. A sub-agent's transcript writes
a response's usage before the response ends, so its output tokens read as a handful: a response
whose content is more than four times its recorded output tokens is counted from the content
instead, at four characters a token, and the run is marked approximate. A skill typed as
`/skill` is counted exactly; one the model invokes in the middle of a turn is counted to the end
of that turn, with what followed it.

`report` reads every project's transcripts and this project's ledger and prints, per skill: its
runs, how many of them are approximate, the median and the largest output tokens, the median
tokens read (the input, cached or not,
summed over the run's turns), the median turns and sub-agents, the models, the last run. With a
skill's name, it prints the estimate: the median of its history, or the floor (the skill's own
text, at four characters a token) with the words "no history" when there is none.

`append` writes this project's runs to the ledger, `.claude/skill-costs.jsonl`, each once, so the
history survives the transcripts (kept thirty days, and not at all in a cloud container) and
follows the project. Tokens, not dollars: prices move, and a subscription has no per-run price.

`hook` is what Claude Code runs before a skill call (`PreToolUse` on the `Skill` tool, from
`.claude/settings.json`): for a skill `scripts/kit.conf` names in `CAPPED_SKILLS`, it answers
allow for a first run (no history: nothing to hold it to, and the run sets the estimate) and for
one whose estimate is not over `SKILL_RUN_CAP_TOKENS`; it answers ask for a second run of a gate
(the artifact `GATE_ARTIFACTS` names for the skill exists), over the cap, or with no cap, with
the number as the reason. For any other skill or tool it says nothing. A skill the owner types
as `/skill` does not pass through it.

The transcript's format is Claude Code's own and may change: a record that cannot be read is
counted and said on stderr, never guessed at. Exit 0 when it ran; 2 when nothing could be read,
except from the hook, which never blocks a call: it exits 0 and leaves the decision to the
permission settings, and when its own check fails it asks, naming the error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

EXIT_RAN: Final = 0
EXIT_NOTHING_READABLE: Final = 2
CONFIG_DIR_VARIABLE: Final = "CLAUDE_CONFIG_DIR"
DEFAULT_CONFIG_DIR: Final = "~/.claude"
PROJECTS_FOLDER: Final = "projects"
TRANSCRIPT_SUFFIX: Final = ".jsonl"
SUBAGENTS_FOLDER: Final = "subagents"
META_SUFFIX: Final = ".meta.json"
LEDGER: Final = ".claude/skill-costs.jsonl"
# Where a skill's text is: in a project, and in the kit that makes one.
SKILL_FOLDERS: Final = (".claude/skills", "template/.claude/skills")
SKILL_FILE: Final = "SKILL.md"
MARKER_PREFIX: Final = "Base directory for this skill: "
CHARACTERS_A_TOKEN: Final = 4
# A response whose content is more than this many times its recorded output tokens had its usage
# written before the response ended; its content is then the count, and the run is approximate.
CONTENT_OVER_USAGE: Final = 4
EXACT: Final = "exact"
APPROXIMATE: Final = "approximate"
PRODUCER: Final = "claude-code"
NO_SESSION: Final = ""
VERSION_PATTERN: Final = re.compile(r"^\s*version:\s*[\"']?(\d+\.\d+\.\d+)", re.MULTILINE)
KIT_CONF: Final = "scripts/kit.conf"
CAP_KEY: Final = "SKILL_RUN_CAP_TOKENS"
CAPPED_KEY: Final = "CAPPED_SKILLS"
ARTIFACTS_KEY: Final = "GATE_ARTIFACTS"
SKILL_TOOL: Final = "Skill"
HOOK_EVENT: Final = "PreToolUse"
ALLOW: Final = "allow"
ASK: Final = "ask"


@dataclass(frozen=True)
class Marker:
    """The record Claude Code adds when a skill is invoked: where a run starts."""

    skill: str
    uuid: str
    date: str
    version: str


@dataclass(frozen=True)
class Prompt:
    """The owner's own prompt: where a run ends."""


@dataclass(frozen=True)
class Turn:
    """One API response: its tokens as recorded and as its content measures them; its tool calls."""

    message_id: str
    model: str
    output_tokens: int
    content_tokens: int
    tokens_read: int
    tool_use_ids: tuple[str, ...]

    @property
    def approximate(self) -> bool:
        """Say whether the usage was written before the response ended: the content outweighs it."""
        return self.output_tokens * CONTENT_OVER_USAGE < self.content_tokens

    @property
    def counted_output_tokens(self) -> int:
        """Return the output tokens to count: as recorded, or from the content when that is all."""
        return self.content_tokens if self.approximate else self.output_tokens


@dataclass(frozen=True)
class Unreadable:
    """A line that is not a JSON object: counted, never guessed at."""


@dataclass(frozen=True)
class SubAgent:
    """A sub-agent's transcript: the tool call that spawned it, and its turns."""

    tool_use_id: str
    turns: tuple[Turn, ...]


@dataclass(frozen=True)
class ForkedSkill:
    """A forked skill's own sub-agent: its transcript opens with the marker and is the run."""

    events: tuple[Marker | Turn, ...]


@dataclass(frozen=True)
class Run:
    """One run of a skill: what it spent from its marker to the next prompt, and how it was counted.

    The sub-agents the run spawned are included; the counting is exact, or approximate where a
    sub-agent's usage was written before its response ended and its content was counted instead.
    """

    skill: str
    session: str
    marker: str
    date: str
    producer: str
    output_tokens: int
    tokens_read: int
    turns: int
    sub_agents: int
    models: tuple[str, ...]
    counting: str


@dataclass(frozen=True)
class Reading:
    """What was read: the runs found, how many records were read, how many could not be."""

    runs: tuple[Run, ...]
    readable: int
    unreadable: int


@dataclass(frozen=True)
class Summary:
    """A skill's history in numbers, and the floor its text sets."""

    skill: str
    runs: int
    approximate_runs: int
    median_output_tokens: int
    largest_output_tokens: int
    median_tokens_read: int
    median_turns: int
    median_sub_agents: int
    models: tuple[str, ...]
    last_run: str
    floor_tokens: int | None


def nested(value: object, keys: tuple[str, ...]) -> object:
    """Return what is under the keys, each inside the last, or None where the path ends early."""
    if not keys:
        return value
    if not isinstance(value, dict):
        return None
    return nested(value.get(keys[0]), keys[1:])


def as_count(value: object) -> int:
    """Return a token count as recorded, or 0 when the record has none."""
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def as_text(value: object) -> str:
    """Return a string field as recorded, or an empty string when the record has none."""
    return value if isinstance(value, str) else ""


def blocks_of(record: dict[str, object]) -> list[dict[str, object]]:
    """Return the content blocks of a record's message; a plain string is one text block."""
    content = nested(record, ("message", "content"))
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def skill_of(base_directory: str) -> str:
    """Return the skill a base directory names: its last part, whichever way the slashes go."""
    return base_directory.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]


def marker_of(record: dict[str, object]) -> Marker | None:
    """Return the marker a record is, when Claude Code added it to invoke a skill."""
    if record.get("type") != "user" or record.get("isMeta") is not True:
        return None
    blocks = blocks_of(record)
    text = as_text(blocks[0].get("text")) if blocks else ""
    if not text.startswith(MARKER_PREFIX):
        return None
    base_directory = text[len(MARKER_PREFIX) :].split("\n", 1)[0].strip()
    skill = skill_of(base_directory)
    if not skill:
        return None
    return Marker(
        skill=skill,
        uuid=as_text(record.get("uuid")),
        date=as_text(record.get("timestamp"))[:10],
        version=as_text(record.get("version")),
    )


def is_prompt(record: dict[str, object]) -> bool:
    """Say whether a record is the owner's prompt: a user record, not a tool result, not added."""
    if record.get("type") != "user" or record.get("isMeta") is True:
        return False
    blocks = blocks_of(record)
    return bool(blocks) and all(block.get("type") != "tool_result" for block in blocks)


def content_characters(block: dict[str, object]) -> int:
    """Return the characters a content block holds: its text, or a tool call's input as JSON."""
    kind = block.get("type")
    if kind == "tool_use":
        return len(json.dumps(block.get("input")))
    if kind == "thinking":
        return len(as_text(block.get("thinking")))
    return len(as_text(block.get("text"))) if kind == "text" else 0


def turn_of(record: dict[str, object]) -> Turn | None:
    """Return the turn a record is: an assistant record with its response's id and usage."""
    if record.get("type") != "assistant":
        return None
    message_id = nested(record, ("message", "id"))
    usage = nested(record, ("message", "usage"))
    if not isinstance(message_id, str) or not isinstance(usage, dict):
        return None
    blocks = blocks_of(record)
    characters = sum(content_characters(block) for block in blocks)
    return Turn(
        message_id=message_id,
        model=as_text(nested(record, ("message", "model"))),
        output_tokens=as_count(usage.get("output_tokens")),
        content_tokens=-(-characters // CHARACTERS_A_TOKEN),
        tokens_read=(
            as_count(usage.get("input_tokens"))
            + as_count(usage.get("cache_read_input_tokens"))
            + as_count(usage.get("cache_creation_input_tokens"))
        ),
        tool_use_ids=tuple(
            as_text(block.get("id"))
            for block in blocks
            if block.get("type") == "tool_use" and as_text(block.get("id"))
        ),
    )


def classify(line: str) -> Marker | Prompt | Turn | Unreadable | None:
    """Return what a transcript line is to the count; None for a record that counts for nothing."""
    try:
        loaded: object = json.loads(line)
    except json.JSONDecodeError:
        return Unreadable()
    if not isinstance(loaded, dict):
        return Unreadable()
    marker = marker_of(loaded)
    if marker is not None:
        return marker
    if is_prompt(loaded):
        return Prompt()
    return turn_of(loaded)


def read_events(path: Path) -> tuple[list[Marker | Prompt | Turn], int, int]:
    """Return a transcript's events, how many records were read, and how many could not be."""
    with path.open(encoding="utf-8", errors="replace") as handle:
        outcomes = [classify(line) for line in handle if line.strip()]
    unreadable = sum(1 for outcome in outcomes if isinstance(outcome, Unreadable))
    events = [outcome for outcome in outcomes if isinstance(outcome, (Marker, Prompt, Turn))]
    return events, len(outcomes) - unreadable, unreadable


def as_one(message_id: str, records: Sequence[Turn]) -> Turn:
    """Return a response's records as one turn: the content adds up, the usage is the fullest."""
    return Turn(
        message_id=message_id,
        model=next((record.model for record in records if record.model), ""),
        output_tokens=max(record.output_tokens for record in records),
        content_tokens=sum(record.content_tokens for record in records),
        tokens_read=max(record.tokens_read for record in records),
        tool_use_ids=tuple(
            dict.fromkeys(identifier for record in records for identifier in record.tool_use_ids)
        ),
    )


def once_each(turns: Sequence[Turn]) -> list[Turn]:
    """Return the turns with each response once: it is recorded once per content block."""
    by_message: dict[str, list[Turn]] = {}
    for turn in turns:
        by_message.setdefault(turn.message_id, []).append(turn)
    return [as_one(message_id, records) for message_id, records in by_message.items()]


def read_sub_agent(meta_path: Path) -> tuple[SubAgent | ForkedSkill | None, int, int]:
    """Return what a meta file describes, with the records read and those not readable.

    It is a sub-agent a tool call spawned, or a skill forked into a sub-agent of its own, whose
    meta file names no tool call and whose transcript starts with the skill's marker.
    """
    try:
        loaded: object = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None, 0, 1
    tool_use_id = nested(loaded, ("toolUseId",))
    transcript = meta_path.with_name(meta_path.name[: -len(META_SUFFIX)] + TRANSCRIPT_SUFFIX)
    if not transcript.is_file():
        return (SubAgent(tool_use_id, ()), 1, 0) if isinstance(tool_use_id, str) else (None, 0, 1)
    events, readable, unreadable = read_events(transcript)
    if isinstance(tool_use_id, str):
        turns = once_each([event for event in events if isinstance(event, Turn)])
        return SubAgent(tool_use_id, tuple(turns)), readable + 1, unreadable
    if events and isinstance(events[0], Marker):
        # The owner's prompt never reaches a forked sub-agent: a user record there is the skill's
        # arguments, and the run lasts to the end of the transcript.
        own = tuple(event for event in events if not isinstance(event, Prompt))
        return ForkedSkill(own), readable + 1, unreadable
    return None, readable, unreadable + 1


def run_of(
    marker: Marker,
    window: Sequence[Marker | Prompt | Turn],
    session: str,
    sub_agents: Sequence[SubAgent],
) -> Run:
    """Return what one run spent: the turns after its marker, and the sub-agents they spawned."""
    turn_records = [event for event in window if isinstance(event, Turn)]
    tool_use_ids = frozenset(
        tool_use_id for turn in turn_records for tool_use_id in turn.tool_use_ids
    )
    spawned = [agent for agent in sub_agents if agent.tool_use_id in tool_use_ids]
    turns = [*once_each(turn_records), *(turn for agent in spawned for turn in agent.turns)]
    return Run(
        skill=marker.skill,
        session=session,
        marker=marker.uuid,
        date=marker.date,
        producer=f"{PRODUCER}/{marker.version}" if marker.version else PRODUCER,
        output_tokens=sum(turn.counted_output_tokens for turn in turns),
        tokens_read=sum(turn.tokens_read for turn in turns),
        turns=len(turns),
        sub_agents=len(spawned),
        models=tuple(sorted({turn.model for turn in turns if turn.model})),
        counting=APPROXIMATE if any(turn.approximate for turn in turns) else EXACT,
    )


def end_of(events: Sequence[Marker | Prompt | Turn], start: int) -> int:
    """Return where the run starting at an index ends: the next prompt or marker, or the end."""
    return next(
        (
            index
            for index, event in enumerate(events)
            if index > start and isinstance(event, (Marker, Prompt))
        ),
        len(events),
    )


def runs_in(
    events: Sequence[Marker | Prompt | Turn], session: str, sub_agents: Sequence[SubAgent]
) -> list[Run]:
    """Return each run the events hold: from a marker to the next prompt or marker, or the end."""
    markers = [(index, event) for index, event in enumerate(events) if isinstance(event, Marker)]
    return [
        run_of(marker, events[index + 1 : end_of(events, index)], session, sub_agents)
        for index, marker in markers
    ]


def read_session(transcript: Path) -> Reading:
    """Return the runs in a session's transcript and in the skills forked from it.

    Each run takes the sub-agents its turns spawned, from the transcripts beside the session's.
    """
    events, readable, unreadable = read_events(transcript)
    agents_folder = transcript.with_suffix("") / SUBAGENTS_FOLDER
    meta_paths = sorted(agents_folder.glob(f"*{META_SUFFIX}")) if agents_folder.is_dir() else []
    readings = [read_sub_agent(meta_path) for meta_path in meta_paths]
    sub_agents = [agent for agent, _, _ in readings if isinstance(agent, SubAgent)]
    forked = [agent for agent, _, _ in readings if isinstance(agent, ForkedSkill)]
    session = transcript.stem
    return Reading(
        runs=(
            *runs_in(events, session, sub_agents),
            *(run for skill in forked for run in runs_in(skill.events, session, sub_agents)),
        ),
        readable=readable + sum(count for _, count, _ in readings),
        unreadable=unreadable + sum(count for _, _, count in readings),
    )


def run_from_ledger(line: str) -> Run | Unreadable:
    """Return the run a ledger line records, or that the line cannot be read as one."""
    try:
        loaded: object = json.loads(line)
    except json.JSONDecodeError:
        return Unreadable()
    if not isinstance(loaded, dict):
        return Unreadable()
    skill = as_text(loaded.get("skill"))
    if not skill:
        return Unreadable()
    models = loaded.get("models")
    return Run(
        skill=skill,
        session=as_text(loaded.get("session")),
        marker=as_text(loaded.get("marker")),
        date=as_text(loaded.get("date")),
        producer=as_text(loaded.get("producer")),
        output_tokens=as_count(loaded.get("output_tokens")),
        tokens_read=as_count(loaded.get("tokens_read")),
        turns=as_count(loaded.get("turns")),
        sub_agents=as_count(loaded.get("sub_agents")),
        models=tuple(as_text(model) for model in models) if isinstance(models, list) else (),
        counting=as_text(loaded.get("counting")) or EXACT,
    )


def read_ledger(ledger: Path) -> Reading:
    """Return the runs the ledger holds; none when there is no ledger yet."""
    if not ledger.is_file():
        return Reading((), 0, 0)
    with ledger.open(encoding="utf-8", errors="replace") as handle:
        outcomes = [run_from_ledger(line) for line in handle if line.strip()]
    runs = [outcome for outcome in outcomes if isinstance(outcome, Run)]
    return Reading(tuple(runs), len(runs), len(outcomes) - len(runs))


def combined(readings: Sequence[Reading]) -> Reading:
    """Return the readings as one, each run once: a run in the ledger and on disk is one run."""
    by_key = {(run.session, run.marker): run for reading in readings for run in reading.runs}
    return Reading(
        runs=tuple(by_key.values()),
        readable=sum(reading.readable for reading in readings),
        unreadable=sum(reading.unreadable for reading in readings),
    )


def project_key(directory: Path) -> str:
    """Return the folder Claude Code names a project by: its path, every other character a dash."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(directory))


def transcripts_in(projects_folder: Path, keys: frozenset[str] | None) -> list[Path]:
    """Return the session transcripts of the projects named by key, or of every project."""
    if not projects_folder.is_dir():
        return []
    folders = [
        folder
        for folder in sorted(projects_folder.iterdir())
        if folder.is_dir() and (keys is None or folder.name in keys)
    ]
    return [path for folder in folders for path in sorted(folder.glob(f"*{TRANSCRIPT_SUFFIX}"))]


def run_git(directory: Path, *arguments: str) -> str:
    """Return what git prints in the directory, or nothing when git is absent or refuses."""
    git_executable = shutil.which("git")
    if git_executable is None:
        return ""
    done = subprocess.run(  # noqa: S603  fixed arguments, no shell, the executable is resolved
        [git_executable, "-C", str(directory), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout.strip() if done.returncode == 0 else ""


def repository_root(directory: Path) -> Path:
    """Return the repository the directory is in, or the directory itself outside one."""
    top = run_git(directory, "rev-parse", "--show-toplevel")
    return Path(top) if top else directory


def skill_folder(repository: Path, skill: str) -> Path | None:
    """Return the folder that holds the skill's text, or None when no skill of that name is here."""
    candidates = [repository / folder / skill for folder in SKILL_FOLDERS]
    found = [path for path in candidates if (path / SKILL_FILE).is_file()]
    return found[0] if found else None


def floor_of(folder: Path) -> int:
    """Return the tokens a skill's text alone takes: its Markdown, at four characters a token."""
    characters = sum(
        len(path.read_text(encoding="utf-8", errors="replace"))
        for path in sorted(folder.rglob("*.md"))
    )
    return -(-characters // CHARACTERS_A_TOKEN)


def skill_version(folder: Path) -> str:
    """Return the version the skill's frontmatter states, or nothing when it states none."""
    match = VERSION_PATTERN.search(
        (folder / SKILL_FILE).read_text(encoding="utf-8", errors="replace")
    )
    return match.group(1) if match else ""


def median_of(values: Sequence[int]) -> int:
    """Return the median, to the nearest whole token."""
    return round(statistics.median(values))


def summary_of(skill: str, runs: Sequence[Run], repository: Path) -> Summary:
    """Return a skill's history in numbers; the floor when its text is in the repository."""
    folder = skill_folder(repository, skill)
    return Summary(
        skill=skill,
        runs=len(runs),
        approximate_runs=sum(1 for run in runs if run.counting == APPROXIMATE),
        median_output_tokens=median_of([run.output_tokens for run in runs]),
        largest_output_tokens=max(run.output_tokens for run in runs),
        median_tokens_read=median_of([run.tokens_read for run in runs]),
        median_turns=median_of([run.turns for run in runs]),
        median_sub_agents=median_of([run.sub_agents for run in runs]),
        models=tuple(sorted({model for run in runs for model in run.models})),
        last_run=max(run.date for run in runs),
        floor_tokens=floor_of(folder) if folder else None,
    )


def summaries_of(reading: Reading, repository: Path) -> list[Summary]:
    """Return one summary per skill with history, in the order of their names."""
    skills = sorted({run.skill for run in reading.runs})
    return [
        summary_of(skill, [run for run in reading.runs if run.skill == skill], repository)
        for skill in skills
    ]


def runs_text(summary: Summary) -> str:
    """Return a skill's runs as text, with how many are approximate when any is."""
    runs = f"{summary.runs} run{'s' if summary.runs != 1 else ''}"
    if summary.approximate_runs == 0:
        return runs
    if summary.approximate_runs == summary.runs:
        return f"{runs}, approximate"
    return f"{runs}, {summary.approximate_runs} approximate"


def history_lines(summary: Summary) -> list[str]:
    """Return one skill's history as text: the estimate first, then where it comes from."""
    runs = runs_text(summary)
    models = ", ".join(summary.models) or "no model recorded"
    return [
        f"estimate: {summary.skill}: {summary.median_output_tokens:,} output tokens"
        f" (median of {runs}; largest {summary.largest_output_tokens:,})",
        f"  a run read {summary.median_tokens_read:,} tokens over {summary.median_turns} turns"
        f" and {summary.median_sub_agents} sub-agents (medians); {models};"
        f" last run {summary.last_run or 'undated'}",
        *(
            [f"  the floor is {summary.floor_tokens:,} tokens of instructions"]
            if summary.floor_tokens is not None
            else []
        ),
    ]


def estimate_lines(skill: str, summaries: Sequence[Summary], repository: Path) -> list[str]:
    """Return the estimate for one skill: its history, or its floor and "no history"."""
    found = [summary for summary in summaries if summary.skill == skill]
    if found:
        return history_lines(found[0])
    folder = skill_folder(repository, skill)
    if folder is None:
        return [f"estimate: {skill}: no history, and no skill of that name"]
    return [
        f"estimate: {skill}: no history; the floor is {floor_of(folder):,} tokens of instructions"
    ]


def report_lines(summaries: Sequence[Summary]) -> list[str]:
    """Return every skill's history, one line each, and how much history there is."""
    if not summaries:
        return ["skill-costs: no run of any skill on this machine or in the ledger"]
    lines = [
        f"{summary.skill}: {runs_text(summary)};"
        f" {summary.median_output_tokens:,} output tokens a run (median),"
        f" {summary.largest_output_tokens:,} at most; {summary.median_tokens_read:,} read;"
        f" {summary.median_turns} turns; {summary.median_sub_agents} sub-agents;"
        f" last {summary.last_run or 'undated'}; {', '.join(summary.models) or 'no model recorded'}"
        for summary in summaries
    ]
    total = sum(summary.runs for summary in summaries)
    return [*lines, f"skill-costs: {len(summaries)} skill(s) with history, {total} run(s)"]


def ledger_entry(run: Run, commit: str, repository: Path) -> dict[str, object]:
    """Return a run as the ledger keeps it, with the commit and the skill's version at the time."""
    folder = skill_folder(repository, run.skill)
    return {
        "skill": run.skill,
        "skill_version": skill_version(folder) if folder else "",
        "commit": commit,
        "date": run.date,
        "output_tokens": run.output_tokens,
        "tokens_read": run.tokens_read,
        "turns": run.turns,
        "sub_agents": run.sub_agents,
        "models": list(run.models),
        "producer": run.producer,
        "session": run.session,
        "marker": run.marker,
        "counting": run.counting,
    }


def append_ledger(
    repository: Path, projects_folder: Path, keys: frozenset[str]
) -> tuple[int, Reading]:
    """Append this project's runs that the ledger lacks, and return how many, with what was read."""
    ledger = repository / LEDGER
    on_disk = combined([read_session(path) for path in transcripts_in(projects_folder, keys)])
    in_ledger = read_ledger(ledger)
    known = {(run.session, run.marker) for run in in_ledger.runs}
    new_runs = sorted(
        (run for run in on_disk.runs if (run.session, run.marker) not in known),
        key=lambda run: (run.date, run.skill, run.session, run.marker),
    )
    commit = run_git(repository, "rev-parse", "--short", "HEAD")
    if new_runs:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(
                "".join(
                    json.dumps(ledger_entry(run, commit, repository)) + "\n" for run in new_runs
                )
            )
    return len(new_runs), combined([on_disk, in_ledger])


def read_conf(path: Path) -> dict[str, str]:
    """Return the KEY=value pairs of kit.conf, or nothing when the project has none."""
    if not path.is_file():
        return {}
    pairs = [
        line.split("=", 1)
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    ]
    return {key.strip(): value.strip() for key, value in pairs}


def cap_of(conf: dict[str, str]) -> int | None:
    """Return the cap kit.conf sets, or None when it sets none that is a number."""
    value = conf.get(CAP_KEY, "")
    return int(value) if value.isdigit() else None


def artifacts_of(conf: dict[str, str]) -> dict[str, str]:
    """Return the artifact each gate skill writes, as kit.conf names them: skill=path, by comma."""
    pairs = [
        entry.split("=", 1) for entry in conf.get(ARTIFACTS_KEY, "").split(",") if "=" in entry
    ]
    return {skill.strip(): artifact.strip() for skill, artifact in pairs}


def hook_decision(
    skill: str,
    summaries: Sequence[Summary],
    repository: Path,
    cap: int | None,
    existing_artifact: str | None,
) -> tuple[str, str]:
    """Return allow or ask for one capped skill, and the reason: a number, or a second run."""
    found = [summary for summary in summaries if summary.skill == skill]
    if cap is None:
        return ASK, f"no cap: set {CAP_KEY} in {KIT_CONF}; say yes to run {skill}"
    if existing_artifact is not None:
        return (
            ASK,
            f"{existing_artifact} exists: a second run is the owner's to start; "
            f"say yes to run {skill} again",
        )
    if not found:
        return (
            ALLOW,
            f"{estimate_lines(skill, summaries, repository)[0]}; the first run sets the estimate",
        )
    estimate = history_lines(found[0])[0]
    if found[0].median_output_tokens > cap:
        return ASK, f"{estimate}: over the cap of {cap:,}; say yes to run it"
    return ALLOW, f"{estimate}: under the cap of {cap:,}"


def skill_called(call: object) -> str:
    """Return the skill a Skill tool call names, or nothing when the call is another tool's."""
    if nested(call, ("tool_name",)) != SKILL_TOOL:
        return ""
    return as_text(nested(call, ("tool_input", "skill"))).strip().lstrip("/").split(" ", 1)[0]


def capped_skills(conf: dict[str, str]) -> list[str]:
    """Return the skills kit.conf holds to the cap, in the order it names them."""
    return [name.strip() for name in conf.get(CAPPED_KEY, "").split(",") if name.strip()]


def decision_for(
    repository: Path, projects_folder: Path, skill: str
) -> tuple[str, str, Reading] | None:
    """Return what the hook answers before a call of the skill, its reason, and what was read.

    None for a skill kit.conf does not cap. `scripts/blockers.py` asks the same question.
    """
    conf = read_conf(repository / KIT_CONF)
    if not skill or skill not in capped_skills(conf):
        return None
    reading = combined(
        [read_ledger(repository / LEDGER)]
        + [read_session(path) for path in transcripts_in(projects_folder, None)]
    )
    artifact = artifacts_of(conf).get(skill)
    existing_artifact = artifact if artifact and (repository / artifact).exists() else None
    answer, reason = hook_decision(
        skill, summaries_of(reading, repository), repository, cap_of(conf), existing_artifact
    )
    return answer, reason, reading


def write_hook_decision(answer: str, reason: str) -> None:
    """Write the decision Claude Code reads from a PreToolUse hook's standard output."""
    sys.stdout.write(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_EVENT,
                    "permissionDecision": answer,
                    "permissionDecisionReason": reason,
                }
            }
        )
        + "\n"
    )


def run_hook(repository: Path, projects_folder: Path) -> int:
    """Answer Claude Code before a skill call: allow under the cap, ask over it, else nothing.

    When the check itself fails, the answer is ask: a hook that crashed would exit 1, and Claude
    Code lets the call go on after any exit but 2, so the cap would pass unasked.
    """
    try:
        call: object = json.loads(sys.stdin.read())
        skill = skill_called(call)
        decided = decision_for(repository, projects_folder, skill)
    # Any failure of the check asks: none may let a call pass unasked.
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
        write_hook_decision(
            "ask", f"skill-costs: the cost check failed ({failure}); asking rather than allowing"
        )
        return EXIT_RAN
    if decided is None:
        return EXIT_RAN
    answer, reason, reading = decided
    write_hook_decision(answer, reason)
    say_unreadable(reading)
    return EXIT_RAN


def say_unreadable(reading: Reading) -> int:
    """Say on stderr what could not be read, and return the exit code that follows."""
    if reading.unreadable:
        sys.stderr.write(
            f"skill-costs: {reading.unreadable} record(s) could not be read;"
            " Claude Code's transcript format may have changed\n"
        )
    return EXIT_NOTHING_READABLE if reading.unreadable and not reading.readable else EXIT_RAN


def main() -> int:
    """Read the transcripts and the ledger, and print what the command asks for."""
    parser = argparse.ArgumentParser(description="What a skill cost before, in tokens.")
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("report", help="each skill's history, or one skill's estimate")
    report.add_argument("skill", nargs="?", help="the skill to estimate")
    report.add_argument("--json", action="store_true", help="the summaries as JSON")
    commands.add_parser("append", help="write this project's runs to the ledger, each once")
    commands.add_parser("hook", help="before a skill call: allow under the cap, ask over it")
    arguments = parser.parse_args()
    working_directory = Path.cwd()
    repository = repository_root(working_directory)
    config_home = Path(os.environ.get(CONFIG_DIR_VARIABLE) or DEFAULT_CONFIG_DIR).expanduser()
    projects_folder = config_home / PROJECTS_FOLDER
    keys = frozenset({project_key(working_directory), project_key(repository)})
    if arguments.command == "hook":
        return run_hook(repository, projects_folder)
    if arguments.command == "append":
        appended, reading = append_ledger(repository, projects_folder, keys)
        sys.stdout.write(f"skill-costs: appended {appended} run(s) to {LEDGER}\n")
        return say_unreadable(reading)
    reading = combined(
        [read_ledger(repository / LEDGER)]
        + [read_session(path) for path in transcripts_in(projects_folder, None)]
    )
    summaries = summaries_of(reading, repository)
    if arguments.json:
        chosen = [one for one in summaries if arguments.skill in (None, one.skill)]
        sys.stdout.write(json.dumps([asdict(summary) for summary in chosen], indent=1) + "\n")
    elif arguments.skill:
        sys.stdout.write(
            "".join(f"{line}\n" for line in estimate_lines(arguments.skill, summaries, repository))
        )
    else:
        sys.stdout.write("".join(f"{line}\n" for line in report_lines(summaries)))
    return say_unreadable(reading)


if __name__ == "__main__":
    sys.exit(main())
