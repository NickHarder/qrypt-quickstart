---
type: Decision
title: Deploying the site to GitHub Pages
description: How the quickstart site reaches its public URL, through CI and the owner's approval, and how to undo it.
tags: [deploy, decision]
status: draft
generated: { by: claude-code/2.1.304, at: 2026-10-20T23:10:00Z }
---
# Deploying the site to GitHub Pages

The site is the static files the site builder writes to `build/site` (`index.html`,
`troubleshooting.html`, `llms.txt`, `llms-full.txt`, a stylesheet and the copy script). It holds
nothing from `docs/`, so the repository can stay private while the site is public.

**Claim:** the site deploys to GitHub Pages from `.github/workflows/deploy.yml`, which takes the
site CI built and tested on `main` (CI's `quickstart-site` artifact, from that run) and deploys it
into the `github-pages` environment, which the owner protects with themselves as required reviewer.
The deploy job checks out and runs no code: semgrep's `workflow-run-target-code-checkout` rule
flagged a first version that checked out the triggering commit.
**Evidence:** the owner's choice of 2026-10-20 ("just use pages and push to github"), after it
became unclear whether Gauntlet's internal GitLab serves Pages ([the architecture](ARCHITECTURE.md),
DV-06); `tests/test_deploy_workflow.py` holds the workflow to running only after CI passes on
`main`, from CI's own artifact with no checkout, with every action pinned and a smoke test.
**Alternative considered:** GitLab Pages on Gauntlet's GitLab, as the plan had it.
**Why rejected:** whether that instance offers Pages is unknown until the project exists there, and
only its administrators can turn Pages on; the deadline leaves no time to wait for them.
**How to reverse:** delete `.github/workflows/deploy.yml` and set the repository's Pages source to
none (Settings, Pages); for GitLab Pages, the `set-up-deploy` skill writes `.gitlab/deploy.yml`.

## The path

| Step | Where | What |
|---|---|---|
| Preview | CI, every push | The `site` job builds the site and keeps it as the `quickstart-site` artifact |
| Production | `Deploy` workflow, after CI succeeds on a push to `main` | Downloads that run's `quickstart-site` artifact, uploads it with `actions/upload-pages-artifact` and deploys it with `actions/deploy-pages`, once the owner approves the `github-pages` environment |
| Smoke test | The same job | Requests the page and `llms.txt` at the deployed URL, five tries ten seconds apart, and fails on anything but success or a page without its heading |

GitHub Pages serves one site per repository, so the preview is CI's artifact rather than a second
environment. No secret is needed: the job deploys with the workflow's own token, scoped to Pages.

## Rollback

Run the `Deploy` workflow again on the previous good commit: in Actions, open the CI run of that
commit on `main` and re-run it, and the deploy follows it. To take the site down, set the Pages
source to none in the repository's settings.

## What the owner does

- Turn Pages on with GitHub Actions as its source (Settings, Pages). A private repository needs a
  paid GitHub plan for this; on the free plan the setting asks to make the repository public, and
  then only a repository holding the `public` branch may be made public, never this one.
- Protect the `github-pages` environment with themselves as required reviewer (Settings,
  Environments).
- Merge the work into `main`, and approve the first deploy in CI.
