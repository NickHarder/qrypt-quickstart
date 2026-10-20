"""The owner's script that carries the work from GitHub to GitLab, run on two local repositories.

`scripts/mirror_to_gitlab.sh` fetches a branch from GitHub and pushes it to a GitLab branch. Here
two bare repositories stand in for the two hosts, so the test needs no network and no token. It
must push the branch as it is, and refuse rather than overwrite when GitLab's branch has commits
GitHub's does not: the owner's rule is never to force-push.
"""

import os
import subprocess
from pathlib import Path
from typing import Final

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
SCRIPT: Final = REPOSITORY_ROOT / "scripts" / "mirror_to_gitlab.sh"
GIT_IDENTITY: Final = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(*arguments: str, cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, **GIT_IDENTITY},
    )
    return completed.stdout.strip()


def make_hosts(tmp_path: Path) -> tuple[Path, Path]:
    """A GitHub stand-in holding one commit on `work`, and an empty GitLab stand-in."""
    github = tmp_path / "github.git"
    gitlab = tmp_path / "gitlab.git"
    git("init", "--bare", "--quiet", str(github), cwd=tmp_path)
    git("init", "--bare", "--quiet", str(gitlab), cwd=tmp_path)
    seed = tmp_path / "seed"
    git("init", "--quiet", "-b", "work", str(seed), cwd=tmp_path)
    (seed / "README.md").write_text("first\n")
    git("add", "README.md", cwd=seed)
    git("commit", "--quiet", "-m", "first", cwd=seed)
    git("push", "--quiet", str(github), "work", cwd=seed)
    return github, gitlab


def run_script(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT), *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, **GIT_IDENTITY},
        timeout=60,
    )


def test_it_clones_github_and_pushes_the_branch_to_gitlabs_main(tmp_path: Path) -> None:
    github, gitlab = make_hosts(tmp_path)
    run = run_script(
        "--github", str(github), "--gitlab", str(gitlab), "--branch", "work", cwd=tmp_path
    )
    assert run.returncode == 0, run.stderr
    github_head = git("rev-parse", "work", cwd=github)
    assert git("rev-parse", "main", cwd=gitlab) == github_head
    assert (tmp_path / "qrypt-quickstart" / ".git").is_dir()


def test_a_second_run_reuses_the_clone_and_carries_new_commits(tmp_path: Path) -> None:
    github, gitlab = make_hosts(tmp_path)
    arguments = ("--github", str(github), "--gitlab", str(gitlab), "--branch", "work")
    assert run_script(*arguments, cwd=tmp_path).returncode == 0
    seed = tmp_path / "seed"
    (seed / "README.md").write_text("second\n")
    git("commit", "--quiet", "-am", "second", cwd=seed)
    git("push", "--quiet", str(github), "work", cwd=seed)
    run = run_script(*arguments, cwd=tmp_path)
    assert run.returncode == 0, run.stderr
    assert git("rev-parse", "main", cwd=gitlab) == git("rev-parse", "work", cwd=github)


def test_it_refuses_to_overwrite_gitlab_commits_that_github_lacks(tmp_path: Path) -> None:
    github, gitlab = make_hosts(tmp_path)
    other = tmp_path / "other"
    git("init", "--quiet", "-b", "main", str(other), cwd=tmp_path)
    (other / "NOTES.md").write_text("made on GitLab\n")
    git("add", "NOTES.md", cwd=other)
    git("commit", "--quiet", "-m", "on gitlab", cwd=other)
    git("push", "--quiet", str(gitlab), "main", cwd=other)
    gitlab_head = git("rev-parse", "main", cwd=gitlab)
    run = run_script(
        "--github", str(github), "--gitlab", str(gitlab), "--branch", "work", cwd=tmp_path
    )
    assert run.returncode != 0
    assert "force" in run.stderr.lower()
    assert git("rev-parse", "main", cwd=gitlab) == gitlab_head


def test_it_says_how_to_run_it_when_an_argument_is_missing(tmp_path: Path) -> None:
    run = run_script("--branch", "work", cwd=tmp_path)
    assert run.returncode != 0
    assert "usage" in run.stderr.lower()
