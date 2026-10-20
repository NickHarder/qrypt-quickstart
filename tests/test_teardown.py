"""The competitive teardown compares the other API against this project's own funnel (RQ-41).

The brief asks to compare one other security or randomness API's quickstart "against your own
funnel criteria": the teardown must walk the five stages of docs/KEY_METRICS.md, and every fact it
states about the other API must come from a source it lists, read on a stated date.
"""

import re
from pathlib import Path
from typing import Final

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
TEARDOWN: Final = REPOSITORY_ROOT / "evidence" / "teardown.md"
KEY_METRICS: Final = REPOSITORY_ROOT / "docs" / "KEY_METRICS.md"


def funnel_stage_names() -> list[str]:
    rows = re.findall(r"^\| (\d)\. ([^|]+?) \| (?:NS|DR|GR)-\d+ \|", KEY_METRICS.read_text(), re.M)
    return [f"{number}. {name}" for number, name in rows]


def test_the_funnel_has_its_five_stages() -> None:
    assert len(funnel_stage_names()) == 5


def test_the_teardown_walks_every_stage_of_the_funnel() -> None:
    text = TEARDOWN.read_text()
    for stage in funnel_stage_names():
        assert f"| {stage} |" in text, f"the teardown has no row for {stage}"


def test_every_source_marker_names_a_listed_source_with_its_date() -> None:
    text = TEARDOWN.read_text()
    body, sources = text.split("## Sources", 1)
    used_markers = set(re.findall(r"\[(R\d+)\]", body))
    listed = dict(re.findall(r"^- \[(R\d+)\] (.+)$", sources, re.M))
    assert used_markers, "the teardown cites no source"
    assert used_markers <= set(listed), used_markers - set(listed)
    for marker, line in listed.items():
        assert "https://" in line, f"{marker} has no URL"
        assert re.search(r"20\d\d-\d\d-\d\d", line), f"{marker} has no date"


def test_it_says_what_this_project_takes_from_the_other_api() -> None:
    assert "## What to borrow" in TEARDOWN.read_text()
