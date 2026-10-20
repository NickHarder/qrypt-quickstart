"""Count a quickstart snippet's lines the way the brief does: excluding comments and imports.

The brief caps each snippet at 25 lines "excluding comments and imports". This module makes that
count a check rather than a claim (docs/brief/research-review.md, item C9). A line counts when it
holds code. These do not count: a blank line, a comment, a docstring (the comment a reader sees
first in Python), and every line of an import statement. Python is read with its own tokenizer;
JavaScript and Rust, line by line: a line that is only a `//` comment (in Rust, `///` and `//!`
doc comments too), a line of a `/* ... */` block that opens a line, and the lines of a static
`import` statement in JavaScript or a `use` declaration in Rust.

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


def count_c_family_lines(source: str, *, import_keyword: str) -> int:
    """Count the lines of `//`-commented source that hold code, excluding comments and imports.

    Args:
        source: The text of a JavaScript module or a Rust file.
        import_keyword: The word that opens an import statement: `import` or `use`.

    Returns:
        How many lines count against the snippet limit.
    """
    code_line_count = 0
    is_in_block_comment = False
    is_in_import = False
    for line in source.splitlines():
        stripped_line = line.strip()
        if is_in_block_comment or stripped_line.startswith("/*"):
            is_in_block_comment = "*/" not in stripped_line
        elif is_in_import or stripped_line.startswith(f"{import_keyword} "):
            is_in_import = not stripped_line.endswith(";")
        elif stripped_line and not stripped_line.startswith("//"):
            code_line_count += 1
    return code_line_count


def count_javascript_lines(source: str) -> int:
    """Count the lines of JavaScript source that hold code, excluding comments and imports."""
    return count_c_family_lines(source, import_keyword="import")


def count_rust_lines(source: str) -> int:
    """Count the lines of Rust source that hold code, excluding comments and `use` declarations."""
    return count_c_family_lines(source, import_keyword="use")


def count_snippet_lines(snippet_path: Path) -> int:
    """Count a snippet's lines with the counter for its language, chosen by its suffix.

    Raises:
        ValueError: If the suffix is not one this module can count.
    """
    source = snippet_path.read_text()
    if snippet_path.suffix == ".py":
        return count_python_lines(source)
    if snippet_path.suffix in {".js", ".mjs"}:
        return count_javascript_lines(source)
    if snippet_path.suffix == ".rs":
        return count_rust_lines(source)
    message = f"no line counter for {snippet_path.suffix} files: {snippet_path}"
    raise ValueError(message)


def main() -> int:
    """Print each named snippet's count and return 1 when any is over the limit."""
    over_limit_count = 0
    for snippet_path in (Path(argument) for argument in sys.argv[1:]):
        line_count = count_snippet_lines(snippet_path)
        verdict = "ok" if line_count <= SNIPPET_LINE_LIMIT else "over the limit"
        sys.stdout.write(f"{snippet_path}: {line_count} of {SNIPPET_LINE_LIMIT} lines, {verdict}\n")
        if line_count > SNIPPET_LINE_LIMIT:
            over_limit_count += 1
    return 1 if over_limit_count else 0


if __name__ == "__main__":
    sys.exit(main())
