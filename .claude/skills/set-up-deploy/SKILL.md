---
name: set-up-deploy
description: Sets up the deploy path through CI, never from a session. A deploy to a dev environment on every merge to main once CI is green, a deploy to production only after the owner approves it in CI, secrets in the CI provider's store, a smoke test after each deploy and a written rollback. Use when the owner asks to set up deploys or the tracer bullet's deploy path is next; the owner starts it by name.
disable-model-invocation: true
metadata:
  version: "1.0.0"
---

# Set up the deploy path

The owner's rules say a change reaches production "through dev and the CI pipeline, never an ad-hoc
script", and that a deploy is asked for first. This skill builds that path once, in CI, so that
every deploy after it follows the same steps. It writes files and records; it deploys nothing.

## Before writing anything

1. **The deploy target.** Find it in `docs/PLAN.md` or the decision `kickoff` recorded. If none is
   recorded, ask the owner once, with a recommendation and its reason, and record the answer with
   the `defend-decision` skill.
2. **The CI provider.** `.github/workflows/` means GitHub Actions; `.gitlab-ci.yml` means GitLab CI.
   With neither, stop: a deploy runs in CI, so the owner chooses a CI provider first.
3. **The target's own deploy tool.** Read the target's current deploy documentation, and use its
   official CLI or CI action. Do not write a deploy script of your own.

## What to write

- **Two environments.** `dev` deploys on every merge to `main`, after the CI jobs pass.
  `production` deploys only after the owner approves it in CI:
  - GitHub Actions: an environment named `production`, which the owner protects with themselves as
    required reviewer.
  - GitLab CI: a manual job on a protected environment named `production`, which only the owner may
    run.
- **A file of its own,** so that `make kit-update` never meets the deploy jobs in the kit's CI file:
  - GitHub Actions: `.github/workflows/deploy.yml`, started by `workflow_run` when the CI workflow
    completes with success on `main`.
  - GitLab CI: `.gitlab/deploy.yml`, with its jobs in a `deploy` stage after the others, and one
    `include:` line for it in `.gitlab-ci.yml`.
- **Pins.** Name every action by its full commit, with its version in a comment, and every image by
  its version, as the kit's CI does.
- **Secrets in the CI provider's store:** environment secrets on GitHub, protected and masked
  variables on GitLab, one set for each environment. Name them in the decision record and the
  handoff; never write a value into the repository.
- **A smoke test after each deploy:** a step that requests the deployed URL (`/health` when the
  HTTP API layer is on) and fails the job on anything but success.
- **A rollback:** the target's own way back to the previous version, written as a command in the
  decision record.

Run `make gate`, and fix what is red, before the change goes to a pull request.

## What to record

- **A decision record,** with the `defend-decision` skill: the target, the two environments, the
  secret names, the smoke test, the rollback command, and how to reverse the whole path.
- **The handoff,** with the `handoff` skill: what is deployed, where, and at which version, which is
  nothing until the first merge after this change.
- **A line for each point where the owner acts,** in the plan and the pull request, so that
  `make blockers` finds them:

  ```text
  **You act:** create the account and a deploy token on <target> (credential or account)
  **You act:** add <secret names> to the CI settings, for dev and production (credential or account)
  **You act:** protect the production environment, with yourself as approver (approval)
  **You act:** approve the first deploy to production in CI (approval)
  ```

## Rules

- Never deploy from the session: no deploy command of the target runs here, against dev or
  production. The first deploy to dev happens in CI, after the merge.
- Never read `.env` to see whether a key is set: ask the owner.
- Do not edit the jobs of the kit's own CI file; the GitLab `include:` line is the one exception.
- Ask first before a new account, a paid plan, or anything installed on the owner's machine.
