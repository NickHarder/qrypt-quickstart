"""The deploy path to GitHub Pages (RQ-05, RQ-33): a CI workflow, never a command from a session.

`.github/workflows/deploy.yml` deploys the built site only after CI passes on `main`, into the
`github-pages` environment the owner protects with themselves as approver, with every action pinned
to a commit, and a smoke test that fails the job when the deployed page does not answer.
"""

import re
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
DEPLOY_WORKFLOW: Final = REPOSITORY_ROOT / ".github" / "workflows" / "deploy.yml"
PINNED_ACTION: Final = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")


@pytest.fixture(scope="module")
def workflow() -> dict[Any, Any]:
    loaded: dict[Any, Any] = yaml.safe_load(DEPLOY_WORKFLOW.read_text())
    return loaded


def test_it_runs_only_after_ci_passes_on_main(workflow: dict[Any, Any]) -> None:
    # PyYAML reads the bare key `on` as True.
    triggers: dict[str, Any] = workflow[True]
    assert triggers["workflow_run"]["workflows"] == ["CI"]
    assert triggers["workflow_run"]["types"] == ["completed"]
    assert triggers["workflow_run"]["branches"] == ["main"]
    deploy_job = workflow["jobs"]["deploy"]
    assert "github.event.workflow_run.conclusion == 'success'" in deploy_job["if"]


def test_it_deploys_the_site_ci_built_into_the_protected_pages_environment(
    workflow: dict[Any, Any],
) -> None:
    # The site CI built and tested, from CI's own run, and no code checked out or run here: a
    # workflow_run job that checks out the triggering commit can run it with this job's rights
    # (semgrep's workflow-run-target-code-checkout).
    deploy_job = workflow["jobs"]["deploy"]
    assert deploy_job["environment"]["name"] == "github-pages"
    actions = [step.get("uses", "") for step in deploy_job["steps"]]
    assert not any("actions/checkout" in action for action in actions)
    download = next(
        step for step in deploy_job["steps"] if "download-artifact" in step.get("uses", "")
    )
    assert download["with"]["name"] == "quickstart-site"
    assert download["with"]["run-id"] == "${{ github.event.workflow_run.id }}"
    assert workflow["permissions"] == {
        "actions": "read",
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }


def test_every_action_is_pinned_to_a_commit(workflow: dict[Any, Any]) -> None:
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            action = step.get("uses", "")
            if action and not action.startswith("./"):
                assert PINNED_ACTION.match(action), action


def test_a_smoke_test_fails_the_job_when_the_deployed_page_does_not_answer(
    workflow: dict[Any, Any],
) -> None:
    scripts = " ".join(step.get("run", "") for step in workflow["jobs"]["deploy"]["steps"])
    assert "curl --fail" in scripts
    assert "steps.deployment.outputs.page_url" in scripts
    assert "llms.txt" in scripts
