import html
import re
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.site_builder import SiteBuildError, build_site, render_page

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
PYTHON_SNIPPET: Final = REPOSITORY_ROOT / "quickstart" / "python" / "quickstart.py"
CODE_BLOCK_PATTERN: Final = re.compile(
    r'<pre[^>]*><code class="language-python">(?P<code>.*?)</code></pre>', re.DOTALL
)


def test_an_include_is_replaced_by_the_file_escaped(tmp_path: Path) -> None:
    included_file = tmp_path / "quickstart" / "example.py"
    included_file.parent.mkdir()
    included_file.write_text('print("<b> & </b>")\n')
    page = "<pre><code><!-- include: quickstart/example.py --></code></pre>"
    rendered_page = render_page(page, repository_root=tmp_path)
    escaped_code = "print(&quot;&lt;b&gt; &amp; &lt;/b&gt;&quot;)\n"
    assert rendered_page == f"<pre><code>{escaped_code}</code></pre>"


@pytest.mark.parametrize(
    "included_path",
    ["quickstart/missing.py", "../outside.py", "src/x.py", "rust/Cargo.toml", "rust/src/../x.rs"],
)
def test_an_include_outside_quickstart_or_missing_fails(tmp_path: Path, included_path: str) -> None:
    (tmp_path / "quickstart").mkdir()
    (tmp_path / "rust" / "src").mkdir(parents=True)
    (tmp_path / "rust" / "Cargo.toml").write_text("[package]\n")
    (tmp_path / "rust" / "x.rs").write_text("fn main() {}\n")
    with pytest.raises(SiteBuildError):
        render_page(f"<!-- include: {included_path} -->", repository_root=tmp_path)


def test_the_built_page_shows_exactly_the_python_snippet_ci_runs(tmp_path: Path) -> None:
    build_site(output_directory=tmp_path)
    page = (tmp_path / "index.html").read_text()
    code_blocks = [html.unescape(match["code"]) for match in CODE_BLOCK_PATTERN.finditer(page)]
    assert code_blocks == [PYTHON_SNIPPET.read_text()]


def test_the_page_is_one_path_from_a_token_to_a_key_with_a_time_target(tmp_path: Path) -> None:
    build_site(output_directory=tmp_path)
    page = (tmp_path / "index.html").read_text()
    assert "QRYPT_API_KEY" in page
    assert "under 10 minutes" in page
    assert page.index("Get a token") < page.index("Run the quickstart")


def test_every_copy_button_has_an_accessible_label(tmp_path: Path) -> None:
    build_site(output_directory=tmp_path)
    page = (tmp_path / "index.html").read_text()
    # The tabs are buttons too; their visible text is their accessible name.
    # One copy button for each language's program: Python, Node.js and Rust.
    copy_buttons = re.findall(r'<button[^>]*class="copy-button"[^>]*>', page)
    assert len(copy_buttons) == 3
    assert all('aria-label="Copy' in button for button in copy_buttons)
    assert (tmp_path / "copy.js").is_file()


NODE_SNIPPET: Final = REPOSITORY_ROOT / "quickstart" / "node" / "quickstart.mjs"
JAVASCRIPT_BLOCK_PATTERN: Final = re.compile(
    r'<pre[^>]*><code class="language-javascript">(?P<code>.*?)</code></pre>', re.DOTALL
)


def test_the_built_page_shows_exactly_the_node_snippet_ci_runs(tmp_path: Path) -> None:
    build_site(output_directory=tmp_path)
    page = (tmp_path / "index.html").read_text()
    code_blocks = [
        html.unescape(match["code"]) for match in JAVASCRIPT_BLOCK_PATTERN.finditer(page)
    ]
    assert code_blocks == [NODE_SNIPPET.read_text()]


def test_the_language_tabs_follow_the_aria_tabs_pattern(tmp_path: Path) -> None:
    build_site(output_directory=tmp_path)
    page = (tmp_path / "index.html").read_text()
    assert page.count('role="tablist"') == 1
    tabs = re.findall(r'<button[^>]*role="tab"[^>]*>', page)
    assert len(tabs) == 3
    controlled_ids = re.findall(r'role="tab"[^>]*aria-controls="([^"]+)"', page)
    assert len(controlled_ids) == 3
    for controlled_id in controlled_ids:
        assert re.search(rf'id="{controlled_id}"[^>]*role="tabpanel"', page)
    assert 'aria-selected="true"' in tabs[0]
    assert all('aria-selected="false"' in tab for tab in tabs[1:])


def test_no_panel_is_hidden_without_javascript(tmp_path: Path) -> None:
    build_site(output_directory=tmp_path)
    page = (tmp_path / "index.html").read_text()
    assert not re.search(r'role="tabpanel"[^>]*hidden', page)


def test_the_rust_quickstart_can_be_included_from_its_crate(tmp_path: Path) -> None:
    (tmp_path / "rust" / "src").mkdir(parents=True)
    (tmp_path / "rust" / "src" / "main.rs").write_text("fn main() {}\n")
    rendered_page = render_page("<!-- include: rust/src/main.rs -->", repository_root=tmp_path)
    assert rendered_page == "fn main() {}\n"


RUST_SNIPPET: Final = REPOSITORY_ROOT / "rust" / "src" / "main.rs"
RUST_BLOCK_PATTERN: Final = re.compile(
    r'<pre[^>]*><code class="language-rust">(?P<code>.*?)</code></pre>', re.DOTALL
)


def test_the_built_page_shows_exactly_the_rust_snippet_ci_runs(tmp_path: Path) -> None:
    build_site(output_directory=tmp_path)
    page = (tmp_path / "index.html").read_text()
    code_blocks = [html.unescape(match["code"]) for match in RUST_BLOCK_PATTERN.finditer(page)]
    assert code_blocks == [RUST_SNIPPET.read_text()]


def test_the_demo_video_is_published_with_the_site(tmp_path: Path) -> None:
    # The owner links the demo straight from the site, which serves it as a video that plays.
    build_site(output_directory=tmp_path)
    published_video = tmp_path / "demo.mp4"
    assert published_video.is_file()
    assert published_video.read_bytes() == (REPOSITORY_ROOT / "site" / "demo.mp4").read_bytes()
