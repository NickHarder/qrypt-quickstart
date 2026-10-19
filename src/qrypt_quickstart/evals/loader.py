"""Read eval cases from YAML, strictly."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from .errors import EvalSetupError
from .models import EvalCase


def load_case(case_file: Path) -> EvalCase:
    """Read one case file.

    Raises:
        EvalSetupError: If the file is not a valid case; the message names the file and the field.
    """
    try:
        return EvalCase.model_validate(yaml.safe_load(case_file.read_text(encoding="utf-8")))
    except (ValidationError, yaml.YAMLError) as error:
        message = f"{case_file}: not a valid eval case: {error}"
        raise EvalSetupError(message) from error


def load_cases(cases_directory: Path) -> list[EvalCase]:
    """Read every case under the directory, ordered by id.

    Raises:
        EvalSetupError: If there are no cases, or two cases share an id. A suite with nothing in it
            must not look like a suite that passed.
    """
    case_files = sorted([*cases_directory.rglob("*.yaml"), *cases_directory.rglob("*.yml")])
    if not case_files:
        message = f"no eval cases under {cases_directory}; an empty suite proves nothing"
        raise EvalSetupError(message)
    cases = [load_case(case_file) for case_file in case_files]
    case_ids = [case.case_id for case in cases]
    duplicate_ids = sorted({case_id for case_id in case_ids if case_ids.count(case_id) > 1})
    if duplicate_ids:
        message = f"duplicate eval case ids: {', '.join(duplicate_ids)}"
        raise EvalSetupError(message)
    return sorted(cases, key=lambda case: case.case_id)
