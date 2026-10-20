"""Every "get a token" link goes to the portal's sign-up page, tagged for the funnel (stage 1).

The brief names https://portal.qrypt.com/register, but the portal renders that as a 404
(2026-10-20); its login page's "Create trial account" leads to /trial, the working sign-up. The
PRD's attribution rests on the quickstart's links carrying `ref=quickstart`, which the portal
stores as `signup_ref`; a link without it would make stage 1 unmeasurable. This keeps the pages
and the PRD in agreement.

The links for someone without a token are the quickstart page's and the agent docs'. The
troubleshooting page's 401 fix is for someone who has an account and needs a new token, so it
links to the portal itself; the programs' printed messages name the portal's host only.
"""

import re
from pathlib import Path
from typing import Final

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
SITE: Final = REPOSITORY_ROOT / "site"
SIGN_UP_URL: Final = "https://portal.qrypt.com/trial?ref=quickstart"


def test_the_quickstart_pages_token_link_is_the_tagged_sign_up_page() -> None:
    page = (SITE / "index.html").read_text()
    links = re.findall(r'href="(https?://portal\.qrypt\.com[^"]*)"', page)
    assert links == [SIGN_UP_URL]


def test_the_agent_docs_send_people_to_the_same_page() -> None:
    for page_name in ("llms.md", "llms-full.md"):
        text = (SITE / page_name).read_text()
        assert SIGN_UP_URL in text, page_name
        # The programs' own messages, quoted in backticks, name the host only; everything else is
        # the tagged page.
        prose = re.sub(r"`[^`]*`", "", text)
        assert not re.search(r"portal\.qrypt\.com(?!/trial\?ref=quickstart)", prose), page_name


def test_the_prd_and_the_metrics_name_the_tag_the_links_carry() -> None:
    for document in (REPOSITORY_ROOT / "PRD.md", REPOSITORY_ROOT / "docs" / "KEY_METRICS.md"):
        assert "`ref=quickstart`" in document.read_text(), document.name


def test_the_claims_table_sources_the_sign_up_page() -> None:
    claims = (REPOSITORY_ROOT / "CLAIMS.md").read_text()
    assert "portal.qrypt.com/trial" in claims
    assert "/register as a 404" in claims
