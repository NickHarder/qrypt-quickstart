"""Thresholds, the committed baseline, and the prompt manifest: what makes a run red.

A threshold is a floor the suite must clear. The baseline is what the suite did on the last green
run: a case that passed there and fails now is a regression, whatever the thresholds say. A change
of wording alone is never a regression; only a verdict is compared. The prompt manifest pins each
prompt's version to its text.
"""

import json
from pathlib import Path

import yaml
from pydantic import ConfigDict, Field, TypeAdapter, ValidationError

from ..prompts import Prompt
from .errors import EvalSetupError
from .models import RunResults, Status, StrictModel


class CoreThreshold(StrictModel):
    """The rule for the core tier."""

    all_must_pass: bool = True


class TraceFloors(StrictModel):
    """Which gaps in the trace fail the gate.

    `scripts/okf_bundle.py` enforces these, in the gate's lint group; the suite only carries them,
    so that every floor of the project is in one file. Turn one on in the change that earns it;
    `evals/thresholds.yaml` says when one may be turned off.

    A floor is `true` or `false` and nothing else. The check reads the same file, and takes only
    `true` for on: a `1` or a `"true"` that this model read as on would be a floor the gate never
    enforced.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    every_case_names_a_use_case_or_finding: bool = False
    every_case_names_a_metric: bool = False
    every_use_case_has_a_case: bool = False
    every_metric_has_a_case_or_a_computation: bool = False
    north_star_has_a_core_case: bool = False
    every_guardrail_has_a_boundary_or_regression_case: bool = False


class Thresholds(StrictModel):
    """`evals/thresholds.yaml`."""

    # The model id, hashed into every recording's ref.
    model: str
    core: CoreThreshold = Field(default_factory=CoreThreshold)
    pass_rate_min: float = 1.0
    trace: TraceFloors = Field(default_factory=TraceFloors)


class BaselineEntry(StrictModel):
    """What one case did on the last green run, and under which prompt versions."""

    status: Status
    prompts: dict[str, str]


class ManifestEntry(StrictModel):
    """One prompt's pinned version and content hash."""

    version: str
    sha256: str


def load_thresholds(thresholds_file: Path) -> Thresholds:
    """Read the thresholds file.

    Raises:
        EvalSetupError: If it is missing or malformed.
    """
    if not thresholds_file.exists():
        message = f"{thresholds_file} is missing"
        raise EvalSetupError(message)
    try:
        return Thresholds.model_validate(
            yaml.safe_load(thresholds_file.read_text(encoding="utf-8"))
        )
    except (ValidationError, yaml.YAMLError) as error:
        message = f"{thresholds_file}: {error}"
        raise EvalSetupError(message) from error


def load_baseline(baseline_file: Path) -> dict[str, BaselineEntry]:
    """Read the committed baseline; empty when there is none yet.

    Raises:
        EvalSetupError: If the file is not a baseline; the message names the file.
    """
    if not baseline_file.exists():
        return {}
    try:
        return TypeAdapter(dict[str, BaselineEntry]).validate_json(
            baseline_file.read_text(encoding="utf-8")
        )
    except ValidationError as error:
        message = f"{baseline_file}: {error}"
        raise EvalSetupError(message) from error


def baseline_from(results: RunResults) -> dict[str, BaselineEntry]:
    """Return the baseline a run would write."""
    return {
        case_result.case_id: BaselineEntry(
            status=case_result.status,
            prompts={prompt.name: prompt.version for prompt in case_result.prompts},
        )
        for case_result in results.cases
    }


def write_baseline(baseline_file: Path, results: RunResults) -> None:
    """Write the baseline from a run. Call this only for a green run."""
    serializable_baseline = {
        case_id: entry.model_dump() for case_id, entry in sorted(baseline_from(results).items())
    }
    baseline_file.write_text(json.dumps(serializable_baseline, indent=2) + "\n", encoding="utf-8")


def threshold_violations(results: RunResults, thresholds: Thresholds) -> list[str]:
    """Return every threshold the run fails."""
    failed_core_ids = [
        case_result.case_id
        for case_result in results.cases
        if case_result.tier == "core" and case_result.status == "fail"
    ]
    core_violations = (
        [f"core.all_must_pass: {', '.join(failed_core_ids)} failed"]
        if thresholds.core.all_must_pass and failed_core_ids
        else []
    )
    pass_rate = results.passed_count / len(results.cases)
    pass_rate_violations = (
        [f"pass_rate_min: {pass_rate:.3f} is below {thresholds.pass_rate_min:.3f}"]
        if pass_rate < thresholds.pass_rate_min
        else []
    )
    return [*core_violations, *pass_rate_violations]


