"""Write a run's results: results.json for programs, summary.md for people, junit.xml for CI.

Each one opens with the versions that were under test (kit, commit, model, prompts, skills), so a
result is never separated from the prompt version that produced it. receipt.json says how the run
was started and which results it wrote, so that a number taken from the run can be attested.
"""

import hashlib
import json
from html import escape
from pathlib import Path
from typing import Final

from .models import CaseResult, RunResults

DIFFICULTIES: Final = ("straightforward", "ambiguous", "edge_case")
SHORT_HASH_LENGTH: Final = 12
NORTH_STAR_ID_PREFIX: Final = "NS-"
RESULTS_FILE_NAME: Final = "results.json"
RECEIPT_FILE_NAME: Final = "receipt.json"


def versions_line(results: RunResults) -> str:
    """Return the versions under test as one line, for a terminal or a log."""
    prompt_descriptions = (
        ", ".join(f"{prompt.name}@{prompt.version}" for prompt in results.versions.prompts)
        or "none"
    )
    skill_descriptions = (
        ", ".join(
            f"{skill_name}@{skill_version}"
            for skill_name, skill_version in sorted(results.versions.skills.items())
        )
        or "none"
    )
    return (
        f"versions: kit {results.versions.kit} | commit {results.versions.git_commit} | "
        f"model {results.model} | prompts {prompt_descriptions} | skills {skill_descriptions}"
    )


def totals_line(results: RunResults) -> str:
    """Return the run's totals as one line."""
    return (
        f"{len(results.cases)} cases: {results.passed_count} passed, {results.failed_count} failed"
    )


def case_prompts(case_result: CaseResult) -> str:
    """Return the prompt versions one case used, as `name@version` pairs."""
    return ", ".join(f"{prompt.name}@{prompt.version}" for prompt in case_result.prompts) or "none"


def metric_rows(results: RunResults) -> list[str]:
    """Return a table row for each metric a case feeds: its cases, how many passed, the rate.

    The north star comes first, then the others in the order of their ids.
    """
    metric_ids = sorted(
        {metric_id for case_result in results.cases for metric_id in case_result.metrics},
        key=lambda metric_id: (not metric_id.startswith(NORTH_STAR_ID_PREFIX), metric_id),
    )
    feeding_cases_by_metric_id = {
        metric_id: [
            case_result for case_result in results.cases if metric_id in case_result.metrics
        ]
        for metric_id in metric_ids
    }
    passed_count_by_metric_id = {
        metric_id: sum(1 for case_result in feeding_cases if case_result.status == "pass")
        for metric_id, feeding_cases in feeding_cases_by_metric_id.items()
    }
    return [
        "| "
        + " | ".join(
            [
                metric_id,
                str(len(feeding_cases)),
                str(passed_count_by_metric_id[metric_id]),
                f"{passed_count_by_metric_id[metric_id] / len(feeding_cases):.0%}",
            ]
        )
        + " |"
        for metric_id, feeding_cases in feeding_cases_by_metric_id.items()
    ]


