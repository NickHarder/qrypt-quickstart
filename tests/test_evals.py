from pathlib import Path
from typing import Final

import pytest

from qrypt_quickstart.config import REPOSITORY_ROOT
from qrypt_quickstart.evals.baseline import (
    load_baseline,
    load_thresholds,
)
from qrypt_quickstart.evals.cassette import cassette_file
from qrypt_quickstart.evals.errors import EvalSetupError
from qrypt_quickstart.evals.loader import (
    load_case,
    load_cases,
)
from qrypt_quickstart.evals.models import (
    CaseResult,
    Expectation,
    RunResults,
    TargetOutput,
    Versions,
)
from qrypt_quickstart.evals.paths import eval_paths
from qrypt_quickstart.evals.reporters import metric_rows
from qrypt_quickstart.evals.scorers import score

EVAL_PATHS: Final = eval_paths(REPOSITORY_ROOT)


def test_every_case_file_is_a_valid_case_with_a_unique_id() -> None:
    assert load_cases(EVAL_PATHS.cases_directory)


def test_every_core_case_has_a_recording_so_the_gate_can_replay_it() -> None:
    core_case_ids = [
        case.case_id for case in load_cases(EVAL_PATHS.cases_directory) if case.tier == "core"
    ]
    assert core_case_ids, "the core tier is empty; the gate would have nothing to run"
    cases_without_a_recording = [
        case_id
        for case_id in core_case_ids
        if not cassette_file(EVAL_PATHS.cassettes_directory, case_id).exists()
    ]
    assert not cases_without_a_recording


def test_the_baseline_names_only_cases_that_exist() -> None:
    known_case_ids = {case.case_id for case in load_cases(EVAL_PATHS.cases_directory)}
    assert set(load_baseline(EVAL_PATHS.baseline_file)) <= known_case_ids


def test_thresholds_load() -> None:
    assert load_thresholds(EVAL_PATHS.thresholds_file).model


def test_a_case_with_an_unknown_field_is_rejected(tmp_path: Path) -> None:
    case_file = tmp_path / "X-01.yaml"
    case_file.write_text(
        "id: X-01\ncategory: demo\ntype: invariant\nstatement: s\nfailure_mode: f\n"
        "input: {prompt: p}\nexpect: {contians: [typo]}\n"
    )
    with pytest.raises(EvalSetupError, match="contians"):
        load_case(case_file)


def test_a_case_names_what_it_guards_and_the_metrics_it_feeds(tmp_path: Path) -> None:
    case_file = tmp_path / "X-01.yaml"
    case_file.write_text(
        "id: X-01\ncategory: demo\ntype: invariant\nstatement: s\nfailure_mode: f\n"
        "input: {prompt: p}\nexpect: {contains: [word]}\nguards: [UC-01]\nmetrics: [NS-01, DR-02]\n"
    )
    loaded_case = load_case(case_file)
    assert loaded_case.guards == ["UC-01"]
    assert loaded_case.metrics == ["NS-01", "DR-02"]


def traced_result(case_id: str, status: str, metric_ids: list[str]) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        category="demo",
        type="invariant",
        tier="core",
        difficulty="straightforward",
        status="pass" if status == "pass" else "fail",
        failures=[],
        prompts=[],
        metrics=metric_ids,
    )


def test_the_pass_rate_is_given_by_metric_with_the_north_star_first() -> None:
    results = RunResults(
        mode="replay",
        tier="all",
        model=load_thresholds(EVAL_PATHS.thresholds_file).model,
        versions=Versions(kit="unknown", git_commit="unknown", skills={}, prompts=[]),
        cases=[
            traced_result("X-01", "pass", ["DR-02", "NS-01"]),
            traced_result("X-02", "fail", ["NS-01"]),
            traced_result("X-03", "pass", []),
        ],
    )
    assert metric_rows(results) == ["| NS-01 | 2 | 1 | 50% |", "| DR-02 | 1 | 1 | 100% |"]


def test_the_floors_of_the_trace_ship_switched_off() -> None:
    floors = load_thresholds(EVAL_PATHS.thresholds_file).trace
    assert not any(floors.model_dump().values())


def test_an_empty_suite_is_an_error_not_a_pass(tmp_path: Path) -> None:
    with pytest.raises(EvalSetupError, match="no eval cases"):
        load_cases(tmp_path)


def test_scorer_passes_an_answer_that_meets_the_expectation() -> None:
    expectation = Expectation(contains=["1,284.50"], must_not_contain=["1,285"])
    assert score(expectation, TargetOutput(text="It was 1,284.50 EUR.")) == []


def test_scorer_reports_each_way_an_answer_falls_short() -> None:
    expectation = Expectation(contains=["1,284.50"], must_not_contain=["about"], refuses=True)
    failures = score(expectation, TargetOutput(text="about 1,285"))
    assert len(failures) == 3


def test_scorer_does_not_pass_an_empty_answer() -> None:
    assert score(Expectation(must_not_contain=["anything"]), TargetOutput(text=""))
