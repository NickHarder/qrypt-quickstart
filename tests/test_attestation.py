import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

from qrypt_quickstart.config import REPOSITORY_ROOT
from qrypt_quickstart.evals.paths import eval_paths
from qrypt_quickstart.evals.runner import main

EVAL_PATHS: Final = eval_paths(REPOSITORY_ROOT)
ATTESTER_FILE: Final = EVAL_PATHS.repository_root / "docs/references/attesters/eval_results.py"
CORE: Final = {"tier": "core"}


def load_attester() -> ModuleType:
    module_spec = importlib.util.spec_from_file_location("eval_results_attester", ATTESTER_FILE)
    assert module_spec is not None
    assert module_spec.loader is not None
    attester_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(attester_module)
    return attester_module


ATTESTER: Final = load_attester()


class Run:
    """One replay of the core tier: the computation that was run, its receipt and its results."""

    def __init__(self, output_directory: Path) -> None:
        self.computation: Final = (
            f"evals --mode replay --tier {{tier}} --compare-baseline --out {output_directory}"
        )
        self.receipt_file: Final = output_directory / "receipt.json"
        self.results_file: Final = output_directory / "results.json"

    def receipt(self) -> dict[str, Any]:
        loaded_receipt: dict[str, Any] = json.loads(self.receipt_file.read_text())
        return loaded_receipt

    def verdict(
        self, claimed_rate: object, parameters: dict[str, str] | None = None
    ) -> dict[str, Any]:
        returned_verdict: dict[str, Any] = ATTESTER.attest(
            computation=self.computation,
            parameters=CORE if parameters is None else parameters,
            receipt=self.receipt(),
            claimed_value=claimed_rate,
        )
        return returned_verdict

    def rewrite_results(self, new_results: dict[str, Any]) -> None:
        """Replace the results and write a receipt that matches them, as a second run would."""
        self.results_file.write_text(json.dumps(new_results))
        matching_receipt = {
            **self.receipt(),
            "results_sha256": hashlib.sha256(self.results_file.read_bytes()).hexdigest(),
        }
        self.receipt_file.write_text(json.dumps(matching_receipt))


@pytest.fixture
def replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Run:
    monkeypatch.chdir(EVAL_PATHS.repository_root)
    output_directory = tmp_path / "out"
    arguments = ["--mode", "replay", "--tier", "core", "--compare-baseline", "--out"]
    assert main([*arguments, str(output_directory)]) == 0
    return Run(output_directory)


def test_the_rate_the_replay_measured_is_attested(replay: Run) -> None:
    verdict = replay.verdict(1.0)
    assert verdict["ok"], verdict
    assert verdict["details"]["cases"] == verdict["details"]["passed"]


# A claimed rate that the run did not measure.
def test_another_number_is_refused(replay: Run) -> None:
    verdict = replay.verdict(0.5)
    assert not verdict["ok"]
    assert "the claimed rate is not the measured one" in verdict["reason"]


# A run of another tier than the one the number is claimed for.
def test_a_run_of_another_tier_is_refused(replay: Run) -> None:
    verdict = replay.verdict(1.0, {"tier": "all"})
    assert not verdict["ok"]
    assert "not the sanctioned run" in verdict["reason"]


# A parameter value that brings words of its own into the run: here, a second tier.
def test_a_parameter_that_adds_words_to_the_run_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(EVAL_PATHS.repository_root)
    output_directory = tmp_path / "out"
    arguments = ["--mode", "replay", "--tier", "core", "--tier", "all", "--compare-baseline"]
    assert main([*arguments, "--out", str(output_directory)]) == 0
    verdict = Run(output_directory).verdict(1.0, {"tier": "core --tier all"})
    assert not verdict["ok"]
    assert "not the sanctioned run" in verdict["reason"]


# The results changed after the receipt was written.
def test_results_edited_after_the_run_are_refused(replay: Run) -> None:
    replay.results_file.write_text(replay.results_file.read_text() + "\n")
    verdict = replay.verdict(1.0)
    assert not verdict["ok"]
    assert "changed after the receipt was written" in verdict["reason"]


# A prompt text that is not the pinned one.
def test_a_run_on_a_prompt_that_is_not_the_pinned_one_is_refused(replay: Run) -> None:
    results: dict[str, Any] = json.loads(replay.results_file.read_text())
    results["versions"]["prompts"][0]["sha256"] = "0" * 64
    replay.rewrite_results(results)
    verdict = replay.verdict(1.0)
    assert not verdict["ok"]
    assert "not the pinned one" in verdict["reason"]


# A run that was not a replay.
def test_a_run_that_called_a_model_is_refused(replay: Run) -> None:
    results: dict[str, Any] = json.loads(replay.results_file.read_text())
    replay.rewrite_results({**results, "mode": "live"})
    verdict = replay.verdict(1.0)
    assert not verdict["ok"]
    assert "only a replay is sanctioned" in verdict["reason"]


# A metric that no case feeds.
def test_a_rate_for_a_metric_no_case_feeds_is_refused(replay: Run) -> None:
    verdict = replay.verdict(1.0, {"tier": "core", "metric": "NS-01"})
    assert not verdict["ok"]
    assert "no case in the run feeds NS-01" in verdict["reason"]


def test_a_rate_for_one_metric_counts_the_cases_that_feed_it(replay: Run) -> None:
    results: dict[str, Any] = json.loads(replay.results_file.read_text())
    results["cases"][0]["metrics"] = ["NS-01"]
    replay.rewrite_results(results)
    verdict = replay.verdict(1.0, {"tier": "core", "metric": "NS-01"})
    assert verdict["ok"], verdict
    assert verdict["details"]["cases"] == 1