def prompt_changes(baseline_prompts: dict[str, str], current_prompts: dict[str, str]) -> str:
    """Describe which prompt versions differ between the baseline and now, or "" when none do."""
    changed_descriptions = [
        f"{prompt_name} {baseline_prompts.get(prompt_name, 'none')} -> {current_version}"
        for prompt_name, current_version in sorted(current_prompts.items())
        if baseline_prompts.get(prompt_name) != current_version
    ]
    return ", ".join(changed_descriptions)


def baseline_violations(results: RunResults, baseline: dict[str, BaselineEntry]) -> list[str]:
    """Return every regression: a case that passed in the baseline and fails now.

    Each line names the prompt versions that changed alongside it, since that is the first thing to
    check.
    """
    regressions: list[str] = []
    for case_result in results.cases:
        baseline_entry = baseline.get(case_result.case_id)
        if (
            baseline_entry is None
            or baseline_entry.status != "pass"
            or case_result.status != "fail"
        ):
            continue
        current_prompts = {prompt.name: prompt.version for prompt in case_result.prompts}
        changed_prompts = prompt_changes(baseline_entry.prompts, current_prompts)
        prompt_note = f" (prompt changed: {changed_prompts})" if changed_prompts else ""
        regressions.append(f"baseline.regression: {case_result.case_id} pass -> fail{prompt_note}")
    return regressions


def baseline_notes(results: RunResults, baseline: dict[str, BaselineEntry]) -> list[str]:
    """Return what differs from the baseline without being a regression: new cases, prompt bumps."""
    notes: list[str] = []
    for case_result in results.cases:
        baseline_entry = baseline.get(case_result.case_id)
        if baseline_entry is None:
            notes.append(f"{case_result.case_id}: not in the baseline yet")
            continue
        current_prompts = {prompt.name: prompt.version for prompt in case_result.prompts}
        changed_prompts = prompt_changes(baseline_entry.prompts, current_prompts)
        if changed_prompts and case_result.status == baseline_entry.status:
            notes.append(
                f"{case_result.case_id}: {case_result.status}, prompt changed: {changed_prompts}"
            )
    return notes


def manifest_from(prompts: list[Prompt]) -> dict[str, ManifestEntry]:
    """Return the manifest the current prompts would write."""
    return {
        prompt.name: ManifestEntry(version=prompt.version, sha256=prompt.sha256)
        for prompt in prompts
    }


def load_prompt_manifest(manifest_file: Path) -> dict[str, ManifestEntry]:
    """Read the committed prompt manifest; empty when there is none yet.

    Raises:
        EvalSetupError: If the file is not a manifest; the message names the file.
    """
    if not manifest_file.exists():
        return {}
    try:
        return TypeAdapter(dict[str, ManifestEntry]).validate_json(
            manifest_file.read_text(encoding="utf-8")
        )
    except ValidationError as error:
        message = f"{manifest_file}: {error}"
        raise EvalSetupError(message) from error


def unbumped_prompts(manifest: dict[str, ManifestEntry], prompts: list[Prompt]) -> list[str]:
    """Return the prompts whose text changed while their version stayed the same."""
    return [
        prompt.name
        for prompt in prompts
        if prompt.name in manifest
        and manifest[prompt.name].version == prompt.version
        and manifest[prompt.name].sha256 != prompt.sha256
    ]


def write_prompt_manifest(manifest_file: Path, prompts: list[Prompt]) -> None:
    """Write the manifest from the current prompts.

    Raises:
        EvalSetupError: If a prompt's text changed under the same version; bump it first.
    """
    unbumped = unbumped_prompts(load_prompt_manifest(manifest_file), prompts)
    if unbumped:
        message = (
            f"prompt text changed without a version bump: {', '.join(unbumped)}; "
            "raise metadata.version in the prompt file, then write the manifest"
        )
        raise EvalSetupError(message)
    serializable_manifest = {
        prompt_name: entry.model_dump()
        for prompt_name, entry in sorted(manifest_from(prompts).items())
    }
    manifest_file.write_text(json.dumps(serializable_manifest, indent=2) + "\n", encoding="utf-8")
