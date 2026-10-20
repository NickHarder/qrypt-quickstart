"""The committed Lighthouse evidence meets the brief's targets (RQ-20, RQ-21).

`make lighthouse` writes evidence/lighthouse/; these tests read what was committed, so a re-run that
misses a target, or a summary that disagrees with its runs, fails the gate.
"""

import csv
import json
from pathlib import Path
from typing import Final

from qrypt_quickstart.lighthouse_benchmark import (
    ACCESSIBILITY_TARGET_SCORE,
    LOAD_TARGET_MILLISECONDS,
    RUN_COUNT,
    nearest_rank_percentile,
)

EVIDENCE: Final = Path(__file__).resolve().parents[1] / "evidence" / "lighthouse"


def test_the_nearest_rank_p95_of_ten_values_is_the_largest() -> None:
    assert nearest_rank_percentile([float(value) for value in range(1, 11)], 95) == 10.0
    assert nearest_rank_percentile([5.0], 95) == 5.0


def test_ten_mobile_runs_of_the_quickstart_page_were_committed() -> None:
    with (EVIDENCE / "runs.csv").open() as runs_file:
        runs = list(csv.DictReader(runs_file))
    assert len([run for run in runs if run["page"] == "index.html"]) == RUN_COUNT
    assert (EVIDENCE / "index-run.report.html").is_file()
    assert (EVIDENCE / "troubleshooting-run.report.html").is_file()


def test_the_summary_agrees_with_the_runs_and_meets_both_targets() -> None:
    with (EVIDENCE / "runs.csv").open() as runs_file:
        runs = list(csv.DictReader(runs_file))
    summary = json.loads((EVIDENCE / "summary.json").read_text())
    loads = [
        float(run["largest_contentful_paint_milliseconds"])
        for run in runs
        if run["page"] == "index.html"
    ]
    assert summary["load_p95_milliseconds"] == round(nearest_rank_percentile(loads, 95), 1)
    assert summary["lowest_accessibility_score"] == min(
        int(run["accessibility_score"]) for run in runs
    )
    assert summary["load_p95_milliseconds"] < LOAD_TARGET_MILLISECONDS
    assert summary["lowest_accessibility_score"] >= ACCESSIBILITY_TARGET_SCORE
