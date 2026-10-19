"""Attest an eval pass rate: that it is what the sanctioned replay of the suite measured.

The contract is docs/computations/eval-pass-rate.md. The receipt is evals/out/receipt.json, which
the eval runner writes beside results.json. Run from the repository root, as `make attest` does:

    attest(*, computation, parameters, receipt, claimed_value) -> {"ok", "reason", "details"}

The number is refused when:

- the run is not the sanctioned one: the arguments the runner was given are not the computation
  with each parameter filled in as one argument;
- the results changed after the receipt was written;
- the run was not a replay, or it used a prompt text other than the one pinned in
  evals/prompt_manifest.json;
- no case in the run feeds the metric that was asked for;
- the claimed rate is not the measured one.

Only the standard library is imported: no model and no service stands behind the verdict, so any
reader can run it and get the same one. The gate holds every attester to that.
"""

import hashlib
import json
import shlex
from pathlib import Path
from typing import Final

PROMPT_MANIFEST_FILE: Final = Path("evals/prompt_manifest.json")
SANCTIONED_MODE: Final = "replay"
METRIC_PARAMETER: Final = "metric"
RATE_DECIMAL_PLACES: Final = 4
PASSED_STATUS: Final = "pass"


def refusal(reason: str, **details: object) -> dict[str, object]:
    """Return the verdict that a number is not backed, with the reason and the facts behind it."""
    return {"ok": False, "reason": reason, "details": details}


def sanctioned_arguments(computation: str, parameters: dict[str, object]) -> list[str]:
    """Return the arguments of the sanctioned run: the computation with its parameters filled in.

    The computation is split into words first, and each parameter is filled into the word that
    holds its place. A value is then one argument however many words it has, and cannot bring an
    argument of its own into the run (`tier=core --tier all`). The computation's first word is the
    program, which a receipt does not record.
    """
    values_by_name = {name: str(value) for name, value in parameters.items()}
    return [word.format_map(values_by_name) for word in shlex.split(computation)][1:]


def unpinned_prompt_names(results: dict[str, object]) -> list[str]:
    """Return the prompts a run used whose text is not the one the manifest pins."""
    manifest: dict[str, dict[str, str]] = (
        json.loads(PROMPT_MANIFEST_FILE.read_text(encoding="utf-8"))
        if PROMPT_MANIFEST_FILE.is_file()
        else {}
    )
    versions = results.get("versions")
    used_prompts: list[dict[str, str]] = (
        versions.get("prompts", []) if isinstance(versions, dict) else []
    )
    return [
        used_prompt["name"]
        for used_prompt in used_prompts
        if manifest.get(used_prompt["name"], {}).get("sha256") != used_prompt["sha256"]
    ]


def provenance_problem(
    computation: str, parameters: dict[str, object], receipt: dict[str, object]
) -> str:
    """Return why the receipt is not that of the sanctioned run, or an empty string when it is."""
    ran_arguments = receipt.get("arguments")
    if ran_arguments != sanctioned_arguments(computation, parameters):
        return f"this is not the sanctioned run: the runner was given {ran_arguments}"
    results_file = Path(str(receipt.get("results_file")))
    if not results_file.is_file():
        return f"the results the receipt names, {results_file}, are not there"
    results_bytes = results_file.read_bytes()
    if hashlib.sha256(results_bytes).hexdigest() != receipt.get("results_sha256"):
        return f"{results_file} changed after the receipt was written"
    results: dict[str, object] = json.loads(results_bytes)
    if results.get("mode") != SANCTIONED_MODE:
        return (
            f"the run was in mode {results.get('mode')}, and only a {SANCTIONED_MODE} is sanctioned"
        )
    unpinned_names = unpinned_prompt_names(results)
    if unpinned_names:
        return f"the run used a prompt text that is not the pinned one: {', '.join(unpinned_names)}"
    return ""


def feeds(case: dict[str, object], metric_id: object) -> bool:
    """Return whether a case of the run names a metric among the ones it feeds."""
    fed_metric_ids = case.get("metrics")
    return isinstance(fed_metric_ids, list) and metric_id in fed_metric_ids


def attest(
    *,
    computation: str,
    parameters: dict[str, object],
    receipt: dict[str, object],
    claimed_value: object,
) -> dict[str, object]:
    """Return whether a claimed pass rate is the one the sanctioned run of the suite measured."""
    problem = provenance_problem(computation, parameters, receipt)
    if problem:
        return refusal(problem)
    results: dict[str, list[dict[str, object]]] = json.loads(
        Path(str(receipt["results_file"])).read_bytes()
    )
    metric_id = parameters.get(METRIC_PARAMETER)
    counted_cases = [
        case for case in results["cases"] if metric_id is None or feeds(case, metric_id)
    ]
    if not counted_cases:
        return refusal(f"no case in the run feeds {metric_id}")
    passed_count = sum(1 for case in counted_cases if case.get("status") == PASSED_STATUS)
    measured_rate = round(passed_count / len(counted_cases), RATE_DECIMAL_PLACES)
    if isinstance(claimed_value, bool) or not isinstance(claimed_value, int | float):
        return refusal("the claimed rate is not a number", claimed=claimed_value)
    if round(claimed_value, RATE_DECIMAL_PLACES) != measured_rate:
        return refusal(
            "the claimed rate is not the measured one",
            claimed=claimed_value,
            measured=measured_rate,
        )
    return {
        "ok": True,
        "reason": None,
        "details": {"cases": len(counted_cases), "passed": passed_count, "rate": measured_rate},
    }
