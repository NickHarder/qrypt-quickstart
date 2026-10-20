"""Every factual claim on the site about Qrypt is traceable to a source (RQ-16, RQ-24).

CLAIMS.md is the claims-to-source table. Each row quotes the site word for word and names the page
it is on and the source it rests on. These tests hold the table and the site to each other: a quote
that is no longer on its page fails, a Qrypt fact on the site that no row quotes fails, and a
marketing superlative anywhere on the site fails.
"""

import html
import re
from pathlib import Path
from typing import Final

import pytest

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
CLAIMS_TABLE: Final = REPOSITORY_ROOT / "CLAIMS.md"
SITE_PAGES: Final = sorted((REPOSITORY_ROOT / "site").glob("*.html")) + sorted(
    (REPOSITORY_ROOT / "site").glob("*.md")
)
ROW_PATTERN: Final = re.compile(
    r"^\| (?P<id>Q-\d{2}) \| (?P<quote>.+?) \| `(?P<page>site/[^`]+)` \| (?P<source>.+?) \|"
)
# Facts about Qrypt the site states; each one, where it appears, must be quoted by some row.
QRYPT_FACT_MARKERS: Final = [
    "api-eus.qrypt.com",
    "application/json",
    "1 to 512",
    "1,024 bytes",
    "30 requests",
    "allotment",
    "invalid or expired",
    "entropy supply",
    "Entropy service",
    "portal.qrypt.com",
    "C/C++",
]
SUPERLATIVES: Final = [
    "unbreakable",
    "unhackable",
    "perfectly secure",
    "100% secure",
    "military-grade",
    "guaranteed",
    "truly random",
    "quantum-proof",
    "best-in-class",
    "world-class",
]


def page_text(page: Path) -> str:
    text = page.read_text()
    without_tags = re.sub(r"<[^>]+>", "", text) if page.suffix == ".html" else text
    return " ".join(html.unescape(without_tags).replace("`", "").split())


def claim_rows() -> list[re.Match[str]]:
    return [
        match
        for line in CLAIMS_TABLE.read_text().splitlines()
        if (match := ROW_PATTERN.match(line))
    ]


def test_the_table_has_rows_with_unique_ids() -> None:
    claim_ids = [row["id"] for row in claim_rows()]
    assert len(claim_ids) >= 15
    assert len(claim_ids) == len(set(claim_ids))


@pytest.mark.parametrize("row", claim_rows(), ids=lambda row: row["id"])
def test_each_quote_is_on_the_page_it_names_and_has_a_source(row: re.Match[str]) -> None:
    quote = " ".join(row["quote"].replace("`", "").split())
    assert quote in page_text(REPOSITORY_ROOT / row["page"]), f"{row['id']} is not on its page"
    assert row["source"].strip(), f"{row['id']} names no source"


@pytest.mark.parametrize("marker", QRYPT_FACT_MARKERS)
def test_each_qrypt_fact_the_site_states_is_quoted_by_a_row(marker: str) -> None:
    quotes = " ".join(row["quote"] for row in claim_rows())
    pages_with_marker = [page for page in SITE_PAGES if marker in page_text(page)]
    if pages_with_marker:
        assert marker in quotes, f"the site says {marker!r} but no claim quotes it"


@pytest.mark.parametrize("page", SITE_PAGES, ids=lambda page: page.name)
def test_no_page_uses_a_marketing_superlative(page: Path) -> None:
    lowered_text = page_text(page).lower()
    for superlative in SUPERLATIVES:
        assert superlative not in lowered_text, f"{page.name} says {superlative!r}"


def test_the_table_reports_how_many_ai_drafted_claims_were_corrected() -> None:
    text = CLAIMS_TABLE.read_text()
    match = re.search(
        r"\*\*(\d+) AI-drafted claims checked: (\d+) verified, (\d+) relabelled", text
    )
    assert match, "CLAIMS.md does not state the fact-check count"
    checked, verified, relabelled = (int(group) for group in match.groups())
    corrected = re.search(r"(\d+) corrected or dropped\*\*", text)
    assert corrected
    assert checked == verified + relabelled + int(corrected[1])
    fact_check_rows = re.findall(r"^\| A-\d{2} \|", text, re.MULTILINE)
    assert len(fact_check_rows) == checked
