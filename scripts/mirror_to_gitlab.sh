#!/bin/sh
# Carry the work from GitHub to GitLab, from the owner's machine: fetch a branch from GitHub and
# push it to a branch on GitLab, as it is. It never force-pushes: if GitLab's branch has commits
# GitHub's does not, it stops and says so.
#
#     scripts/mirror_to_gitlab.sh --gitlab <GitLab clone URL> [--branch <GitHub branch>]
#                                 [--target <GitLab branch>] [--github <GitHub clone URL>]
#                                 [--directory <clone folder>]
#
# Defaults: --github https://github.com/NickHarder/qrypt-quickstart.git, --branch main,
# --target main, --directory ./qrypt-quickstart. The first run clones GitHub into the folder; later
# runs fetch into the same clone, so each run carries whatever is new.
#
# Credentials: git asks for them on the first push over HTTPS. For GitLab, give any user name
# (`oauth2` works) and your personal access token as the password; on a Mac the keychain keeps it.
# The token is never written into this script, the remote's URL or the clone.
set -eu

usage() {
  echo "usage: scripts/mirror_to_gitlab.sh --gitlab <GitLab clone URL> [--branch <GitHub branch>]" >&2
  echo "       [--target <GitLab branch>] [--github <GitHub clone URL>] [--directory <folder>]" >&2
  exit 2
}

github_url="https://github.com/NickHarder/qrypt-quickstart.git"
gitlab_url=""
source_branch="main"
target_branch="main"
clone_directory="qrypt-quickstart"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --github) github_url="${2:-}"; shift 2 ;;
    --gitlab) gitlab_url="${2:-}"; shift 2 ;;
    --branch) source_branch="${2:-}"; shift 2 ;;
    --target) target_branch="${2:-}"; shift 2 ;;
    --directory) clone_directory="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done
[ -n "$gitlab_url" ] && [ -n "$github_url" ] && [ -n "$source_branch" ] && [ -n "$target_branch" ] \
  || usage

if [ -d "$clone_directory/.git" ]; then
  existing_origin=$(git -C "$clone_directory" remote get-url origin)
  if [ "$existing_origin" != "$github_url" ]; then
    echo "mirror: $clone_directory is a clone of $existing_origin, not $github_url; pass --directory" >&2
    exit 1
  fi
else
  echo "mirror: cloning $github_url into $clone_directory"
  git clone --quiet "$github_url" "$clone_directory"
fi

echo "mirror: fetching $source_branch from GitHub"
git -C "$clone_directory" fetch --quiet origin "$source_branch"

if git -C "$clone_directory" remote get-url gitlab >/dev/null 2>&1; then
  git -C "$clone_directory" remote set-url gitlab "$gitlab_url"
else
  git -C "$clone_directory" remote add gitlab "$gitlab_url"
fi

echo "mirror: pushing GitHub's $source_branch to GitLab's $target_branch"
if ! git -C "$clone_directory" push --quiet gitlab \
  "refs/remotes/origin/$source_branch:refs/heads/$target_branch"; then
  echo "mirror: GitLab refused the push. If its $target_branch has commits GitHub's $source_branch" >&2
  echo "        lacks, bring them into GitHub first; this script never force-pushes." >&2
  exit 1
fi
echo "mirror: done; GitLab's $target_branch is $(git -C "$clone_directory" rev-parse --short "origin/$source_branch")"
