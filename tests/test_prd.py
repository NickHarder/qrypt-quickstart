"""PRD.md has what the brief asks of the onboarding PRD, and its funnel is the one specification.

RQ-08: problem, personas and jobs-to-be-done, the five-stage funnel with a target and a measurement
for each stage, scope, out of scope, risks, and the tradeoff not made; an engineer can build the
instrumentation from it without a question. RQ-29: a busy engineering lead reads it in 10 minutes.

docs/KEY_METRICS.md holds the funnel's one specification; PRD.md shows it. These tests fail when
the two tables differ in any cell, so neither can drift from the other.
"""

import re
from pathlib import Path
from typing import Final

import pytest

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
PRD: Final = REPOSITORY_ROOT / "PRD.md"
KEY_METRICS: Final = REPOSITORY_ROOT / "docs" / "KEY_METRICS.md"
REQUIRED_SECTIONS: Final = [
    "## Problem",
    "## Personas and jobs to be done",
    "## The activation funnel",
    "## Metrics and instrumentation",
    "## Scope",
    "## Out of scope",
    "## Risks",
    "## The tradeoff we are not making",
]
WORD_LIMIT: Final = 2500
ASSUMED_FIGURES: Final = ["25%", "45 minutes", "400 signups", "$1,800"]


def table_rows(text: str, heading: str) -> list[list[str]]:
    section = text.split(heading, 1)[1]
    rows: list[list[str]] = []
    for line in section.splitlines()[1:]:
        if line.startswith("#") or (rows and not line.startswith("|")):
            break  # the first table under the heading ends at the first line that is not a row
        if line.startswith("|") and not line.startswith("|---"):
            rows.append([cell.strip() for cell in line.strip("|").split(" | ")])
    return rows[1:]


@pytest.mark.parametrize("section", REQUIRED_SECTIONS)
def test_the_prd_has_each_section_the_brief_asks_for(section: str) -> None:
    assert section in PRD.read_text()


def test_the_funnel_stages_match_the_key_metrics_cell_for_cell() -> None:
    specification = table_rows(KEY_METRICS.read_text(), "## Each stage")
    shown = table_rows(PRD.read_text(), "### Each stage")
    assert len(specification) == 5
    assert shown == specification


def test_the_rules_common_to_every_stage_match_too() -> None:
    def without_footnotes(rows: list[list[str]]) -> list[list[str]]:
        return [[re.sub(r"\[\^[\w-]+\]", "", cell) for cell in row] for row in rows]

    specification = table_rows(KEY_METRICS.read_text(), "## Common to every stage")
    shown = table_rows(PRD.read_text(), "### Common to every stage")
    assert len(specification) >= 6
    assert without_footnotes(shown) == without_footnotes(specification)


def test_each_stage_names_the_five_stages_of_the_brief_in_order() -> None:
    stages = [row[0] for row in table_rows(PRD.read_text(), "### Each stage")]
    assert stages == [
        "1. Landing",
        "2. Token created",
        "3. First successful call",
        "4. First key",
        "5. Return within 7 days",
    ]


@pytest.mark.parametrize("figure", ASSUMED_FIGURES)
def test_every_illustrative_figure_is_labelled_an_assumption(figure: str) -> None:
    lines_with_figure = [line for line in PRD.read_text().splitlines() if figure in line]
    assert lines_with_figure, f"the PRD never states {figure}"
    for line in lines_with_figure:
        assert "assum" in line.lower(), f"{figure} is not labelled an assumption: {line}"


def test_the_agent_metrics_are_specified_with_their_source() -> None:
    text = PRD.read_text()
    assert "at least 4 of 5" in text.lower()
    assert "10 minutes" in text
    assert "evidence/agent_runs.csv" in text


def test_a_busy_engineering_lead_reads_it_in_ten_minutes() -> None:
    word_count = len(PRD.read_text().split())
    assert word_count <= WORD_LIMIT, f"PRD.md is {word_count} words"
