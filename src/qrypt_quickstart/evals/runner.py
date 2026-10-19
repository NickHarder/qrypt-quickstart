"""Run the eval suite.

    --mode replay|record|live    replay (the default) answers from recordings: $0 and offline;
                                 record and live call the real model and cost money
    --tier core|all              core (the default) is the tier that must pass on every commit
    --compare-baseline           also fail on a case that passed in the baseline and fails now
    --out DIR                    write results.json, summary.md and junit.xml there
    --write-baseline             after a green run, record what the suite did
    --write-prompt-manifest      after a deliberate prompt version bump, pin the new text

Exit 0: every threshold holds and nothing regressed. Exit 1: a threshold failed or a case regressed.
Exit 2: the suite could not run (no cases, a bad case file, a missing recording).
"""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..config import REPOSITORY_ROOT
from ..prompts import all_prompts
from .baseline import (
    baseline_notes,
    baseline_violations,
    load_baseline,
    load_thresholds,
    threshold_violations,
    write_baseline,
    write_prompt_manifest,
)
from .cassette import load_cassette, save_cassette
from .clients import ModelClient, RecordingClient, ReplayClient
from .errors import CassetteMissError, EvalSetupError
from .loader import load_cases
from .models import CaseResult, EvalCase, RunResults
from .paths import EvalPaths, eval_paths
from .reporters import totals_line, versions_line, write_receipt, write_reports
from .scorers import score
from .target import build_live_client, run_target
from .versions import collect_versions

EXIT_GREEN: Final = 0
EXIT_RED: Final = 1
EXIT_COULD_NOT_RUN: Final = 2


@dataclass(frozen=True)
class CaseRun:
    """One case, and the model client its run must use."""

    case: EvalCase
    model_client: ModelClient


def parse_arguments(argument_list: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Run the eval suite.")
    parser.add_argument("--mode", choices=["replay", "record", "live"], default="replay")
    parser.add_argument("--tier", choices=["core", "all"], default="core")
    parser.add_argument("--compare-baseline", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--write-prompt-manifest", action="store_true")
    return parser.parse_args(argument_list)


def client_for(case: EvalCase, *, mode: str, model: str, paths: EvalPaths) -> ModelClient:
    """Return the model client one case's run uses in the given mode.

    Raises:
        CassetteMissError: In replay, if the case has no recording, or its recording was made
            with another model.
    """
    if mode == "replay":
        cassette = load_cassette(paths.cassettes_directory, case.case_id)
        if cassette.model != model:
            message = (
                f"cassette miss: {case.case_id} was recorded with model {cassette.model!r} "
                f"but evals/thresholds.yaml names {model!r}"
            )
            raise CassetteMissError(message)
        return ReplayClient(cassette)
    live_client = build_live_client(model)
    if mode == "record":
        return RecordingClient(case_id=case.case_id, model=model, live_client=live_client)
    return live_client


async def execute(case_runs: list[CaseRun], cassettes_directory: Path) -> list[CaseResult]:
    """Run each case through the system under test and score it, one after another.

    A recording is saved as soon as its case has run: each one was a paid call, and a later case
    that fails must not take it with it.
    """
    case_results: list[CaseResult] = []
    for case_run in case_runs:
        output = await run_target(case_run.case.input, case_run.model_client)
        if isinstance(case_run.model_client, RecordingClient):
            save_cassette(cassettes_directory, case_run.model_client.cassette())
        failures = score(case_run.case.expect, output)
        case_results.append(
            CaseResult(
                case_id=case_run.case.case_id,
                category=case_run.case.category,
                type=case_run.case.type,
                tier=case_run.case.tier,
                difficulty=case_run.case.difficulty,
                status="fail" if failures else "pass",
                failures=failures,
                prompts=output.prompts_used,
                guards=case_run.case.guards,
                metrics=case_run.case.metrics,
            )
        )
    return case_results


def print_report(results: RunResults, violations: list[str], notes: list[str]) -> None:
    """Print each case's verdict, the totals, and whatever made the run red."""
    for case_result in results.cases:
        verdict = "pass" if case_result.status == "pass" else "FAIL"
        failure_detail = f"  {'; '.join(case_result.failures)}" if case_result.failures else ""
        print(f"{case_result.case_id}  {verdict}{failure_detail}")
    print(totals_line(results))
    for note in notes:
        print(f"note: {note}")
    for violation in violations:
        print(f"VIOLATION {violation}", file=sys.stderr)
    if violations:
        # The first question about a red run is which prompt and which instructions produced it.
        print(versions_line(results), file=sys.stderr)


def run_suite(arguments: argparse.Namespace, given_arguments: list[str]) -> int:
    """Load the suite, run it, report, and return the exit code.

    `given_arguments` is the command line as it was typed, which the receipt of the run records.
    """
    paths = eval_paths(REPOSITORY_ROOT)
    prompts = all_prompts()
    if arguments.write_prompt_manifest:
        write_prompt_manifest(paths.prompt_manifest_file, prompts)
        print(f"wrote {paths.prompt_manifest_file}")
        return EXIT_GREEN

    thresholds = load_thresholds(paths.thresholds_file)
    selected_cases = [
        case for case in load_cases(paths.cases_directory) if arguments.tier in ("all", case.tier)
    ]
    if not selected_cases:
        message = f"no eval cases in tier {arguments.tier!r}; an empty run proves nothing"
        raise EvalSetupError(message)

    case_runs = [
        CaseRun(
            case=case,
            model_client=client_for(case, mode=arguments.mode, model=thresholds.model, paths=paths),
        )
        for case in selected_cases
    ]
    case_results = asyncio.run(execute(case_runs, paths.cassettes_directory))

    results = RunResults(
        mode=arguments.mode,
        tier=arguments.tier,
        model=thresholds.model,
        versions=collect_versions(paths.repository_root, prompts),
        cases=case_results,
    )
    baseline = load_baseline(paths.baseline_file) if arguments.compare_baseline else {}
    violations = [
        *threshold_violations(results, thresholds),
        *baseline_violations(results, baseline),
    ]
    notes = baseline_notes(results, baseline) if arguments.compare_baseline else []
    print_report(results, violations, notes)
    if arguments.out is not None:
        write_reports(arguments.out, results, violations, notes)
        write_receipt(arguments.out, given_arguments)
        print(f"wrote results.json, summary.md, junit.xml and receipt.json to {arguments.out}")

    if arguments.write_baseline:
        if violations or results.failed_count:
            print("the baseline is written only from a green run; this run is red", file=sys.stderr)
            return EXIT_RED
        write_baseline(paths.baseline_file, results)
        print(f"wrote {paths.baseline_file}")
    return EXIT_RED if violations else EXIT_GREEN


def main(argument_list: list[str] | None = None) -> int:
    """Run the suite from the command line and return the process exit code."""
    given_arguments = sys.argv[1:] if argument_list is None else argument_list
    arguments = parse_arguments(given_arguments)
    try:
        return run_suite(arguments, given_arguments)
    except (EvalSetupError, NotImplementedError) as error:
        print(f"runner error: {error}", file=sys.stderr)
        if isinstance(error, CassetteMissError):
            print(
                "A cassette miss means a request to the model changed (a prompt, the model id or a "
                "case's input) and no recording matches it. Undo the change, or record the case "
                "again (that costs money) and commit the recording in the same change.",
                file=sys.stderr,
            )
        return EXIT_COULD_NOT_RUN
