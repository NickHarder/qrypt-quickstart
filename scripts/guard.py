#!/usr/bin/env python3
"""Refuse the shell commands the owner's rules forbid, before Claude Code runs them.

    scripts/guard.py     (before every Bash call: PreToolUse in .claude/settings.json)

Two of the owner's rules are "never" rules, and a hook holds them rather than the model's memory:

    an agent never reads a `.env`   a command that names `.env` or `.env.<anything>` is
                                    refused, except `.env.example`, which names the keys only
    nobody force-pushes             `git push` with `--force`, `-f`, `--force-with-lease`,
                                    `--mirror` or a `+refspec` is refused, however git is called

The `Read` deny rules in `.claude/settings.json` cover only Claude Code's own file tools, so
`cat .env` through Bash passes them; this hook reads the whole command text instead. A command run
by `bash -c '...'` is read too. It cannot see what a glob (`cat .e*`) or a variable expands to: for
that, the owner turns on Claude Code's sandbox.

Text that is only written somewhere may name an env file, since writing it reads nothing: the body
of a heredoc with a quoted delimiter that `cat` or `tee` writes to a file, or that `git commit -m
"$(cat <<'EOF' ...)"` takes as its message; the arguments of `echo` or `printf` sent to a file; and
a commit message. Any of these holding `$(` or a backtick is read like any other text, and so is
everything that runs, a heredoc fed to `python` or piped to `bash` included: it could open the file.
In a command with a pipe or a process substitution (`>(...)`), no text counts as only written.

Any other command, and any other tool, passes untouched: the hook prints nothing. A refused
command gets the answer deny, with the reason. When its own check fails, the answer is ask, naming
the error: Claude Code lets a call go on after any exit but 2, so a crash would let the command
through.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path
from typing import Final

HOOK_EVENT: Final = "PreToolUse"
SHELL_TOOL: Final = "Bash"
DENY: Final = "deny"
ASK: Final = "ask"

# `.env` or `.env.<suffix>` as a path or a path's last part, not inside a longer name (`.envrc`,
# `process.env`). The example is the one such file an agent may read.
ENV_FILE_PATTERN: Final = re.compile(r"(?<![\w.$-])\.env(?:\.[\w-]+)*(?![\w-])")
ENV_EXAMPLE_NAME: Final = ".env.example"
# What ends one simple command and starts the next, as shlex splits them off.
COMMAND_SEPARATORS: Final = frozenset({";", "&&", "||", "|", "&", "(", ")", "\n"})
# git's own options before the subcommand that take a value as the next word.
GIT_OPTIONS_WITH_A_VALUE: Final = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})
FORCE_FLAGS: Final = ("--force", "--force-with-lease", "--mirror")
SHORT_FORCE_FLAG: Final = "f"
FORCED_REFSPEC_PREFIX: Final = "+"
ENV_REASON: Final = (
    "guard: this command names {name}, and an agent never reads a .env (a key it reads goes to the "
    "model provider and into the transcript); ask the owner for what you need from it"
)
FORCE_REASON: Final = (
    "guard: this is a force-push, and nobody force-pushes; a red pipeline gets an ordinary commit "
    "on top"
)
# A word that holds a space may be a command of its own, run by `bash -c` or `sh -c`.
NESTED_COMMAND_PATTERN: Final = re.compile(r"\s")
# When shlex cannot split the text (an unclosed quote), git push with any force sign refuses.
FORCE_FALLBACK_PATTERN: Final = re.compile(
    r"\bgit\b.*\bpush\b.*(?:--force|--mirror|\s-[a-zA-Z]*f|\s\+\S)"
)
# A heredoc whose delimiter is quoted, so the shell expands nothing in its body: `<<'EOF'`.
QUOTED_HEREDOC_PATTERN: Final = re.compile(r"<<(-?)[ \t]*(['\"])(\w+)\2")
# `git commit -m "$(cat <<'EOF'`, ending the line: the body of the heredoc is the commit's message.
COMMIT_MESSAGE_HEREDOC_PATTERN: Final = re.compile(
    r"^\s*git\s+commit\b[^|;&`]*\$\(\s*cat\s*<<-?[ \t]*(['\"])\w+\1\s*$"
)
# Any heredoc operator, quoted or not, other than a here-string's `<<<`.
HEREDOC_OPERATOR_PATTERN: Final = re.compile(r"(?<!<)<<(?!<)")
# Output sent on to another command, which may read what the text names: a pipe or a process
# substitution. Where the command has one, no text counts as only written.
SENT_ON_PATTERN: Final = re.compile(r"\||[<>]\(")
# What makes text run rather than sit: a command substitution.
EXPANSION_PATTERN: Final = re.compile(r"\$\(|`")
HEREDOC_WRITERS: Final = frozenset({"cat", "tee"})
ARGUMENT_WRITERS: Final = frozenset({"echo", "printf"})
COMMIT_SUBCOMMAND: Final = "commit"
COMMIT_MESSAGE_LONG_OPTION: Final = "--message"
COMMIT_MESSAGE_SHORT_OPTION: Final = "m"
HEREDOC_OPERATOR: Final = "<<"
REDIRECTION_CHARACTERS: Final = frozenset("<>")
REDIRECTION_OPERATOR_CHARACTERS: Final = frozenset("<>&|")
OUTPUT_REDIRECTION_CHARACTER: Final = ">"


def first_env_file_in(text: str) -> str:
    """Return the first `.env` file a text names, other than the example, or ""."""
    names = [match.group(0) for match in ENV_FILE_PATTERN.finditer(text)]
    return next((name for name in names if name != ENV_EXAMPLE_NAME), "")


def is_redirection(word: str) -> bool:
    """Say whether a word shlex split off is a redirection operator, such as `>`, `>>` or `<`."""
    characters = set(word)
    return (
        bool(characters & REDIRECTION_CHARACTERS) and characters <= REDIRECTION_OPERATOR_CHARACTERS
    )


def sends_output_to_a_file(words: list[str]) -> bool:
    """Say whether a simple command redirects its output, as `>` or `>>` does."""
    return any(is_redirection(word) and OUTPUT_REDIRECTION_CHARACTER in word for word in words)


def writes_its_heredoc_to_a_file(line: str) -> bool:
    """Say whether the line opening a heredoc only writes its body: to a file, or as a message."""
    if COMMIT_MESSAGE_HEREDOC_PATTERN.match(line):
        return True
    if EXPANSION_PATTERN.search(line):
        return False
    try:
        commands = simple_commands(line)
    except ValueError:
        return False
    heredoc_commands = [
        words for words in commands if any(word.startswith(HEREDOC_OPERATOR) for word in words)
    ]
    return bool(heredoc_commands) and all(
        Path(words[0]).name == "tee"
        or (Path(words[0]).name in HEREDOC_WRITERS and sends_output_to_a_file(words))
        for words in heredoc_commands
    )


def without_written_heredocs(command: str) -> str:
    """Return the command text without the bodies of the heredocs it only writes."""
    lines = command.split("\n")
    kept_lines: list[str] = []
    position = 0
    while position < len(lines):
        line = lines[position]
        kept_lines.append(line)
        position += 1
        every_heredoc_is_quoted = len(HEREDOC_OPERATOR_PATTERN.findall(line)) == len(
            QUOTED_HEREDOC_PATTERN.findall(line)
        )
        drop_bodies = every_heredoc_is_quoted and writes_its_heredoc_to_a_file(line)
        for heredoc in QUOTED_HEREDOC_PATTERN.finditer(line):
            strips_leading_tabs, delimiter = heredoc.group(1) == "-", heredoc.group(3)
            while position < len(lines):
                body_line = lines[position]
                position += 1
                ends_the_body = (
                    body_line.lstrip("\t") if strips_leading_tabs else body_line
                ) == delimiter
                if ends_the_body or not drop_bodies:
                    kept_lines.append(body_line)
                if ends_the_body:
                    break
    return "\n".join(kept_lines)


def words_that_may_be_read(words: list[str]) -> list[str]:
    """Return the words of a simple command that a program may read as a path or run as code.

    The arguments of `echo` or `printf` sent to a file, and a commit's message, are only written:
    they are left out unless they hold a command substitution.
    """
    program = Path(words[0]).name
    subcommand, arguments = git_subcommand_arguments(words)
    written_positions: set[int] = set()
    if program in ARGUMENT_WRITERS and sends_output_to_a_file(words):
        after_redirection = {
            position + 1 for position, word in enumerate(words) if is_redirection(word)
        }
        written_positions = {
            position
            for position, word in enumerate(words)
            if position > 0 and not is_redirection(word) and position not in after_redirection
        }
    elif program == "git" and subcommand == COMMIT_SUBCOMMAND:
        first_argument = len(words) - len(arguments)
        written_positions = {
            first_argument + position + 1
            for position, argument in enumerate(arguments)
            if argument == COMMIT_MESSAGE_LONG_OPTION
            or (
                argument.startswith("-")
                and not argument.startswith("--")
                and argument.endswith(COMMIT_MESSAGE_SHORT_OPTION)
            )
        } | {
            first_argument + position
            for position, argument in enumerate(arguments)
            if argument.startswith(COMMIT_MESSAGE_LONG_OPTION + "=")
        }
    return [
        word
        for position, word in enumerate(words)
        if position not in written_positions or EXPANSION_PATTERN.search(word)
    ]


def env_file_named(command: str) -> str:
    """Return the first `.env` file the command may read, other than the example, or ""."""
    if SENT_ON_PATTERN.search(command):
        return first_env_file_in(command)
    text = without_written_heredocs(command)
    try:
        commands = simple_commands(text)
    except ValueError:
        return first_env_file_in(text)
    words_read = [word for words in commands for word in words_that_may_be_read(words)]
    return first_env_file_in("\n".join(words_read))


def simple_commands(command: str) -> list[list[str]]:
    """Split shell text into simple commands, each a list of words; ValueError on bad quotes."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    words = list(lexer)
    commands: list[list[str]] = [[]]
    for word in words:
        if word in COMMAND_SEPARATORS:
            commands.append([])
        else:
            commands[-1].append(word)
    return [words_of_one for words_of_one in commands if words_of_one]


