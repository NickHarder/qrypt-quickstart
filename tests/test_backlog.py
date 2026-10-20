"""BACKLOG.csv and BACKLOG.md: ten follow-up items, each RICE-scored with its evidence (RQ-10).

The brief asks for ten items drawn from the agent-readiness findings and a review of the first-run
experience, each with a RICE score and the evidence behind it. These tests hold the sheet to its
own arithmetic and to Intercom's RICE scales, make every evidence link lead to a committed file,
and keep `BACKLOG.md`'s ranking equal to the sheet's.
"""

import csv
import re
from pathlib import Path
from typing import Final

import pytest

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
SHEET: Final = REPOSITORY_ROOT / "BACKLOG.csv"
REPORT: Final = REPOSITORY_ROOT / "BACKLOG.md"
ITEM_COUNT: Final = 10
# RQ-29: a busy engineering lead reads it in 10 minutes, the PRD's own cap (tests/test_prd.py).
WORD_LIMIT: Final = 2500
# Intercom's RICE scales: impact from minimal to massive, confidence from low to high.
IMPACT_SCALE: Final = {0.25, 0.5, 1.0, 2.0, 3.0}
CONFIDENCE_PERCENT_SCALE: Final = {50, 80, 100}
# One ranked row of BACKLOG.md's table: | 1 | B-01 | ... | 1,600 |
REPORT_ROW: Final = re.compile(
    r"^\| (?P<rank>\d+) \| (?P<item_id>B-\d{2}) \|.*\| (?P<rice_score>[\d,.]+) \|$", re.MULTILINE
)


def backlog_items() -> list[dict[str, str]]:
    """Return every row of the backlog sheet."""
    with SHEET.open(newline="") as sheet_file:
        return list(csv.DictReader(sheet_file))


def test_the_sheet_has_ten_items_with_unique_ids() -> None:
    item_ids = [item["item_id"] for item in backlog_items()]
    assert len(item_ids) == ITEM_COUNT
    assert len(set(item_ids)) == ITEM_COUNT


@pytest.mark.parametrize("item", backlog_items(), ids=lambda item: item["item_id"])
def test_each_score_is_its_own_rice_arithmetic_on_rices_scales(item: dict[str, str]) -> None:
    reach_per_quarter = int(item["reach_per_quarter"])
    impact = float(item["impact"])
    confidence_percent = int(item["confidence_percent"])
    effort_person_weeks = float(item["effort_person_weeks"])
    assert reach_per_quarter > 0
    assert impact in IMPACT_SCALE
    assert confidence_percent in CONFIDENCE_PERCENT_SCALE
    assert effort_person_weeks > 0
    computed_score = reach_per_quarter * impact * confidence_percent / 100 / effort_person_weeks
    assert float(item["rice_score"]) == round(computed_score, 1)


@pytest.mark.parametrize("item", backlog_items(), ids=lambda item: item["item_id"])
def test_each_item_names_its_reach_basis_its_owner_and_evidence_that_exists(
    item: dict[str, str],
) -> None:
    assert item["reach_basis"].strip()
    assert item["fix_owner"] in {"Qrypt", "This project"}
    evidence_paths = [path.strip() for path in item["evidence"].split(";")]
    assert evidence_paths
    for evidence_path in evidence_paths:
        assert (REPOSITORY_ROOT / evidence_path).is_file(), f"{item['item_id']}: {evidence_path}"


def test_the_sheet_is_ranked_by_score() -> None:
    items = backlog_items()
    scores = [float(item["rice_score"]) for item in items]
    assert scores == sorted(scores, reverse=True)
    assert [int(item["rank"]) for item in items] == list(range(1, ITEM_COUNT + 1))


def test_the_report_lists_the_sheets_items_in_its_order_with_its_scores() -> None:
    report_rows = list(REPORT_ROW.finditer(REPORT.read_text()))
    sheet_rows = [
        (item["rank"], item["item_id"], float(item["rice_score"])) for item in backlog_items()
    ]
    listed_rows = [
        (row["rank"], row["item_id"], float(row["rice_score"].replace(",", "")))
        for row in report_rows
    ]
    assert listed_rows == sheet_rows


def test_the_report_says_its_reach_rests_on_the_prds_assumption() -> None:
    report_text = REPORT.read_text()
    assert "400 signups a quarter" in report_text
    assert "assumption" in report_text


def test_a_busy_engineering_lead_reads_it_in_ten_minutes() -> None:
    word_count = len(REPORT.read_text().split())
    assert word_count <= WORD_LIMIT, f"{REPORT.name} is {word_count} words"
