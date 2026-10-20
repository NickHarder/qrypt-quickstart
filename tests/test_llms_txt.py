"""The agent-readable quickstart: llms.txt and llms-full.txt (RQ-38).

Both are built from Markdown in site/, filled from the snippet files, so an agent reads exactly the
code CI runs. Their rules must agree with the snippets, and llms-full.txt must quote every message
the troubleshooting page explains.
"""

import html
import re
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.site_builder import build_site

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
SNIPPETS: Final = [
    REPOSITORY_ROOT / "quickstart" / "python" / "quickstart.py",
    REPOSITORY_ROOT / "quickstart" / "node" / "quickstart.mjs",
    REPOSITORY_ROOT / "rust" / "src" / "main.rs",
]
ENDPOINT: Final = "https://api-eus.qrypt.com/api/v1/quantum-entropy"


@pytest.fixture(scope="module")
def built_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output_directory = tmp_path_factory.mktemp("site")
    build_site(output_directory=output_directory)
    return output_directory


def test_llms_txt_has_the_shape_llmstxt_org_describes(built_site: Path) -> None:
    lines = (built_site / "llms.txt").read_text().splitlines()
    assert lines[0].startswith("# ")
    assert next(line for line in lines[1:] if line.strip()).startswith("> ")
    assert any(re.match(r"- \[[^\]]+\]\([^)]+\)", line) for line in lines)


@pytest.mark.parametrize("file_name", ["llms.txt", "llms-full.txt"])
def test_both_files_state_every_rule_the_snippets_follow(built_site: Path, file_name: str) -> None:
    text = (built_site / file_name).read_text()
    for rule in (
        ENDPOINT,
        "Accept: application/json",
        "Authorization: Bearer",
        "size=1",
        "KiB",
        "QRYPT_API_KEY",
        "No SDK",
        "Never print",
        "429",
        "403",
        # Backlog item B-07: Gemini CLI tried to read the token file and ran both programs twice.
        "Never open `.env`",
        "never print the environment",
        "Run the finished program once",
    ):
        assert rule in text, f"{file_name} does not say {rule!r}"


@pytest.mark.parametrize("file_name", ["llms.txt", "llms-full.txt"])
def test_both_files_install_python_packages_in_a_virtual_environment(
    built_site: Path, file_name: str
) -> None:
    # Agent test round 1: every Python run had to find this out (a system Python refuses a bare
    # `pip install` under PEP 668), so the agent-readable files say it first.
    text = (built_site / file_name).read_text()
    for rule in (
        "python3 -m venv .venv",
        ".venv/bin/pip install cryptography python-dotenv",
        ".venv/bin/python quickstart.py",
        "externally-managed-environment",
        "`.venv/`",
    ):
        assert rule in text, f"{file_name} does not say {rule!r}"


def test_the_troubleshooting_page_explains_a_refused_pip_install(built_site: Path) -> None:
    page = (built_site / "troubleshooting.html").read_text()
    assert "externally-managed-environment" in page
    assert "python3 -m venv .venv" in page


def test_the_snippets_use_the_endpoint_and_headers_llms_txt_names(built_site: Path) -> None:
    for snippet in SNIPPETS:
        source = snippet.read_text()
        assert ENDPOINT in source
        assert "application/json" in source
        assert "Bearer" in source
        assert "size=1" in source


def test_llms_full_txt_holds_every_snippet_word_for_word(built_site: Path) -> None:
    text = (built_site / "llms-full.txt").read_text()
    for snippet in SNIPPETS:
        assert snippet.read_text() in text


def test_llms_full_txt_quotes_every_message_the_troubleshooting_page_explains(
    built_site: Path,
) -> None:
    page = (built_site / "troubleshooting.html").read_text()
    messages = [
        html.unescape(code)
        for code in re.findall(r'<code class="language-text">(.*?)</code>', page, re.DOTALL)
    ]
    assert len(messages) >= 7
    full_text = (built_site / "llms-full.txt").read_text()
    for message in messages:
        assert message in full_text, f"llms-full.txt does not quote {message!r}"


def test_the_pages_link_to_llms_txt_and_llms_txt_links_to_the_full_version(
    built_site: Path,
) -> None:
    assert 'href="llms.txt"' in (built_site / "index.html").read_text()
    llms_text = (built_site / "llms.txt").read_text()
    assert "(llms-full.txt)" in llms_text
    assert "(troubleshooting.html)" in llms_text


def test_no_markdown_source_is_published_as_is(built_site: Path) -> None:
    assert not list(built_site.glob("*.md"))
