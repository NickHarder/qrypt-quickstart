"""AGENT_READINESS.md reports what evidence/agent_runs.csv logged, and nothing else (RQ-09, RQ-23).

The brief's agent-readiness test: 5 fresh runs, a doc revision, 5 more, each run with its result,
wall-clock time and failure reason. These tests hold the log to that shape, keep the report's
summary table equal to the log, keep every failed run in the report's taxonomy with the commit
that addressed it, and keep the run's token out of every transcript.
"""

import csv
import re
import statistics
from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.mock_server import SUCCESS_TOKEN

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
REPORT: Final = REPOSITORY_ROOT / "AGENT_READINESS.md"
RUN_LOG: Final = REPOSITORY_ROOT / "evidence" / "agent_runs.csv"
TRANSCRIPTS: Final = REPOSITORY_ROOT / "evidence" / "transcripts"
# Round 2 ran twice on the revised docs: against the mock, then against Qrypt ("2-live").
ROUNDS: Final = ["1", "2", "2-live"]
RUNS_PER_ROUND: Final = 5
# RQ-29: a busy engineering lead reads it in 10 minutes, the PRD's own cap (tests/test_prd.py).
WORD_LIMIT: Final = 2500
# One row of the report's summary table: | Round 1 | 5 of 5 | 0.49 | ...
SUMMARY_ROW: Final = re.compile(
    r"^\| Round (?P<round_name>[\w-]+) \| (?P<succeeded>\d) of (?P<runs>\d)"
    r" \| (?P<median>[\d.]+) \|",
    re.MULTILINE,
)
# A failed run is named in the taxonomy as `round-run`, with a commit of 7 to 40 hex digits.
TAXONOMY_ROW: Final = re.compile(
    r"^\| `(?P<run>\d-\d)` \|.*`(?P<commit>[0-9a-f]{7,40})`", re.MULTILINE
)


def logged_runs() -> list[dict[str, str]]:
    """Return every row of the agent-readiness log."""
    with RUN_LOG.open(newline="") as log_file:
        return list(csv.DictReader(log_file))


def runs_of_round(round_name: str) -> list[dict[str, str]]:
    """Return the log's rows for one round."""
    return [run for run in logged_runs() if run["round_name"] == round_name]


@pytest.mark.parametrize("round_name", ROUNDS)
def test_each_round_has_five_runs_each_with_a_time_a_result_and_a_category(
    round_name: str,
) -> None:
    runs = runs_of_round(round_name)
    assert [int(run["run_number"]) for run in runs] == list(range(1, RUNS_PER_ROUND + 1))
    for run in runs:
        assert float(run["wall_clock_minutes"]) > 0
        assert run["succeeded"] in {"True", "False"}
        has_category = bool(run["failure_category"])
        assert has_category == (run["succeeded"] == "False"), f"run {run['run_number']}"


@pytest.mark.parametrize("round_name", ROUNDS)
def test_the_reports_success_count_and_median_equal_the_logs(round_name: str) -> None:
    runs = runs_of_round(round_name)
    summary_rows = {row["round_name"]: row for row in SUMMARY_ROW.finditer(REPORT.read_text())}
    summary_row = summary_rows[round_name]
    successful_minutes = [
        float(run["wall_clock_minutes"]) for run in runs if run["succeeded"] == "True"
    ]
    assert int(summary_row["succeeded"]) == len(successful_minutes)
    assert int(summary_row["runs"]) == len(runs)
    median_minutes = statistics.median(successful_minutes)
    assert summary_row["median"] == f"{median_minutes:.2f}"


def test_the_revised_round_meets_the_briefs_bar() -> None:
    revised_runs = runs_of_round("2")
    successes = [run for run in revised_runs if run["succeeded"] == "True"]
    assert len(successes) >= 4
    assert statistics.median(float(run["wall_clock_minutes"]) for run in successes) <= 10


def test_the_live_round_meets_the_briefs_bar_against_qrypt() -> None:
    live_runs = runs_of_round("2-live")
    assert {run["target"] for run in live_runs} == {"live"}
    successes = [run for run in live_runs if run["succeeded"] == "True"]
    assert len(successes) >= 4
    assert statistics.median(float(run["wall_clock_minutes"]) for run in successes) <= 10


def test_every_failed_run_is_in_the_taxonomy_with_the_commit_that_addressed_it() -> None:
    taxonomy = {row["run"]: row["commit"] for row in TAXONOMY_ROW.finditer(REPORT.read_text())}
    for run in logged_runs():
        if run["succeeded"] == "False":
            assert f"{run['round_name']}-{run['run_number']}" in taxonomy


@pytest.mark.parametrize("round_name", ROUNDS)
def test_no_transcript_holds_the_runs_token(round_name: str) -> None:
    for run_number in range(1, RUNS_PER_ROUND + 1):
        transcript = (TRANSCRIPTS / f"{round_name}-run-{run_number}.txt").read_text()
        assert SUCCESS_TOKEN not in transcript, f"{round_name}-run-{run_number}"


def test_a_busy_engineering_lead_reads_it_in_ten_minutes() -> None:
    word_count = len(REPORT.read_text().split())
    assert word_count <= WORD_LIMIT, f"{REPORT.name} is {word_count} words"