def git_subcommand_arguments(words: list[str]) -> tuple[str, list[str]]:
    """Return git's subcommand in a simple command and the words after it; ("", []) without git."""
    git_positions = [position for position, word in enumerate(words) if Path(word).name == "git"]
    if not git_positions:
        return "", []
    after_git = words[git_positions[0] + 1 :]
    skip_next_word = False
    for position, word in enumerate(after_git):
        if skip_next_word:
            skip_next_word = False
        elif word in GIT_OPTIONS_WITH_A_VALUE:
            skip_next_word = True
        elif not word.startswith("-"):
            return word, after_git[position + 1 :]
    return "", []


def is_force_argument(argument: str) -> bool:
    """Say whether one argument of `git push` makes it a force-push."""
    if argument.startswith(FORCE_FLAGS):
        return True
    if argument.startswith("-") and not argument.startswith("--"):
        return SHORT_FORCE_FLAG in argument[1:]
    return argument.startswith(FORCED_REFSPEC_PREFIX)


def is_force_push(command: str) -> bool:
    """Say whether any simple command in the text, or a command nested in one, is a force-push."""
    try:
        commands = simple_commands(command)
    except ValueError:
        return FORCE_FALLBACK_PATTERN.search(command) is not None
    for words in commands:
        subcommand, arguments = git_subcommand_arguments(words)
        if subcommand == "push" and any(is_force_argument(argument) for argument in arguments):
            return True
        nested = [word for word in words if NESTED_COMMAND_PATTERN.search(word)]
        if any(is_force_push(nested_command) for nested_command in nested):
            return True
    return False


def refusal_reason(command: str) -> str:
    """Return why the guard refuses a shell command, or "" when it lets the command run."""
    env_file = env_file_named(command)
    if env_file:
        return ENV_REASON.format(name=env_file)
    if is_force_push(command):
        return FORCE_REASON
    return ""


def shell_command_of(tool_call: object) -> str:
    """Return the command of a Bash tool call, or "" when the call is another tool's."""
    if not isinstance(tool_call, dict) or tool_call.get("tool_name") != SHELL_TOOL:
        return ""
    tool_input = tool_call.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    return command if isinstance(command, str) else ""


def write_decision(answer: str, reason: str) -> None:
    """Write the decision Claude Code reads from a PreToolUse hook's standard output."""
    decision = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": answer,
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(decision) + "\n")


def main() -> int:
    """Read the tool call from stdin, and refuse it when it breaks one of the rules."""
    try:
        tool_call: object = json.loads(sys.stdin.read())
        reason = refusal_reason(shell_command_of(tool_call))
    # Any failure of the check asks: none may let a command pass unasked.
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
        write_decision(ASK, f"guard: its check failed ({failure}); say yes to run it")
        return 0
    if reason:
        write_decision(DENY, reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
