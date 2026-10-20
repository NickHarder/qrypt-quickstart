"""The built site in a real browser: keyboard only, copy buttons, and 200% zoom (RQ-18).

Playwright drives Chromium against the site built into a temporary folder and served on localhost.
"""

import http.server
import threading
from collections.abc import Iterator
from functools import partial
from pathlib import Path
from typing import Final

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from qrypt_quickstart.site_builder import build_site

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
DESKTOP_WIDTH_PIXELS: Final = 1280
# At 200% zoom a 1280-pixel window lays the page out in 640 CSS pixels.
ZOOMED_WIDTH_PIXELS: Final = DESKTOP_WIDTH_PIXELS // 2


@pytest.fixture(scope="module")
def site_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    site_directory = tmp_path_factory.mktemp("built-site")
    build_site(output_directory=site_directory)
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(site_directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    serving_thread = threading.Thread(target=server.serve_forever, daemon=True)
    serving_thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="module")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        launched_browser = playwright.chromium.launch()
        yield launched_browser
        launched_browser.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport={"width": DESKTOP_WIDTH_PIXELS, "height": 900})
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    opened_page = context.new_page()
    yield opened_page
    context.close()


def test_the_language_tabs_work_with_the_keyboard_alone(page: Page, site_url: str) -> None:
    page.goto(f"{site_url}/index.html")
    page.focus("#tab-python")
    page.keyboard.press("ArrowRight")
    assert page.evaluate("document.activeElement.id") == "tab-node"
    assert page.get_attribute("#tab-node", "aria-selected") == "true"
    assert page.is_visible("#panel-node")
    assert page.is_hidden("#panel-python")
    page.keyboard.press("Home")
    assert page.is_visible("#panel-python")


def test_every_interactive_element_is_reached_by_tab_and_shows_focus(
    page: Page, site_url: str
) -> None:
    page.goto(f"{site_url}/index.html")
    focused_ids: set[str] = set()
    for _press in range(40):
        page.keyboard.press("Tab")
        focused = page.evaluate(
            "({id: document.activeElement.id,"
            " label: document.activeElement.getAttribute('aria-label'),"
            " outline: getComputedStyle(document.activeElement).outlineStyle})"
        )
        if focused["id"] or focused["label"]:
            focused_ids.add(focused["id"] or focused["label"])
            assert focused["outline"] != "none", f"{focused} shows no focus"
    assert "tab-python" in focused_ids
    assert "Copy the Python quickstart" in focused_ids


def test_a_copy_button_copies_its_snippet_and_says_so(page: Page, site_url: str) -> None:
    page.goto(f"{site_url}/index.html")
    page.focus("button[aria-label='Copy the Python quickstart']")
    page.keyboard.press("Enter")
    page.wait_for_function("document.querySelector('.copy-status').textContent.length > 0")
    copied_text = page.evaluate("navigator.clipboard.readText()")
    snippet = (REPOSITORY_ROOT / "quickstart" / "python" / "quickstart.py").read_text()
    assert copied_text == snippet
    assert "Copied" in page.inner_text(".copy-status")


@pytest.mark.parametrize("page_name", ["index.html", "troubleshooting.html"])
def test_code_reads_without_sideways_scrolling_at_200_percent_zoom(
    browser: Browser, site_url: str, page_name: str
) -> None:
    context = browser.new_context(viewport={"width": ZOOMED_WIDTH_PIXELS, "height": 450})
    zoomed_page = context.new_page()
    zoomed_page.goto(f"{site_url}/{page_name}")
    overflowing_blocks = zoomed_page.evaluate(
        "[...document.querySelectorAll('pre')]"
        ".filter(block => block.scrollWidth > block.clientWidth + 1).length"
    )
    page_overflows = zoomed_page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
    )
    context.close()
    assert overflowing_blocks == 0
    assert not page_overflows
