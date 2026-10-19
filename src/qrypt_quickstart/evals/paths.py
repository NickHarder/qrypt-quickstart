"""Where the suite's files live, found from the repository root."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class EvalPaths(BaseModel):
    """The suite's directories and files."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    repository_root: Path
    cases_directory: Path
    cassettes_directory: Path
    thresholds_file: Path
    baseline_file: Path
    prompt_manifest_file: Path


def eval_paths(repository_root: Path) -> EvalPaths:
    """Return where each of the suite's files lives under the repository root."""
    evals_directory = repository_root / "evals"
    return EvalPaths(
        repository_root=repository_root,
        cases_directory=evals_directory / "cases",
        cassettes_directory=evals_directory / "cassettes",
        thresholds_file=evals_directory / "thresholds.yaml",
        baseline_file=evals_directory / "baseline.json",
        prompt_manifest_file=evals_directory / "prompt_manifest.json",
    )
