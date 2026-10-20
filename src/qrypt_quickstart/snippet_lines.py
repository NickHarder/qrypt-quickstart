"""Count a quickstart snippet's lines the way the brief does: excluding comments and imports.

The brief caps each snippet at 25 lines "excluding comments and imports". This module makes that
count a check rather than a claim (docs/brief/research-review.md, item C9). A line counts when it
holds code. These do not count: a blank line, a comment, a docstring (the comment a reader sees
first in Python), and every line of an import statement.

Run `python -m qrypt_quickstart.snippet_lines <file>...`: it prints each file's count and exits 1
when one is over the limit.
"""

import ast
import io
import sys
import tokenize
from pathlib import Path
from typing import Final

SNIPPET_LINE_LIMIT: Final = 25
NON_CODE_TOKEN_TYPES: Final = frozenset(
    {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
)


def lines_spanned(node: ast.stmt) -> set[int]:
    """Return the line numbers a statement covers, from its first line to its last."""
    last_line = node.end_lineno if node.end_lineno is not None else node.lineno
    return set(range(node.lineno, last_line + 1))


def is_docstring(node: ast.stmt) -> bool:
    """Say whether a statement is a bare string, which Python reads as documentation."""
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def count_python_lines(source: str) -> int:
    """Count the lines of Python source that hold code, excluding comments and imports.

    Args:
        source: The text of a Python file.

    Returns:
        How many lines count against the snippet limit.
    """
    code_lines = {
        token.start[0]
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type not in NON_CODE_TOKEN_TYPES
    }
    excluded_lines: set[int] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import | ast.ImportFrom) or (
            isinstance(node, ast.stmt) and is_docstring(node)
        ):
            excluded_lines |= lines_spanned(node)
    return len(code_lines - excluded_lines)


def main() -> int:
    """Print each named snippet's count and return 1 when any is over the limit."""
    over_limit_count = 0
    for snippet_path in (Path(argument) for argument in sys.argv[1:]):
        line_count = count_python_lines(snippet_path.read_text())
        verdict = "ok" if line_count <= SNIPPET_LINE_LIMIT else "over the limit"
        sys.stdout.write(f"{snippet_path}: {line_count} of {SNIPPET_LINE_LIMIT} lines, {verdict}\n")
        if line_count > SNIPPET_LINE_LIMIT:
            over_limit_count += 1
    return 1 if over_limit_count else 0


if __name__ == "__main__":
    sys.exit(main())
