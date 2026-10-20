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


@pytest.mark.parametrize("included_path", ["quickstart/missing.py", "../outside.py", "src/x.py"])
def test_an_include_outside_quickstart_or_missing_fails(tmp_path: Path, included_path: str) -> None:
    (tmp_path / "quickstart").mkdir()
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
    buttons = re.findall(r"<button[^>]*>", page)
    assert buttons
    assert all('aria-label="Copy' in button for button in buttons)
    assert (tmp_path / "copy.js").is_file()
