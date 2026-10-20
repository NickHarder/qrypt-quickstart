from pathlib import Path
from typing import Final

from qrypt_quickstart.snippet_lines import SNIPPET_LINE_LIMIT, count_python_lines

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]


def test_comments_docstrings_imports_and_blank_lines_are_not_counted() -> None:
    source = '''"""A module docstring
over two lines."""
import os
from sys import (
    argv,
)

# a comment
value = os.sep  # a trailing comment does not hide the code
print(argv, value)
'''
    assert count_python_lines(source) == 2


def test_a_statement_over_several_lines_counts_each_line() -> None:
    source = "total = sum(\n    [1, 2],\n)\n"
    assert count_python_lines(source) == 3


def test_the_python_quickstart_is_within_the_limit() -> None:
    snippet = REPOSITORY_ROOT / "quickstart" / "python" / "quickstart.py"
    assert count_python_lines(snippet.read_text()) <= SNIPPET_LINE_LIMIT
