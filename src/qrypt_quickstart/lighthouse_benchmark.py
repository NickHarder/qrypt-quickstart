"""Measure the quickstart site with Lighthouse, as the brief asks (RQ-20, RQ-21).

The brief's targets: the site loads in under 1.5 s at the 95th percentile on mobile, over 10 runs of
Lighthouse's mobile preset, and its accessibility score is at least 95, with the report committed.

This builds the site, serves it on localhost, and runs `web/`'s pinned Lighthouse 10 times on the
quickstart page with its default configuration (mobile emulation, simulated slow 4G and CPU
slowdown), plus once on the troubleshooting page. "Load" is Largest Contentful Paint: the moment the
page's main content is drawn. It writes `evidence/lighthouse/`: `runs.csv`, one row per run;
`summary.json`, the figures the brief's targets are judged on; and the last run's full HTML report
for each page.

Run `make lighthouse`. Lighthouse drives the Chromium build Playwright installed.
"""

import csv
import http.server
import json
import math
import os
import subprocess
import tempfile
import threading
from functools import partial
from pathlib import Path
from typing import Final

from playwright.sync_api import sync_playwright
from pydantic import BaseModel, ConfigDict

from .config import REPOSITORY_ROOT
from .site_builder import build_site

RUN_COUNT: Final = 10
LOAD_TARGET_MILLISECONDS: Final = 1500
ACCESSIBILITY_TARGET_SCORE: Final = 95
EVIDENCE_DIRECTORY: Final = REPOSITORY_ROOT / "evidence" / "lighthouse"
LIGHTHOUSE_BINARY: Final = REPOSITORY_ROOT / "web" / "node_modules" / ".bin" / "lighthouse"


class LighthouseRun(BaseModel):
    """The figures of one Lighthouse run that the brief's targets are judged on."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    page: str
    run_number: int
    accessibility_score: int
    performance_score: int
    first_contentful_paint_milliseconds: float
    largest_contentful_paint_milliseconds: float


class LighthouseSummary(BaseModel):
    """What the 10 runs show against the brief's two targets."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lighthouse_version: str
    run_count: int
    load_p95_milliseconds: float
    load_target_milliseconds: int
    lowest_accessibility_score: int
    accessibility_target_score: int
    meets_load_target: bool
    meets_accessibility_target: bool


def nearest_rank_percentile(values: list[float], percentile: float) -> float:
    """Return the nearest-rank percentile of a list of values.

    Args:
        values: The measured values; at least one.
        percentile: The percentile wanted, from 0 to 100.

    Returns:
        The smallest value at or above that share of the values.
    """
    ordered_values = sorted(values)
    rank = max(1, math.ceil(percentile / 100 * len(ordered_values)))
    return ordered_values[rank - 1]


def run_lighthouse(page_url: str, *, output_stem: Path, chrome_path: str) -> dict[str, object]:
    """Run Lighthouse once on a page and return its JSON report.

    Args:
        page_url: The page to measure.
        output_stem: The report's path without its suffix; `.report.json` and `.report.html` are
            written beside it.
        chrome_path: The Chromium executable Lighthouse drives.

    Returns:
        The parsed JSON report.
    """
    subprocess.run(  # noqa: S603  web/'s pinned Lighthouse, on a URL this module serves
        [
            str(LIGHTHOUSE_BINARY),
            page_url,
            "--only-categories=performance,accessibility",
            "--output=json",
            "--output=html",
            f"--output-path={output_stem}",
            "--chrome-flags=--headless=new --no-sandbox",
            "--quiet",
        ],
        check=True,
        env={**os.environ, "CHROME_PATH": chrome_path},
        timeout=180,
    )
    json_report = output_stem.with_suffix(".report.json")
    report: dict[str, object] = json.loads(json_report.read_text())
    json_report.unlink()  # the HTML report is the one kept; it holds the same figures
    return report


def figures_of(report: dict[str, object], *, page: str, run_number: int) -> LighthouseRun:
    """Pick the figures the targets are judged on out of a Lighthouse report."""
    categories = report["categories"]
    audits = report["audits"]
    assert isinstance(categories, dict)
    assert isinstance(audits, dict)
    return LighthouseRun(
        page=page,
        run_number=run_number,
        accessibility_score=round(categories["accessibility"]["score"] * 100),
        performance_score=round(categories["performance"]["score"] * 100),
        first_contentful_paint_milliseconds=audits["first-contentful-paint"]["numericValue"],
        largest_contentful_paint_milliseconds=audits["largest-contentful-paint"]["numericValue"],
    )


def main() -> None:
    """Build and serve the site, run Lighthouse, and write the evidence."""
    EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as site_directory, sync_playwright() as playwright:
        chrome_path = playwright.chromium.executable_path
        build_site(output_directory=Path(site_directory))
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=site_directory)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        runs: list[LighthouseRun] = []
        lighthouse_version = ""
        pages = [("index.html", number) for number in range(1, RUN_COUNT + 1)]
        for page, run_number in [*pages, ("troubleshooting.html", 1)]:
            output_stem = EVIDENCE_DIRECTORY / f"{page.removesuffix('.html')}-run"
            report = run_lighthouse(
                f"{base_url}/{page}", output_stem=output_stem, chrome_path=chrome_path
            )
            lighthouse_version = str(report["lighthouseVersion"])
            runs.append(figures_of(report, page=page, run_number=run_number))
            print(f"lighthouse: {page} run {run_number}: {runs[-1]}")  # noqa: T201  a command-line tool
        server.shutdown()
    quickstart_runs = [run for run in runs if run.page == "index.html"]
    load_p95 = nearest_rank_percentile(
        [run.largest_contentful_paint_milliseconds for run in quickstart_runs], 95
    )
    lowest_accessibility = min(run.accessibility_score for run in runs)
    summary = LighthouseSummary(
        lighthouse_version=lighthouse_version,
        run_count=len(quickstart_runs),
        load_p95_milliseconds=round(load_p95, 1),
        load_target_milliseconds=LOAD_TARGET_MILLISECONDS,
        lowest_accessibility_score=lowest_accessibility,
        accessibility_target_score=ACCESSIBILITY_TARGET_SCORE,
        meets_load_target=load_p95 < LOAD_TARGET_MILLISECONDS,
        meets_accessibility_target=lowest_accessibility >= ACCESSIBILITY_TARGET_SCORE,
    )
    with (EVIDENCE_DIRECTORY / "runs.csv").open("w", newline="") as runs_file:
        writer = csv.DictWriter(runs_file, fieldnames=list(LighthouseRun.model_fields))
        writer.writeheader()
        writer.writerows(run.model_dump() for run in runs)
    (EVIDENCE_DIRECTORY / "summary.json").write_text(summary.model_dump_json(indent=2) + "\n")
    print(f"lighthouse: {summary.model_dump_json()}")  # noqa: T201  a command-line tool


if __name__ == "__main__":
    main()