def summary_markdown(results: RunResults, violations: list[str], notes: list[str]) -> str:
    """Return the human-readable summary of a run."""
    rows_by_metric = metric_rows(results)
    version_rows = [
        f"| kit | {results.versions.kit} |",
        f"| commit | {results.versions.git_commit} |",
        f"| model | {results.model} |",
        *[
            f"| prompt `{prompt.name}` | {prompt.version} "
            f"(`sha256:{prompt.sha256[:SHORT_HASH_LENGTH]}`) |"
            for prompt in results.versions.prompts
        ],
        *[
            f"| skill `{skill_name}` | {skill_version} |"
            for skill_name, skill_version in sorted(results.versions.skills.items())
        ],
    ]
    case_rows = [
        f"| {case_result.case_id} | {case_result.category} | {case_result.type} "
        f"| {case_result.tier} | {case_result.difficulty} | {case_result.status} "
        f"| {', '.join(case_result.guards)} | {', '.join(case_result.metrics)} "
        f"| {case_prompts(case_result)} "
        f"| {'; '.join(case_result.failures)} |"
        for case_result in results.cases
    ]
    categories = sorted({case_result.category for case_result in results.cases})
    coverage_rows = [
        "| "
        + " | ".join(
            [
                category,
                *[
                    str(
                        sum(
                            1
                            for case_result in results.cases
                            if case_result.category == category
                            and case_result.difficulty == difficulty
                        )
                    )
                    for difficulty in DIFFICULTIES
                ],
            ]
        )
        + " |"
        for category in categories
    ]
    summary_lines = [
        "# Eval results",
        "",
        f"**{totals_line(results)}** (mode {results.mode}, tier {results.tier})",
        "",
        "## Pass rate by metric (the north star first)",
        "",
        *(
            ["| Metric | Cases | Passed | Pass rate |", "|---|---|---|---|", *rows_by_metric]
            if rows_by_metric
            else ["No case names a metric yet."]
        ),
        "",
        "## Versions under test",
        "",
        "| What | Version |",
        "|---|---|",
        *version_rows,
        "",
        "## Violations",
        "",
        *([f"- {violation}" for violation in violations] or ["None."]),
        "",
        "## Notes against the baseline",
        "",
        *([f"- {note}" for note in notes] or ["None."]),
        "",
        "## Cases",
        "",
        "| Id | Category | Type | Tier | Difficulty | Status | Guards | Metrics | Prompts "
        "| Failures |",
        "|---|---|---|---|---|---|---|---|---|---|",
        *case_rows,
        "",
        "## Coverage (cases per category and difficulty; a 0 is a case to write next)",
        "",
        "| Category | " + " | ".join(DIFFICULTIES) + " |",
        "|---|" + "---|" * len(DIFFICULTIES),
        *coverage_rows,
        "",
    ]
    return "\n".join(summary_lines)


def xml_property(name: str, value: str) -> str:
    """Return one JUnit property element."""
    return f'<property name="{escape(name, quote=True)}" value="{escape(value, quote=True)}"/>'


def junit_xml(results: RunResults) -> str:
    """Return the run as JUnit XML, with the versions under test as properties."""
    suite_properties = [
        xml_property("kit", results.versions.kit),
        xml_property("git_commit", results.versions.git_commit),
        xml_property("model", results.model),
        *[
            xml_property(f"prompt.{prompt.name}", f"{prompt.version} sha256:{prompt.sha256}")
            for prompt in results.versions.prompts
        ],
        *[
            xml_property(f"skill.{skill_name}", skill_version)
            for skill_name, skill_version in sorted(results.versions.skills.items())
        ],
    ]
    testcase_elements: list[str] = []
    for case_result in results.cases:
        case_properties = "".join(
            xml_property(f"prompt.{prompt.name}", prompt.version) for prompt in case_result.prompts
        )
        failure_element = (
            f'<failure message="{escape("; ".join(case_result.failures), quote=True)}"/>'
            if case_result.status == "fail"
            else ""
        )
        testcase_elements.append(
            f'    <testcase classname="evals.{escape(case_result.category, quote=True)}" '
            f'name="{escape(case_result.case_id, quote=True)}">'
            f"<properties>{case_properties}</properties>{failure_element}</testcase>"
        )
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<testsuite name="evals" tests="{len(results.cases)}" failures="{results.failed_count}">',
        "  <properties>",
        *[f"    {suite_property}" for suite_property in suite_properties],
        "  </properties>",
        *testcase_elements,
        "</testsuite>",
        "",
    ]
    return "\n".join(xml_lines)


def write_reports(
    output_directory: Path, results: RunResults, violations: list[str], notes: list[str]
) -> None:
    """Write results.json, summary.md and junit.xml into the directory."""
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / RESULTS_FILE_NAME).write_text(
        results.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    (output_directory / "summary.md").write_text(
        summary_markdown(results, violations, notes), encoding="utf-8"
    )
    (output_directory / "junit.xml").write_text(junit_xml(results), encoding="utf-8")


def write_receipt(output_directory: Path, given_arguments: list[str]) -> None:
    """Write receipt.json beside results.json: how the run was started, and what it wrote.

    The receipt is what an attester reads (docs/references/attesters/). It holds the arguments the
    runner was given, the results file, and the hash of that file as it was written, so that a
    later edit of the results shows.
    """
    results_file = output_directory / RESULTS_FILE_NAME
    receipt = {
        "arguments": given_arguments,
        "results_file": results_file.as_posix(),
        "results_sha256": hashlib.sha256(results_file.read_bytes()).hexdigest(),
    }
    (output_directory / RECEIPT_FILE_NAME).write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
