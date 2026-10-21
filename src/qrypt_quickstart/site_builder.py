"""Build the quickstart site from `site/`, filling each page's code blocks from the snippet files.

A page in `site/` is HTML with include lines such as
`<!-- include: quickstart/python/quickstart.py -->`. The builder replaces each one with that file's
text, escaped, so the site shows exactly the code CI runs: one source for each snippet
(docs/PLAN.md). The eval target renders pages the same way, so a model is shown the page a
developer sees.

A Markdown page in `site/` (`llms.md`, `llms-full.md`) becomes a plain-text file of the same name
(`llms.txt`, `llms-full.txt`), for AI coding agents: its includes are filled with the raw text of
the files they name, not escaped, and the Markdown source itself is not published.

Run `python -m qrypt_quickstart.site_builder --out build/site`.
"""

import argparse
import html
import re
import shutil
from pathlib import Path
from typing import Final

from .config import REPOSITORY_ROOT

SITE_DIRECTORY_NAME: Final = "site"
# The snippets live in quickstart/, but the Rust quickstart is its crate's program, in rust/src/.
INCLUDABLE_DIRECTORY_NAMES: Final = ("quickstart", "rust/src")
INCLUDE_PATTERN: Final = re.compile(r"<!-- include: (?P<path>[^ ]+) -->")
# The demo video ships with the site, so its link plays in a browser (README, "The demo").
STATIC_SUFFIXES: Final = frozenset({".css", ".js", ".txt", ".mp4"})


class SiteBuildError(Exception):
    """A page names a file the builder cannot include."""


def included_text(included_path: str, *, repository_root: Path, escape_html: bool = True) -> str:
    """Return the text of a file a page includes.

    Args:
        included_path: The path the include line names, from the repository's root.
        repository_root: The repository's root directory.
        escape_html: Escape the text for an HTML page; False for a plain-text page.

    Returns:
        The file's text, escaped for HTML unless `escape_html` is False.

    Raises:
        SiteBuildError: If the path leaves `quickstart/` and `rust/src/`, or names no file.
    """
    includable_directories = [
        (repository_root / directory_name).resolve()
        for directory_name in INCLUDABLE_DIRECTORY_NAMES
    ]
    resolved_path = (repository_root / included_path).resolve()
    if not any(resolved_path.is_relative_to(directory) for directory in includable_directories):
        message = f"a page may include only files under quickstart/ or rust/src/: {included_path}"
        raise SiteBuildError(message)
    if not resolved_path.is_file():
        message = f"a page includes a file that does not exist: {included_path}"
        raise SiteBuildError(message)
    file_text = resolved_path.read_text()
    return html.escape(file_text) if escape_html else file_text


def render_page(page_text: str, *, repository_root: Path = REPOSITORY_ROOT) -> str:
    """Replace each include line of a page with the escaped text of the file it names.

    Args:
        page_text: The page's HTML, with include lines.
        repository_root: The directory include paths are read from.

    Returns:
        The page's HTML, with every include filled in.
    """
    return INCLUDE_PATTERN.sub(
        lambda match: included_text(match["path"], repository_root=repository_root), page_text
    )


def render_text(page_text: str, *, repository_root: Path = REPOSITORY_ROOT) -> str:
    """Replace each include line of a plain-text page with the raw text of the file it names.

    Args:
        page_text: The page's Markdown, with include lines.
        repository_root: The directory include paths are read from.

    Returns:
        The page's text, with every include filled in as it is in the file.
    """
    return INCLUDE_PATTERN.sub(
        lambda match: included_text(
            match["path"], repository_root=repository_root, escape_html=False
        ),
        page_text,
    )


def build_site(*, output_directory: Path, repository_root: Path = REPOSITORY_ROOT) -> list[Path]:
    """Render every page of `site/` and copy its static files into the output directory.

    Args:
        output_directory: Where the built site goes; it is created if missing.
        repository_root: The repository whose `site/` and `quickstart/` are read.

    Returns:
        The files written.
    """
    site_directory = repository_root / SITE_DIRECTORY_NAME
    output_directory.mkdir(parents=True, exist_ok=True)
    written_files: list[Path] = []
    for source_file in sorted(site_directory.iterdir()):
        output_file = output_directory / source_file.name
        if source_file.suffix == ".html":
            rendered_page = render_page(source_file.read_text(), repository_root=repository_root)
            output_file.write_text(rendered_page)
            written_files.append(output_file)
        elif source_file.suffix == ".md":
            text_file = output_directory / f"{source_file.stem}.txt"
            text_file.write_text(
                render_text(source_file.read_text(), repository_root=repository_root)
            )
            written_files.append(text_file)
        elif source_file.suffix in STATIC_SUFFIXES:
            shutil.copyfile(source_file, output_file)
            written_files.append(output_file)
    return written_files


def main() -> None:
    """Build the site into the directory given on the command line."""
    parser = argparse.ArgumentParser(description="Build the quickstart site from site/.")
    parser.add_argument("--out", type=Path, default=REPOSITORY_ROOT / "build" / "site")
    arguments = parser.parse_args()
    written_files = build_site(output_directory=arguments.out)
    print(f"site: wrote {len(written_files)} file(s) to {arguments.out}")  # noqa: T201  a command-line tool


if __name__ == "__main__":
    main()
